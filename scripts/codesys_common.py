"""
Shared helpers for the CODESYS Scripting entry points
(codesys_build.py / codesys_deploy.py / codesys_test.py).
"""

import io
import os

from scriptengine import *

# "type|id|version" of the device the project is retargeted to before
# compiling/deploying - see retarget_device(). Empty/unset = keep the
# project's own device.
TARGET_DEVICE_ENV = "CODESYS_TARGET_DEVICE"
# Comma-separated placeholder names that keep the library version they
# resolved to on the original device after retargeting - see
# _pin_placeholders().
KEEP_PLACEHOLDERS_ENV = "CODESYS_KEEP_PLACEHOLDERS"


def write_junit(report_path, testsuite_name, cases):
    failures = sum(1 for c in cases if c["status"] != "pass")
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(
        '<testsuite name="%s" tests="%d" failures="%d">'
        % (testsuite_name, len(cases), failures)
    )
    for c in cases:
        lines.append('  <testcase name="%s" time="%.2f">' % (c["name"], c["time"]))
        if c["status"] != "pass":
            # The failure detail goes in the element's TEXT CONTENT, not a
            # "message" attribute - XML attribute values get whitespace
            # normalized on parse (newlines collapse to spaces), which
            # squashes a multi-line list of compile errors onto one line.
            lines.append("    <failure>%s</failure>" % escape(c["message"]))
        lines.append("  </testcase>")
    lines.append("</testsuite>")
    with io.open(report_path, "w", encoding="utf-8") as f:
        f.write(u"\n".join(lines))


def escape(text):
    return (text or u"").replace(u"&", u"&amp;").replace(u"<", u"&lt;")


def retarget_device(project):
    """
    Swaps the project's Device for the one named in the
    CODESYS_TARGET_DEVICE env var ("type|id|version"), in memory only -
    the .project file in git keeps its real target.

    Needed because the real project targets a hardware PLC (AX8) the CI
    runner doesn't have: CI installs CODESYS Control Win V3 x64 locally,
    so the project must be compiled/downloaded for that device instead.
    In V3.5 SP22 / SoftMotion 4.x there is no separate "Win V3 x64
    SoftMotion" device any more - SoftMotion runs on the plain
    "CODESYS Control Win V3 x64" (4096 / "0000 0004").

    Same as "Update Device" in the IDE: ScriptDeviceObject.update(type,
    id, version, module_id) - signature confirmed by reflecting
    ScriptDriverDeviceObject.plugin.dll of CODESYS 3.5.22.30. Idempotent:
    skipped when the device already matches (e.g. the BUILD stage saved
    the retargeted project and DEPLOY/TEST reopen it).
    """
    spec = os.environ.get(TARGET_DEVICE_ENV, "").strip()
    if not spec:
        print("%s not set - keeping the project's own device." % TARGET_DEVICE_ENV)
        return
    dev_type, dev_id, dev_version = [p.strip() for p in spec.split("|")]
    dev_type = int(dev_type)

    device = project.find("Device", True)[0]
    current = device.get_device_identification()
    current_str = "%s|%s|%s" % (current.type, current.id, current.version)
    if (current.type, current.id, current.version) == (dev_type, dev_id, dev_version):
        print("Device already %s - no retarget needed." % current_str)
        return

    print("Retargeting Device %s -> %s" % (current_str, spec))
    # The project comes from DIADesigner-AX 1.10, so changing its device
    # asks "Do you want to upgrade the storage format to 'CODESYS V3.5
    # SP22 Patch 3'?" (message key LossOfDataWarning2, default "Yes").
    # Headless CI can't answer that via --textPrompts (no stdin ->
    # "The handle is invalid"), so let CODESYS auto-answer simple prompts
    # with their default and just log them. Only affects the in-memory
    # project - the file on disk isn't touched unless saved. Verified
    # locally against CODESYS 3.5.22.30.
    placeholders_before = _snapshot_placeholders(project)
    previous_handling = system.prompt_handling
    system.prompt_handling = PromptHandling.LogMessageKeys | PromptHandling.LogSimplePrompts
    try:
        device.update(dev_type, dev_id, dev_version, None)
    finally:
        system.prompt_handling = previous_handling
    new = device.get_device_identification()
    print("Device is now %s|%s|%s" % (new.type, new.id, new.version))
    _restore_placeholders(project, placeholders_before)
    _pin_placeholders(project, placeholders_before)


def _libmans(project):
    return [o for o in project.get_children(True) if o.is_libman]


def _effective(ref):
    try:
        return ref.effective_resolution
    except Exception:  # noqa: BLE001
        return None


def _snapshot_placeholders(project):
    """
    {libman guid: {placeholder name: (default resolution, effective
    resolution)}} before retarget - i.e. the library versions the project
    was built with on AX8 in DIADesigner-AX.
    """
    snap = {}
    for libman in _libmans(project):
        snap[libman.guid] = dict(
            (ref.placeholder_name, (ref.default_resolution, _effective(ref)))
            for ref in libman.references if ref.is_placeholder
        )
    return snap


def _restore_placeholders(project, snapshot):
    """
    Library references the AX8 device added implicitly (SM3_Basic,
    SM3_CNC, SM3_Drive_ETC, ... - SoftMotion) are dropped by
    device.update(), because the plain Win V3 x64 device doesn't add
    them - the application then fails with "C77: Unknown type 'SMC_...'".
    Re-add every placeholder that disappeared, as a normal library
    reference, with its original default resolution; the redirect step
    below then points it at an installed version. Verified locally.
    """
    for libman in _libmans(project):
        before = snapshot.get(libman.guid, {})
        now = set(ref.placeholder_name for ref in libman.references if ref.is_placeholder)
        for name, (default, _) in sorted(before.items()):
            if name in now:
                continue
            libman.add_placeholder(name, default)
            print("Placeholder %s: re-added after retarget (default %s)" % (name, default))


def _parse_library_title(lib):
    # str(managed library) is "Title, 1.2.3.4 (Company)"
    text = "%s" % lib
    title, rest = text.split(", ", 1)
    version = rest.split(" (", 1)[0]
    return title, tuple(int(p) for p in version.split(".") if p.isdigit()), text


def _pin_placeholders(project, snapshot):
    """
    Library placeholders (#SM3_Basic, #IecVarAccess, ...) are resolved by
    the DEVICE description, so swapping AX8 for Win V3 x64 silently swaps
    library versions too - e.g. IecVarAccess 3.5.15.20 -> 4.6.0.0, which
    then doesn't match the project's SymbolicVarsBase (C4 "'IsReference'
    is no component of 'SymbolicVarNodeAccessor'"), and SoftMotion
    placeholders the new device doesn't define at all stay unresolved
    ("C77: Unknown type 'SMC_...'").

    Fix, same as "Placeholder redirection" in the IDE's Library Manager:
      1. placeholders listed in CODESYS_KEEP_PLACEHOLDERS go back to the
         version they resolved to before retarget, if installed (the
         project archive installs them in CI) - e.g. IecVarAccess;
      2. placeholders that are unresolved now go to the newest installed
         library whose title equals the placeholder name (e.g. SM3_Basic
         -> "SM3_Basic, 4.20.0.0 (CODESYS)");
      3. everything else keeps what the new device resolves it to.
    Pinning ALL placeholders back to their AX8 versions was tried and is
    worse (50 vs 14 errors): system/IO libraries (IoStandard,
    CmpIecTask, IoDrv*) and Delta's DL_* libraries must match the new
    device, so pinning is opt-in per placeholder.
    API (ScriptPlaceholderReference.effective_resolution / set_redirection())
    confirmed by reflecting ScriptDriverLibManObject.plugin.dll of
    CODESYS 3.5.22.30; verified locally.
    """
    keep = set(p.strip() for p in os.environ.get(KEEP_PLACEHOLDERS_ENV, "").split(",") if p.strip())
    installed = set()
    newest = {}
    for repo in librarymanager.repositories:
        for lib in librarymanager.get_all_libraries(repo):
            try:
                title, version, text = _parse_library_title(lib)
            except ValueError:
                continue
            installed.add(text)
            if title not in newest or version > newest[title][0]:
                newest[title] = (version, text)

    for libman in _libmans(project):
        before = snapshot.get(libman.guid, {})
        for ref in libman.references:
            if not ref.is_placeholder:
                continue
            name = ref.placeholder_name
            current = _effective(ref)
            original = before.get(name, (None, None))[1]
            if name in keep and original and original in installed:
                target = original
            elif not current and name in newest:
                target = newest[name][1]
            else:
                if not current:
                    print("Placeholder %s: unresolved, no installed library named '%s'" % (name, name))
                continue
            if target != current:
                ref.set_redirection(target)
                print("Placeholder %s: %s -> %s" % (name, current, target))


def _get_or_create_local_gateway(new_gateway_name="Gateway-1"):
    """
    Returns an existing gateway if this machine has one registered, else
    creates a new TCP/IP gateway pointing at the local CODESYS Gateway
    service (localhost:1217). A fresh CI runner has zero gateways -
    hardcoding a name like "Gateway-1" and indexing online.gateways[name]
    throws KeyError there, so this only ever relies on *some* gateway
    existing, never a specific name.

    Gateway-creation call confirmed against an official CODESYS Forge
    example: https://forum.codesys.com/viewtopic.php?t=7676
    """
    gws = online.gateways
    for existing in gws:
        return existing

    tcp_driver = online.gateway_drivers["TCP/IP"]
    tcp_params = tcp_driver.gateway_parameters

    host_param = tcp_params[0]
    host_param.validate("localhost")
    host_value = gws.convert_gateway_parameter("localhost", host_param.parameter_type)

    port_param = tcp_params[1]
    port_param.validate(1217)
    port_value = gws.convert_gateway_parameter(1217, port_param.parameter_type)

    return gws.add_new_gateway(new_gateway_name, {0: host_value, 1: port_value}, tcp_driver)


def configure_device_gateway(project):
    """
    Points the project's Device at the local runtime.

    A project's device stores no gateway/address by default when opened
    from a fresh .projectarchive (get_gateway() is the zero GUID), which
    makes login fail with "Gateway not configured properly". Setting a
    hardcoded IP (e.g. "127.0.0.1") is accepted by set_gateway_and_address
    but does NOT work either - login then fails with "No connection to
    the device. Please rescan your network", because the local runtime is
    addressed by a short device-address code the gateway assigns
    (discovered via a scan), not by IP. So: scan, then use the first
    result found (the local runtime is the only thing this CI machine's
    gateway can ever find).
    """
    device = project.find("Device", True)[0]
    gw = _get_or_create_local_gateway()
    results = list(gw.perform_network_scan())
    if not results:
        raise RuntimeError("Network scan found no devices - is the CODESYS Control Win V3 service running?")
    device.set_gateway_and_address(gw, results[0].address)

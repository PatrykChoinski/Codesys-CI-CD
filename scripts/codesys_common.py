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
    device.update(dev_type, dev_id, dev_version, None)


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

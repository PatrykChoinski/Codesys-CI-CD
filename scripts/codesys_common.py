"""
Shared helpers for the CODESYS Scripting entry points
(codesys_build.py / codesys_deploy.py / codesys_test.py).
"""

from scriptengine import *


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
            lines.append('    <failure message="%s"></failure>' % escape(c["message"]))
        lines.append("  </testcase>")
    lines.append("</testsuite>")
    with open(report_path, "w") as f:
        f.write("\n".join(lines))


def escape(text):
    return (text or "").replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def configure_device_gateway(project, gateway_name="Gateway-1"):
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

    Confirmed against an official CODESYS Forge example:
    https://forum.codesys.com/viewtopic.php?t=7676
    """
    device = project.find("Device", True)[0]
    gw = online.gateways[gateway_name]
    results = list(gw.perform_network_scan())
    if not results:
        raise RuntimeError("Network scan via '%s' found no devices - is the CODESYS Control Win V3 service running?" % gateway_name)
    device.set_gateway_and_address(gw, results[0].address)

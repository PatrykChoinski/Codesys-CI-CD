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

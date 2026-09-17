"""
CODESYS Scripting entry point for the DEPLOY stage.

Invoked headlessly on the Windows self-hosted runner, after the runtime
container is already built and running:

    "C:\\Program Files\\CODESYS 3.5.22.0\\CODESYS\\Common\\CODESYS.exe" ^
        --profile "CODESYS V3.5 SP22" --noUI --runscript=scripts\\codesys_deploy.py ^
        --scriptargs "<project_path>;<device_address>;<gateway_port>;<report_path>"

Responsibilities:
  1. Open the (already built) project.
  2. Point the active application's communication channel at the
     CODESYS Control Win V3 runtime running on this same runner
     (device_address:gateway_port, installed directly - no container).
  3. Log in, download the boot application, start it.
  4. Log out (the application keeps running on the device independently
     of the engineering session) and write a JUnit-style XML report.

Deliberately does not verify RUN state here - that's the TEST stage's job,
kept separate so "deploy failed" and "smoke test failed" are distinguishable
in CI.
"""

import sys
import time
import traceback

from scriptengine import projects, system  # provided by CODESYS at runtime


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
            lines.append('    <failure message="%s"></failure>' % _escape(c["message"]))
        lines.append("  </testcase>")
    lines.append("</testsuite>")
    with open(report_path, "w") as f:
        f.write("\n".join(lines))


def _escape(text):
    return (text or "").replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def main():
    args = system.get_script_args() if hasattr(system, "get_script_args") else sys.argv[1:]
    project_path, device_address, gateway_port, report_path = args[0].split(";")
    gateway_port = int(gateway_port)

    cases = []
    t0 = time.time()
    try:
        project = projects.open(project_path)
        app = project.active_application

        app.get_device().set_communication_address(device_address, gateway_port)
        app.online_change_option = "IgnoreOnlineChange"
        app.login(update_bootproject=True)
        app.start()
        app.logout()

        cases.append({
            "name": "login_download_start",
            "status": "pass",
            "message": "",
            "time": time.time() - t0,
        })
        system.exit_code = 0
    except Exception:  # noqa: BLE001
        cases.append({
            "name": "login_download_start",
            "status": "fail",
            "message": traceback.format_exc(),
            "time": time.time() - t0,
        })
        system.exit_code = 1

    write_junit(report_path, "codesys-deploy", cases)


main()

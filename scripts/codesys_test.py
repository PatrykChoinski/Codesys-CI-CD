"""
CODESYS Scripting entry point for the TEST stage (smoke test).

Invoked headlessly on the Windows runner, after the DEPLOY stage has
downloaded and started the application on the runtime running on the
same machine:

    "C:\\Program Files\\CODESYS 3.5.22.0\\CODESYS\\Common\\CODESYS.exe" ^
        --profile "CODESYS V3.5 SP22" --noUI --runscript=scripts\\codesys_test.py ^
        --scriptargs "<project_path>;<device_address>;<gateway_port>;<report_path>"

Responsibilities:
  1. Open the project, log in to the already-running application in
     monitor-only mode (no re-download).
  2. Verify the device reports RUN state.
  3. Log out and write a JUnit-style XML report consumed by the CI job.

Extend this script with additional test cases (reading/forcing symbols,
running a CODESYS Unit Testing Framework suite, etc.) as needed - each
should append its own entry to `cases` so it shows up as its own testcase
in the JUnit report.
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

    project = projects.open(project_path)
    app = project.active_application
    app.get_device().set_communication_address(device_address, gateway_port)

    t0 = time.time()
    try:
        app.login(update_bootproject=False)

        state = app.get_device_state() if hasattr(app, "get_device_state") else None
        is_running = state is None or str(state).lower() in ("run", "running")

        cases.append({
            "name": "plc_in_run_state",
            "status": "pass" if is_running else "fail",
            "message": "" if is_running else "PLC did not report RUN state (state=%s)" % state,
            "time": time.time() - t0,
        })

        app.logout()
        system.exit_code = 0 if is_running else 1
    except Exception:  # noqa: BLE001
        cases.append({
            "name": "plc_in_run_state",
            "status": "fail",
            "message": traceback.format_exc(),
            "time": time.time() - t0,
        })
        system.exit_code = 1

    write_junit(report_path, "codesys-test", cases)


main()

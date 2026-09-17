"""
CODESYS Scripting entry point for the TEST stage (smoke test).

Invoked headlessly, after the DEPLOY stage has downloaded and started the
application:
    CODESYS.exe --profile="CODESYS V3.5 SP22" --runscript="scripts\\codesys_test.py" ^
        --scriptargs:'<project_path> <report_path>' --noUI

Responsibilities:
  1. Open the project, log in to the already-running application without
     forcing a re-download.
  2. Verify the application reports RUN state.
  3. Log out and write a JUnit-style XML report consumed by the CI job.

Extend this script with additional test cases (reading/forcing symbols
via onlineapp.read_value(...), running a CODESYS Unit Testing Framework
suite, etc.) as needed - each should append its own entry to `cases` so
it shows up as its own testcase in the JUnit report.
"""

import sys
import time
import traceback

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
            lines.append('    <failure message="%s"></failure>' % _escape(c["message"]))
        lines.append("  </testcase>")
    lines.append("</testsuite>")
    with open(report_path, "w") as f:
        f.write("\n".join(lines))


def _escape(text):
    return (text or "").replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def main():
    project_path, report_path = sys.argv[1], sys.argv[2]

    cases = []
    t0 = time.time()
    try:
        project = projects.open(project_path)
        app = project.active_application
        onlineapp = online.create_online_application(app)
        onlineapp.login(OnlineChangeOption.Try, False)

        is_running = onlineapp.application_state == ApplicationState.run

        cases.append({
            "name": "plc_in_run_state",
            "status": "pass" if is_running else "fail",
            "message": "" if is_running else "Application state was %s, expected run" % onlineapp.application_state,
            "time": time.time() - t0,
        })

        onlineapp.logout()
        exit_code = 0 if is_running else 1
    except Exception:  # noqa: BLE001
        cases.append({
            "name": "plc_in_run_state",
            "status": "fail",
            "message": traceback.format_exc(),
            "time": time.time() - t0,
        })
        exit_code = 1

    write_junit(report_path, "codesys-test", cases)
    system.exit(exit_code)


main()

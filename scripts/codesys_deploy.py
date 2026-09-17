"""
CODESYS Scripting entry point for the DEPLOY stage.

Invoked headlessly, after the runtime service is already installed and
running on this same machine:
    CODESYS.exe --profile="CODESYS V3.5 SP22" --runscript="scripts\\codesys_deploy.py" ^
        --scriptargs:'<project_path> <report_path>' --noUI

Responsibilities:
  1. Open the (already built) project.
  2. Log in to the runtime, forcing a full download, and start the
     application.
  3. Log out (the application keeps running on the device independently
     of the engineering session) and write a JUnit-style XML report.

No device address is set here: the project's device is assumed to
already be configured to talk to the local runtime (127.0.0.1), the same
setup used when the project was created/tested locally against a local
CODESYS Control Win V3/SL instance - CI runs the runtime on the same
machine as the engineering session, so this should just work.

Deliberately does not verify RUN state here - that's the TEST stage's
job, kept separate so "deploy failed" and "smoke test failed" are
distinguishable in CI.

API confirmed against an official CODESYS Forge example
(create_online_application/OnlineChangeOption/ApplicationState):
https://forge.codesys.com/forge/redirect/forum?lan=en&thread=1890
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
        onlineapp.login(OnlineChangeOption.Try, True)
        if not onlineapp.application_state == ApplicationState.run:
            onlineapp.start()
        onlineapp.logout()

        cases.append({
            "name": "login_download_start",
            "status": "pass",
            "message": "",
            "time": time.time() - t0,
        })
        exit_code = 0
    except Exception:  # noqa: BLE001
        cases.append({
            "name": "login_download_start",
            "status": "fail",
            "message": traceback.format_exc(),
            "time": time.time() - t0,
        })
        exit_code = 1

    write_junit(report_path, "codesys-deploy", cases)
    system.exit(exit_code)


main()

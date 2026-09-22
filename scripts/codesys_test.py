"""
CODESYS Scripting entry point for the TEST stage (smoke test).

Invoked headlessly, after the DEPLOY stage has downloaded and started the
application, and after the BUILD stage has already "primed" the
machine's device repository (see codesys_build.py's docstring):
    CODESYS.exe --profile="CODESYS V3.5 SP22 Patch 3" --runscript="scripts\\codesys_test.py" ^
        --scriptargs:'<project_path> <report_path>' --noUI

Responsibilities:
  1. Open the live CICD.project, pointing the Device at the local
     runtime same as codesys_deploy.py (a freshly opened project has no
     gateway/address set at all).
  2. Log in with always_update=True (same as DEPLOY - using False here
     reliably left the application in STOP state; keeping this even
     though both stages now open the identical live .project rather than
     two separately-compiled archive copies, since it's a harmless,
     already-proven-safe default).
  3. Start the application if it isn't already running, then verify it
     reports RUN state.
  4. Log out and write a JUnit-style XML report consumed by the CI job.

Extend this script with additional test cases (reading/forcing symbols
via onlineapp.read_value(...), running a CODESYS Unit Testing Framework
suite, etc.) as needed - each should append its own entry to `cases` so
it shows up as its own testcase in the JUnit report.
"""

import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scriptengine import *
from codesys_common import write_junit, configure_device_gateway


def main():
    project_path, report_path = sys.argv[1], sys.argv[2]

    cases = []
    t0 = time.time()
    try:
        project = projects.open(project_path)
        configure_device_gateway(project)

        app = project.active_application
        onlineapp = online.create_online_application(app)
        onlineapp.login(OnlineChangeOption.Try, True)

        if not onlineapp.application_state == ApplicationState.run:
            onlineapp.start()

        deadline = time.time() + 10
        state = onlineapp.application_state
        while state != ApplicationState.run and time.time() < deadline:
            time.sleep(1)
            state = onlineapp.application_state

        is_running = state == ApplicationState.run

        cases.append({
            "name": "plc_in_run_state",
            "status": "pass" if is_running else "fail",
            "message": "" if is_running else "Application state was %s, expected run" % state,
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

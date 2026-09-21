"""
CODESYS Scripting entry point for the TEST stage (smoke test).

Invoked headlessly, after the DEPLOY stage has downloaded and started the
application:
    CODESYS.exe --profile="CODESYS V3.5 SP22 Patch 3" --runscript="scripts\\codesys_test.py" ^
        --scriptargs:'<archive_path> <extract_dir> <report_path>' --noUI

Responsibilities:
  1. Open CICD.projectarchive (see codesys_build.py's docstring for why -
     the plain .project fails on a CI runner with no device descriptions
     registered), pointing the Device at the local runtime same as
     codesys_deploy.py (this stage opens its own separate extract_dir, so
     the gateway/address isn't already set from the DEPLOY stage's run).
  2. Log in to the already-running application without forcing a
     re-download.
  3. Verify the application reports RUN state.
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
    archive_path, extract_dir, report_path = sys.argv[1], sys.argv[2], sys.argv[3]

    cases = []
    t0 = time.time()
    try:
        project = projects.open_archive(archive_path, extract_dir, True, "")
        configure_device_gateway(project)

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

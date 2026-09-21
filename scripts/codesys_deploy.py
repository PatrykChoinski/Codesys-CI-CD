"""
CODESYS Scripting entry point for the DEPLOY stage.

Invoked headlessly, after the runtime service is already installed and
running on this same machine:
    CODESYS.exe --profile="CODESYS V3.5 SP22 Patch 3" --runscript="scripts\\codesys_deploy.py" ^
        --scriptargs:'<archive_path> <extract_dir> <report_path>' --noUI

Responsibilities:
  1. Open CICD.projectarchive (see codesys_build.py's docstring for why -
     the plain .project fails on a CI runner with no device descriptions
     registered).
  2. Point the Device at the local runtime (see
     codesys_common.configure_device_gateway - a fresh archive-opened
     project has no gateway/address set at all).
  3. Log in to the runtime, forcing a full download, and start the
     application.
  4. Log out (the application keeps running on the device independently
     of the engineering session) and write a JUnit-style XML report.

Deliberately does not verify RUN state here - that's the TEST stage's
job, kept separate so "deploy failed" and "smoke test failed" are
distinguishable in CI.

API confirmed against official CODESYS Forge examples
(create_online_application/OnlineChangeOption/ApplicationState):
https://forge.codesys.com/forge/redirect/forum?lan=en&thread=1890
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

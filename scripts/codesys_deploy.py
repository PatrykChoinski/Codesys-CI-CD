"""
CODESYS Scripting entry point for the DEPLOY stage.

Invoked headlessly, after the runtime service is already installed and
running on this same machine, and after the BUILD stage has already
"primed" the machine's device repository (see codesys_build.py's
docstring):
    CODESYS.exe --profile="CODESYS V3.5 SP22 Patch 3" --runscript="scripts\\codesys_deploy.py" ^
        --scriptargs:'<project_path> <report_path> [encryption_password]' --noUI

Responsibilities:
  1. Open the live PilaJednosuportowa.project (not the archive - the device it needs
     is already registered machine-wide by the BUILD stage's priming).
  2. Point the Device at the local runtime (see
     codesys_common.configure_device_gateway - a freshly opened project
     has no gateway/address set at all).
  3. Log in to the runtime, forcing a full download, and start the
     application.
  4. Log out (the application keeps running on the device independently
     of the engineering session) and write a JUnit-style XML report.

Polls briefly for RUN state right after start() to catch a start that
didn't stick (see below) - the TEST stage still does the real,
independent verification (a fresh login/state check in its own process),
kept separate so "deploy failed" and "smoke test failed" stay
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
from codesys_common import write_junit, configure_device_gateway, retarget_device


def main():
    project_path, report_path = sys.argv[1], sys.argv[2]
    encryption_password = sys.argv[3] if len(sys.argv) > 3 else ""

    cases = []
    t0 = time.time()
    try:
        project = projects.open(project_path, encryption_password=encryption_password)
        retarget_device(project)
        configure_device_gateway(project)

        app = project.active_application
        onlineapp = online.create_online_application(app)
        onlineapp.login(OnlineChangeOption.Try, True)
        if not onlineapp.application_state == ApplicationState.run:
            onlineapp.start()

        # start() isn't guaranteed to have taken effect the instant it
        # returns - poll briefly rather than trusting it blindly, so a
        # start that silently doesn't stick is caught here as a deploy
        # failure instead of surfacing confusingly in the TEST stage.
        deadline = time.time() + 10
        state = onlineapp.application_state
        while state != ApplicationState.run and time.time() < deadline:
            time.sleep(1)
            state = onlineapp.application_state

        onlineapp.logout()

        if state != ApplicationState.run:
            raise RuntimeError("Application did not reach RUN state after start() (state=%s)" % state)

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

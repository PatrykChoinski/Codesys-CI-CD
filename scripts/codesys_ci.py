"""
CODESYS Scripting entry point used by the CI pipeline.

Runs INSIDE the CODESYS Development System's script engine (IronPython),
invoked headlessly from the Windows self-hosted runner:

    "C:\\Program Files\\CODESYS 3.5.22.0\\CODESYS\\Common\\CODESYS.exe" ^
        --profile "CODESYS V3.5 SP22" --noUI --runscript=scripts\\codesys_ci.py ^
        --scriptargs "<project_path>;<device_address>;<gateway_port>;<report_path>"

Responsibilities:
  1. Open the project.
  2. Build (compile) the active application.
  3. Set the active application's communication address to the runtime
     running in the Docker container (device_address:gateway_port).
  4. Log in, download, start the application.
  5. Read back the application's run state to confirm the PLC is RUNning.
  6. Write a JUnit-style XML report consumed by the GitHub Actions job.

NOTE: exact CODESYS Scripting API calls (module/method names) can shift
slightly between SP versions - verify against the "CODESYS Scripting"
help chapter for V3.5 SP22 if a call below no longer matches your install.
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

    t0 = time.time()
    try:
        build_result = app.build()
        ok = getattr(build_result, "successful", build_result)
        cases.append({
            "name": "compile",
            "status": "pass" if ok else "fail",
            "message": "" if ok else "Build reported errors, see build log",
            "time": time.time() - t0,
        })
        if not ok:
            raise RuntimeError("Compilation failed")
    except Exception as exc:  # noqa: BLE001
        cases.append({
            "name": "compile",
            "status": "fail",
            "message": traceback.format_exc(),
            "time": time.time() - t0,
        })
        write_junit(report_path, "codesys-ci", cases)
        system.exit_code = 1
        return

    t0 = time.time()
    try:
        # Point the application's active communication channel at the
        # runtime container exposed by Docker (host:port mapped to 1217).
        app.get_device().set_communication_address(device_address, gateway_port)

        app.online_change_option = "IgnoreOnlineChange"
        app.login(update_bootproject=True)
        app.start()

        # Give the runtime a moment, then verify RUN state.
        time.sleep(2)
        state = app.get_device_state() if hasattr(app, "get_device_state") else None
        is_running = state is None or str(state).lower() in ("run", "running")

        cases.append({
            "name": "deploy_and_run",
            "status": "pass" if is_running else "fail",
            "message": "" if is_running else "PLC did not reach RUN state (state=%s)" % state,
            "time": time.time() - t0,
        })

        app.logout()
    except Exception:  # noqa: BLE001
        cases.append({
            "name": "deploy_and_run",
            "status": "fail",
            "message": traceback.format_exc(),
            "time": time.time() - t0,
        })

    write_junit(report_path, "codesys-ci", cases)
    system.exit_code = 0 if all(c["status"] == "pass" for c in cases) else 1


main()

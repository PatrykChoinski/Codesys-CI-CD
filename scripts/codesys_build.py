"""
CODESYS Scripting entry point for the BUILD stage.

Invoked headlessly on the Windows self-hosted runner:

    "C:\\Program Files\\CODESYS 3.5.22.0\\CODESYS\\Common\\CODESYS.exe" ^
        --profile "CODESYS V3.5 SP22" --noUI --runscript=scripts\\codesys_build.py ^
        --scriptargs "<project_path>;<report_path>"

Responsibilities:
  1. Open the project.
  2. Build (compile) the active application.
  3. Write a JUnit-style XML report with the compile result.

Only compiles - does not touch any runtime/device. Exit code is non-zero
on compile failure so the CI "build" job fails fast, before any container
is started.

NOTE: exact CODESYS Scripting API calls can shift slightly between SP
versions - verify against the "CODESYS Scripting" help chapter for
V3.5 SP22 if a call below no longer matches your install.
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
    project_path, report_path = args[0].split(";")

    cases = []
    t0 = time.time()
    try:
        project = projects.open(project_path)
        app = project.active_application

        build_result = app.build()
        ok = getattr(build_result, "successful", build_result)

        cases.append({
            "name": "compile",
            "status": "pass" if ok else "fail",
            "message": "" if ok else "Build reported errors, see build log",
            "time": time.time() - t0,
        })

        # Keep the compiled state (precompilecache) on disk so the deploy
        # stage can reuse it without a full recompile.
        project.save()

        system.exit_code = 0 if ok else 1
    except Exception:  # noqa: BLE001
        cases.append({
            "name": "compile",
            "status": "fail",
            "message": traceback.format_exc(),
            "time": time.time() - t0,
        })
        system.exit_code = 1

    write_junit(report_path, "codesys-build", cases)


main()

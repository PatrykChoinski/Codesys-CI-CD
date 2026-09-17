"""
CODESYS Scripting entry point for the BUILD stage.

Invoked headlessly:
    CODESYS.exe --profile="CODESYS V3.5 SP22" --runscript="scripts\\codesys_build.py" ^
        --scriptargs:'<project_path> <report_path>' --noUI

Responsibilities:
  1. Open the project.
  2. Generate code (compile) for the active application.
  3. Write a JUnit-style XML report with the compile result.

Only compiles - does not touch any runtime/device. Exit code is non-zero
on compile failure so the CI "build" job fails fast, before any runtime
install is attempted.

API confirmed against official CODESYS Forge examples (generate_code(),
CompileCategory/Severity message checking):
https://forge.codesys.com/forge/talk/Engineering/thread/26b27aa0cf/
https://forge.codesys.com/tol/scripting/snippets/11/
"""

from scriptengine import *
import sys
import time
import traceback

CompileCategory = Guid("{97F48D64-A2A3-4856-B640-75C046E37EA9}")
_SEVERITY_NAMES = {
    Severity.FatalError: "Fatal error",
    Severity.Error: "Error",
    Severity.Warning: "Warning",
    Severity.Information: "Information",
    Severity.Text: "Text",
}


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
        system.clear_messages(CompileCategory)
        project.active_application.generate_code()

        msgs = list(system.get_message_objects(CompileCategory, Severity.FatalError | Severity.Error))
        ok = len(msgs) == 0
        message = "\n".join(
            "%s %s%s: %s" % (_SEVERITY_NAMES.get(m.severity, m.severity), m.prefix, m.number, m.text)
            for m in msgs
        )

        cases.append({
            "name": "compile",
            "status": "pass" if ok else "fail",
            "message": message,
            "time": time.time() - t0,
        })

        if ok:
            project.save()

        exit_code = 0 if ok else 1
    except Exception:  # noqa: BLE001
        cases.append({
            "name": "compile",
            "status": "fail",
            "message": traceback.format_exc(),
            "time": time.time() - t0,
        })
        exit_code = 1

    write_junit(report_path, "codesys-build", cases)
    system.exit(exit_code)


main()

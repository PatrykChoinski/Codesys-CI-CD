"""
CODESYS Scripting entry point for the BUILD stage.

Invoked headlessly:
    CODESYS.exe --profile="CODESYS V3.5 SP22 Patch 3" --runscript="scripts\\codesys_build.py" ^
        --scriptargs:'<archive_path> <prime_extract_dir> <project_path> <report_path> [archive_password]' --noUI

archive_password unlocks the encrypted PilaJednosuportowa.projectarchive
(without it, projects.open_archive() blocks on an "Encryption Password"
dialog that --noUI/--textPrompts can't answer, and eventually fails with
"StandardError: Operation cancelled by user."). Passed via the
CODESYS_PROJECT_PASSWORD env var / PROJECT_PASSWORD GitHub secret - never
hardcoded/committed. Optional: omitted entirely for an unencrypted archive.

Responsibilities:
  1. "Prime" the machine-wide CODESYS device repository by opening
     PilaJednosuportowa.projectarchive once and immediately closing it
     again - see below for why.
  2. Open the real, live PilaJednosuportowa.project (not the archive)
     and generate code (compile) for the active application.
  3. Write a JUnit-style XML report with the compile result.

Why the archive is only used to "prime" and code always comes from the
live .project: a bare CI install of CODESYS has no device descriptions
registered, so opening PilaJednosuportowa.project directly fails to
compile with "C188: Device not installed to the system. No code
generation possible." (plus a cascade of unresolved placeholder
libraries). projects.open_archive() installs the bundled device
description as a side effect of opening - but that installation lands
in the machine-wide, file-based device repository
(C:\\ProgramData\\CODESYS\\Devices), not something scoped to the
archive-opened project. So opening the archive once, then discarding
it, is enough to make the device available to every later
projects.open(PilaJednosuportowa.project) call for the rest of the job -
meaning the archive only ever needs regenerating
(scripts/Update-ProjectArchive.ps1) when the device/target or bundled
libraries change, never for ordinary code edits. See README.md for more
background.
https://forge.codesys.com/forge/talk/CODESYS-V2/thread/0952ef6ae0/

Only compiles - does not touch any runtime/device. Exit code is non-zero
on compile failure so the CI "build" job fails fast, before any runtime
install is attempted.

API confirmed against official CODESYS Forge examples (generate_code(),
CompileCategory/Severity message checking):
https://forge.codesys.com/forge/talk/Engineering/thread/26b27aa0cf/
https://forge.codesys.com/tol/scripting/snippets/11/
"""

import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scriptengine import *
from codesys_common import write_junit

CompileCategory = Guid("{97F48D64-A2A3-4856-B640-75C046E37EA9}")
_SEVERITY_NAMES = {
    Severity.FatalError: "Fatal error",
    Severity.Error: "Error",
    Severity.Warning: "Warning",
    Severity.Information: "Information",
    Severity.Text: "Text",
}


def main():
    archive_path, prime_extract_dir, project_path, report_path = (
        sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    )
    archive_password = sys.argv[5] if len(sys.argv) > 5 else ""

    cases = []
    t0 = time.time()
    try:
        primer = projects.open_archive(archive_path, prime_extract_dir, overwrite=True,
                                        encryption_password=archive_password)
        primer.close()

        project = projects.open(project_path, encryption_password=archive_password)
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
            # Best-effort: lets the DEPLOY stage reuse this compiled state
            # instead of recompiling from scratch. Purely a speed
            # optimization, so a failure here (e.g. the project is marked
            # "Released"/read-only in Project Information and can't be
            # saved back to disk) must not turn a successful compile into
            # a failed build.
            try:
                project.save()
            except Exception:  # noqa: BLE001
                print("Warning: could not save compiled state (non-fatal): %s" % traceback.format_exc())

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

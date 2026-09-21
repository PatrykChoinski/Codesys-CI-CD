"""
CODESYS Scripting entry point that (re)generates the checked-in
CICD.projectarchive from CICD.project.

Invoked via scripts/Update-ProjectArchive.ps1 - run this LOCALLY (on a
machine with the project's target device already installed, e.g. after
installing CODESYS Control Win V3) whenever CICD.project changes, and
commit the resulting CICD.projectarchive alongside it.

Why this exists: a bare CODESYS Development System install on a CI
runner has no device descriptions registered, so opening/building
CICD.project directly fails with "C188: Device not installed to the
system." A .projectarchive bundles the device description (and required
libraries) with the project, and opening it via projects.open_archive()
installs whatever is missing automatically - see
scripts/codesys_build.py / codesys_deploy.py / codesys_test.py, which all
open the archive instead of the plain .project for this reason.
"""

import sys
import traceback

from scriptengine import *


def main():
    project_path, archive_path = sys.argv[1], sys.argv[2]

    try:
        project = projects.open(project_path)
        project.save_archive(path=archive_path, comment="CI build archive")
        print("Saved %s" % archive_path)
        system.exit(0)
    except Exception:  # noqa: BLE001
        print(traceback.format_exc())
        system.exit(1)


main()

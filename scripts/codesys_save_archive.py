"""
CODESYS Scripting entry point that (re)generates the
PilaJednosuportowa.projectarchive asset from PilaJednosuportowa.project.

Invoked via scripts/Update-ProjectArchive.ps1 - run this LOCALLY (on a
machine with the project's target device already installed, e.g. after
installing CODESYS Control Win V3) whenever the project's target/device
or bundled libraries change, then re-upload the resulting
.projectarchive to the GitHub Release asset CI downloads it from (too
large to commit to git - see README.md).

Why this exists: a bare CODESYS Development System install on a CI
runner has no device descriptions registered, so opening/building the
plain .project directly fails with "C188: Device not installed to the
system." A .projectarchive bundles the device description (and required
libraries) with the project, and opening it via projects.open_archive()
installs whatever is missing into the machine-wide device repository as
a side effect - see scripts/codesys_build.py, which opens the archive
once just to "prime" that repository, then closes it and compiles the
live .project instead.
"""

import sys
import traceback

from scriptengine import *


def main():
    project_path, archive_path = sys.argv[1], sys.argv[2]
    encryption_password = sys.argv[3] if len(sys.argv) > 3 else ""

    try:
        project = projects.open(project_path, encryption_password=encryption_password)
        project.save_archive(path=archive_path, comment="CI build archive")
        print("Saved %s" % archive_path)
        system.exit(0)
    except Exception:  # noqa: BLE001
        print(traceback.format_exc())
        system.exit(1)


main()

#!/bin/bash
# Print one release's section of CHANGELOG.md (without its heading):
#   k4nza-changelog-section.sh CHANGELOG.md v3.0.15-20
# A section starts at "## v3.0.15-20" (anything may follow on that line) and
# ends at the next "## " heading. Used for the GitHub release notes, which the
# feeder's Updates page shows as "What's new".
set -euo pipefail
file="${1:?usage: $0 CHANGELOG.md vX.Y.Z-N}"
version="${2:?usage: $0 CHANGELOG.md vX.Y.Z-N}"
awk -v v="$version" '
    /^## / {
        if (found) exit
        split(substr($0, 4), w, /[ \t]/)
        if (w[1] == v) { found = 1; next }
    }
    found { print }
    END { if (!found) exit 1 }
' "$file" | sed -e '/./,$!d'

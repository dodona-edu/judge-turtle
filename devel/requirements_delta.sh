#!/bin/bash
set -euo pipefail

ROOT="$(dirname "$(dirname "$0")")"

cd "$ROOT"

# Without an argument this only reports what it found, and writes delta=true or
# delta=false to $GITHUB_OUTPUT for a workflow to gate on. With --fail it turns the
# comparison into a verdict, and exits 1 unless requirements.txt and the image agree.
guard=false
if [ "${1:-}" = "--fail" ]; then
    guard=true
fi

# Only the verdict belongs in the run summary.
report() {
    if [ "$guard" = true ] && [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
        tee -a "$GITHUB_STEP_SUMMARY"
    else
        cat
    fi
}

set_delta() {
    if [ -n "${GITHUB_OUTPUT:-}" ]; then
        echo "delta=$1" >> "$GITHUB_OUTPUT"
    fi
}

if [ ! -f /requirements/judge-turtle.txt ]; then
    echo "The running image ships no /requirements/judge-turtle.txt, so it predates the baked dependency list and there is nothing to compare requirements.txt against. Expected until the image carrying that file is published (dodona-edu/docker-images, the dodona-python per-consumer requirements spike, plus a publish run)." | report
    # Neither a delta nor the absence of one, since there was nothing to compare against.
    set_delta ""

    if [ "$guard" = true ]; then
        exit 1
    fi
    exit 0
fi

# Requirement lines only: comments legitimately differ on either side.
requirement_lines() { grep -Ev '^[[:space:]]*(#|$)' "$1" | sort; }

requirement_lines requirements.txt > /tmp/repo-requirements.txt
requirement_lines /requirements/judge-turtle.txt > /tmp/image-requirements.txt

if diff -u --label 'image /requirements/judge-turtle.txt' --label 'requirements.txt' /tmp/image-requirements.txt /tmp/repo-requirements.txt > /tmp/requirements.diff; then
    echo "requirements.txt matches the dependency list the image ships." | report
    set_delta false
    exit 0
fi

{
    echo "requirements.txt does not match the dependency list the image ships. Either this branch proposes a dependency change the image has not shipped yet, in which case the PR becomes mergeable once docker-images has published it; or main's requirements.txt went stale after a publish, in which case merging the Dependabot sync PR closes the gap."
    echo
    echo '```diff'
    cat /tmp/requirements.diff
    echo '```'
} | report
set_delta true

if [ "$guard" = true ]; then
    exit 1
fi

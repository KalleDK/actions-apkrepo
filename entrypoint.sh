#!/usr/bin/env sh

set -e

echo "::group::Setup"

export PACKAGER="${INPUT_ABUILD_PACKAGER}"
export SRCDEST="${GITHUB_WORKSPACE}/cache/distfiles"
export REPODEST="${GITHUB_WORKSPACE}/packages"
export SUBREPO_BUILD="${REPODEST}/workspace"
export REPONAME=${INPUT_ABUILD_REPO_NAME}
export SUBREPO="${REPODEST}/${REPONAME}"
export BASE_URL=${INPUT_ABUILD_REPO_URL}

export PREFIX=${INPUT_ABUILD_PREFIX:-.}
export GIT_COMMIT=${INPUT_ABUILD_PKG_COMMIT}
export PKG_VER=${INPUT_ABUILD_PKG_VER}
export ABUILD_DIR=~/.abuild


ls -la
ls -la dist

apk index -o ./dist/APKINDEX.tar.gz ./dist/*.apk
abuild-sign -k ./apk.rsa ./dist/APKINDEX.tar.gz

ls -la
ls -la dist

echo "::endgroup::"
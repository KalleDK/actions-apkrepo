#!/usr/bin/env sh

set -e

echo "::group::Setup"

export PACKAGER="${INPUT_ABUILD_PACKAGER}"

apk index -o ./dist/APKINDEX.tar.gz ./dist/*.apk
abuild-sign -k $(pwd)/${INPUT_ABUILD_KEY_NAME}.rsa ./dist/APKINDEX.tar.gz
mkdir ./apk-repo
cp ${INPUT_ABUILD_KEY_NAME}.rsa.pub ./apk-repo/
cp ./dist/*.apk ./apk-repo/
cp ./dist/APKINDEX.tar.gz ./apk-repo/
ls -la ./apk-repo
echo "repo_path=./apk-repo" >> $GITHUB_OUTPUT
echo "::endgroup::"
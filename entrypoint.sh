#!/usr/bin/env sh

set -e

echo "::group::Setup"

export PACKAGER="${INPUT_ABUILD_PACKAGER}"
export REPONAME=${INPUT_ABUILD_REPO_NAME}
export BASE_URL=${INPUT_ABUILD_REPO_URL}

apk index -o ./dist/APKINDEX.tar.gz ./dist/*.apk
abuild-sign -k $(pwd)/${INPUT_ABUILD_KEY_NAME}.rsa ./dist/APKINDEX.tar.gz
mkdir ./apk
cp ${INPUT_ABUILD_KEY_NAME}.rsa.pub ./apk/
cp ./dist/*.apk ./apk/
cp ./dist/APKINDEX.tar.gz ./apk/
ls -la ./apk
cat << EOF > ./apk/index.md
# ACME DNS Proxy

\`\`\`bash
# Install key
wget -O "/etc/apk/keys/${INPUT_ABUILD_KEY_NAME}.rsa.pub" "${BASE_URL}/${REPONAME}/apk/${KEY_NAME}.rsa.pub"

# Install repo
echo "${BASE_URL}/${REPONAME}/apk" >> /etc/apk/repositories
\`\`\` 
EOF

cat ./apk/index.md
echo "repo_path=./apk" >> $GITHUB_OUTPUT
echo "::endgroup::"
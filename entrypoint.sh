#!/usr/bin/env sh

set -ex

echo "::group::Setup"

export PACKAGER="${INPUT_ABUILD_PACKAGER}"
export BUILD_DIR=./.apk
export APKREPO="${BUILD_DIR}/repo"
export APKKEYS="${BUILD_DIR}/keys"

echo "::group::Setup Build Dir"
mkdir -p ${BUILD_DIR}
echo "::endgroup::"
echo "::endgroup::"

echo "::group::Setup Keys"
mkdir -p ${APKKEYS}
printf -- '${INPUT_ABUILD_KEY_PRIV}' > ${APKKEYS}/${INPUT_ABUILD_KEY_NAME}.rsa
printf -- '${INPUT_ABUILD_KEY_PUB}' > ${APKKEYS}/${INPUT_ABUILD_KEY_NAME}.rsa.pub
ls -la "${APKKEYS}"
echo "::endgroup::"

echo "::group::Setup Repo"
mkdir -p ${APKREPO}
echo "::endgroup::"

echo "::group::Sign x86_64"
mkdir -p ${APKREPO}/x86_64
cp ./x86_64/*/*.apk ${APKREPO}/x86_64/
apk index -o ${APKREPO}/x86_64/APKINDEX.tar.gz ${APKREPO}/x86_64/*.apk
abuild-sign -k "${APKKEYS}/${INPUT_ABUILD_KEY_NAME}.rsa" "${APKREPO}/x86_64/APKINDEX.tar.gz"
echo "::endgroup::"

echo "::group::Add public key"
cp ${APKKEYS}/${INPUT_ABUILD_KEY_NAME}.rsa.pub ${APKREPO}/
echo "::endgroup::"

echo "::group::Create index"
cat << EOF > ${APKREPO}/index.md
# ACME DNS Proxy

\`\`\`bash
# Install key
wget -O "/etc/apk/keys/${INPUT_ABUILD_KEY_NAME}.rsa.pub" "${INPUT_ABUILD_REPO_URL}/${INPUT_ABUILD_KEY_NAME}.rsa.pub"

# Install repo
echo "${INPUT_ABUILD_REPO_URL}" >> /etc/apk/repositories
\`\`\` 
EOF

echo "::endgroup::"

echo "repo_path=${APKREPO}" >> $GITHUB_OUTPUT

#!/usr/bin/env sh

set -ex

set +x; echo "::group::Setup"; set -x
export PACKAGER="${INPUT_ABUILD_PACKAGER}"

export REPO_URL="${INPUT_ABUILD_REPO_URL}"

export BUILD_DIR_REL=.apk
export KEYS_DIR_REL="${BUILD_DIR_REL}/keys"
export REPO_DIR_REL="${BUILD_DIR_REL}/repo"

export BUILD_DIR="${GITHUB_WORKSPACE}/${BUILD_DIR_REL}"
export KEYS_DIR="${GITHUB_WORKSPACE}/${KEYS_DIR_REL}"
export REPO_DIR="${GITHUB_WORKSPACE}/${REPO_DIR_REL}"

export PRIVATE_KEY_NAME="${INPUT_ABUILD_KEY_NAME}.rsa"
export PRIVATE_KEY="${KEYS_DIR}/${PRIVATE_KEY_NAME}"

export PUBLIC_KEY_NAME="${INPUT_ABUILD_KEY_NAME}.rsa.pub"
export PUBLIC_KEY="${KEYS_DIR}/${PUBLIC_KEY_NAME}"


set +x; echo "::endgroup::"; set -x

set +x; echo "::group::Setup Build Dir"; set -x
mkdir -p ${BUILD_DIR}
set +x; echo "::endgroup::"; set -x

set +x; echo "::group::Setup Keys"; set -x
mkdir -p ${KEYS_DIR}
printf -- "${INPUT_ABUILD_KEY_PRIV}" > ${PRIVATE_KEY}
printf -- "${INPUT_ABUILD_KEY_PUB}" > ${PUBLIC_KEY}
set +x; echo "::endgroup::"; set -x

set +x; echo "::group::Setup Repo"; set -x
mkdir -p ${REPO_DIR}
set +x; echo "::endgroup::"; set -x

set +x; echo "::group::Sign x86_64"; set -x
mkdir -p ${REPO_DIR}/x86_64
cp ./x86_64/*/*.apk ${REPO_DIR}/x86_64/
apk index -o ${REPO_DIR}/x86_64/APKINDEX.tar.gz ${REPO_DIR}/x86_64/*.apk
abuild-sign -k "${PRIVATE_KEY}" "${REPO_DIR}/x86_64/APKINDEX.tar.gz"
set +x; echo "::endgroup::"; set -x

set +x; echo "::group::Add public key"; set -x
cp "${PUBLIC_KEY}" "${REPO_DIR}/"
set +x; echo "::endgroup::"; set -x

set +x; echo "::group::Create index"; set -x
cat << EOF > "${REPO_DIR}/index.md"
# ACME DNS Proxy

\`\`\`bash
# Install key
wget -O "/etc/apk/keys/${PUBLIC_KEY_NAME}" "${REPO_URL}/${PUBLIC_KEY_NAME}"

# Install repo
echo "${REPO_URL}" >> /etc/apk/repositories

\`\`\` 

* Sub [Sub](x86_64/acmednsproxy/acmednsproxy-openrc-0.1.5.apk)
* Sub [Sub](./x86_64/acmednsproxy/acmednsproxy-openrc-0.1.5.apk)
* Link [x86_64](x86_64.md)
* Link [x86_64](x86_64.md)
* Link [x86_64](x86_64)
* Link [x86_64](x86_64/index.md)
* Link [x86_64](./x86_64.md)
* Link [x86_64](./x86_64)
* Link [x86_64](./x86_64/index.md)

EOF

cat << EOF > "${REPO_DIR}/x86_64.md"
# x86_64 sub DNS Proxy

\`\`\`bash
# Install key
wget -O "/etc/apk/keys/${PUBLIC_KEY_NAME}" "${REPO_URL}/${PUBLIC_KEY_NAME}"

# Install repo
echo "${REPO_URL}" >> /etc/apk/repositories

\`\`\` 
EOF

cat << EOF > "${REPO_DIR}/x86_64/index.md"
# x86_64 DNS Proxy

\`\`\`bash
# Install key
wget -O "/etc/apk/keys/${PUBLIC_KEY_NAME}" "${REPO_URL}/${PUBLIC_KEY_NAME}"

# Install repo
echo "${REPO_URL}" >> /etc/apk/repositories

\`\`\` 
EOF

set +x; echo "::endgroup::"; set -x

echo "repo_path=${REPO_DIR_REL}" >> $GITHUB_OUTPUT

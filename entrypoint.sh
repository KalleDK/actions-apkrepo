#!/usr/bin/env sh

set -e

make_arch() {
    PKGS_PATH=$1
    ARCH=$2

    echo "::group::Sign ${ARCH}"
    mkdir -p "${REPO_DIR}/${ARCH}"
    
    for apk in $(find ${PKGS_PATH} -name "*-${ARCH}.apk"); do
        cp $apk ${REPO_DIR}/${ARCH}/$(basename $apk | sed s/-${ARCH}\.apk/.apk/)
    done
    echo "Creating index for ${ARCH}"
    apk index -o ${REPO_DIR}/${ARCH}/APKINDEX.tar.gz ${REPO_DIR}/${ARCH}/*.apk
    echo "Signing index for ${ARCH}"
    abuild-sign -k ${PRIVATE_KEY} ${REPO_DIR}/${ARCH}/APKINDEX.tar.gz
    

    cat << EOF > "${REPO_DIR}/${ARCH}/index.md"
# List ${ARCH}

\`\`\`bash
# Install key
wget -O "/etc/apk/keys/${PUBLIC_KEY_NAME}" "${REPO_URL}/${PUBLIC_KEY_NAME}"

# Install repo
echo "${REPO_URL}" >> /etc/apk/repositories

\`\`\` 
EOF

    for x in $(find "${REPO_DIR}/${ARCH}" -type f -name '*.apk' -exec basename {} \;); do echo "* [$x]($x)"; done >> "${REPO_DIR}/${ARCH}/index.md"
    
    echo "* [${ARCH}](${ARCH}/)" >> "${REPO_DIR}/index.md"

    echo "::endgroup::"
}

echo "::group::Setup"
export PACKAGER="${INPUT_ABUILD_PACKAGER}"

export PKGS_PATH="${INPUT_PKGS_PATH}"
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

echo "Packager: $PACKAGER"
echo "Package Dir: $PKGS_PATH"
echo "Keyname: ${INPUT_ABUILD_KEY_NAME}"
echo "::endgroup::"

echo "::group::Setup Build Dir"
mkdir -p ${BUILD_DIR}
echo "::endgroup::"

echo "::group::Setup Keys"
mkdir -p ${KEYS_DIR}
printf -- "${INPUT_ABUILD_KEY_PRIV}" > ${PRIVATE_KEY}
printf -- "${INPUT_ABUILD_KEY_PUB}" > ${PUBLIC_KEY}
echo "::endgroup::"
find .
ls -la ${KEYS_DIR}
echo "::group::Setup Repo"
mkdir -p ${REPO_DIR}
cp "${PUBLIC_KEY}" "${REPO_DIR}/"

cat << EOF > ${REPO_DIR}/index.md
# APK Registry

\`\`\`bash
# Install key
wget -O "/etc/apk/keys/${PUBLIC_KEY_NAME}" "${REPO_URL}/${PUBLIC_KEY_NAME}"

# Install repo
echo "${REPO_URL}" >> /etc/apk/repositories

\`\`\` 

EOF

echo "::endgroup::"

make_arch "${PKGS_PATH}" x86_64
make_arch "${PKGS_PATH}" x86

echo "repo_path=${REPO_DIR_REL}" >> $GITHUB_OUTPUT

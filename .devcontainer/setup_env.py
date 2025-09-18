#!/usr/bin/env python3

import os
import pathlib
import subprocess

PACKAGER = os.getenv("PACKAGER", "Joe Smith <joe.smith@example.com>")

TMPL = '''export GITHUB_TOKEN=ghp_yourtokenhere
export INPUT_PKGS_PATH="src"
export INPUT_ABUILD_REPO_URL="https://example.com/repo"
export INPUT_ABUILD_PACKAGER="{PACKAGER}"
export INPUT_ABUILD_KEY_NAME="{KEY_NAME}"
export INPUT_ABUILD_KEY_PRIV={KEY_PRIV}
export INPUT_ABUILD_KEY_PUB={KEY_PUB}
export GITHUB_OUTPUT="./github-output"
'''

envrc_file = pathlib.Path('.envrc')

if not envrc_file.exists():
    subprocess.run(['abuild-keygen', '-n'], env={**os.environ, "PACKAGER": PACKAGER}, check=True, capture_output=True)
    abuild_path = pathlib.Path.home().joinpath('.abuild')
    priv = next(abuild_path.glob('*.rsa'))
    pub = priv.with_suffix('.rsa.pub')
    envrc_file.write_text(TMPL.format(
        PACKAGER=PACKAGER,
        KEY_NAME=priv.stem,
        KEY_PRIV=repr(priv.read_text().strip()),
        KEY_PUB=repr(pub.read_text().strip()),
    ))
    pub.unlink()
    priv.unlink()
    abuild_path.rmdir()

subprocess.run(['direnv', 'allow'], check=True)
subprocess.run(["git", "config", "--global", "--unset-all", "credential.https://github.com.helper"], check=False)
subprocess.run(["git", "config", "--global", "--unset-all", "credential.https://gist.github.com.helper"], check=False)
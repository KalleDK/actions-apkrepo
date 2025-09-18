import subprocess
subprocess.run(["git", "config", "--global", "--unset-all", "credential.https://github.com.helper"], check=False)
subprocess.run(["git", "config", "--global", "--unset-all", "credential.https://gist.github.com.helper"], check=False)
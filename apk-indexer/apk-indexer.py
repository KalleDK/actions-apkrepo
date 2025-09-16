import contextlib
import pathlib
import tarfile
import configparser
import dataclasses
import os
import pydantic
from rich.console import Console
from rich.table import Table
import subprocess


console = Console()


@contextlib.contextmanager
def with_group(name: str):
    console.print(f"::group::{name}")
    try:
        yield
    finally:
        console.print("::endgroup::")


@dataclasses.dataclass(slots=True)
class KeyMgr:
    path: pathlib.Path
    name: str = dataclasses.field(
        default_factory=lambda: os.environ["INPUT_ABUILD_KEY_NAME"]
    )
    private_key: bytes = dataclasses.field(
        default_factory=lambda: os.environ["INPUT_ABUILD_KEY_PRIV"].encode()
    )
    public_key: bytes = dataclasses.field(
        default_factory=lambda: os.environ["INPUT_ABUILD_KEY_PUB"].encode()
    )

    @property
    def public_key_name(self) -> str:
        return self.name + ".rsa.pub"

    @property
    def private_key_name(self) -> str:
        return self.name + ".rsa"

    def sign(self, file: pathlib.Path) -> None:
        import subprocess

        std = subprocess.run(
            ["abuild-sign", "-k", self.path.absolute() / self.private_key_name, file],
            capture_output=True,
            text=True,
        )
        print(std.stderr)
        print(std.stdout)

    def install(self):
        with with_group("Setup Keys"):
            console.print(f"Installing keys to '{self.path}'")
            self.path.mkdir(parents=True, exist_ok=True)
            self.install_private_key(self.path)
            self.install_public_key(self.path)

    def install_private_key(self, dest: pathlib.Path) -> pathlib.Path:
        dest_file = dest.joinpath(self.private_key_name)
        console.print(f"Installing private key to '{dest_file}'")
        dest_file.write_bytes(self.private_key)
        return dest_file

    def install_public_key(self, dest: pathlib.Path) -> pathlib.Path:
        dest_file = dest.joinpath(self.public_key_name)
        console.print(f"Installing public key to '{dest_file}'")
        dest_file.write_bytes(self.public_key)
        return dest_file


class PKGINFO(pydantic.BaseModel):
    pkgname: str
    pkgver: str
    arch: str
    size: int
    pkgdesc: str
    url: str
    maintainer: str
    license: str
    datahash: str

    @property
    def filename(self) -> str:
        return f"{self.pkgname}-{self.pkgver}.apk"


@dataclasses.dataclass(slots=True)
class SourcePkg:
    path: pathlib.Path
    info: PKGINFO


def get_apk_info(path: pathlib.Path):
    with tarfile.open(path, "r:gz") as tar:
        apk_info_file = tar.extractfile(".PKGINFO")
        if apk_info_file is None:
            raise ValueError("No .PKGINFO in APK")
        config = configparser.ConfigParser()
        config.read_string("[PKGINFO]\n" + apk_info_file.read().decode())
        return PKGINFO(**config["PKGINFO"])

APK_INDEX = """
# APK Registry

```bash
# Install key
wget -O "/etc/apk/keys/{PUBLIC_KEY_NAME}" "{REPO_URL}/{PUBLIC_KEY_NAME}"
sudo wget -O "/etc/apk/keys/{PUBLIC_KEY_NAME}" "{REPO_URL}/{PUBLIC_KEY_NAME}"

# Install repo
echo "{REPO_URL}" >> /etc/apk/repositories
echo "{REPO_URL}" | sudo tee -a /etc/apk/repositories

{archs}

``` 
"""


def md_repo_index(
    public_key_name: str, repo_url: str, archs: list[str]
) -> str:
    arch_lines = [md_pkg_line(arch) for arch in archs]
    return APK_INDEX.format(
        PUBLIC_KEY_NAME=public_key_name,
        REPO_URL=repo_url,
        archs="\n".join(arch_lines),
    )

ARCH_INDEX = """# List {ARCH}

```bash
# Install key
wget -O "/etc/apk/keys/{PUBLIC_KEY_NAME}" "{REPO_URL}/{PUBLIC_KEY_NAME}"
sudo wget -O "/etc/apk/keys/{PUBLIC_KEY_NAME}" "{REPO_URL}/{PUBLIC_KEY_NAME}"

# Install repo
echo "{REPO_URL}" >> /etc/apk/repositories
echo "{REPO_URL}" | sudo tee -a /etc/apk/repositories

{pkgs}

```
"""


def md_arch_index(
    arch: str, public_key_name: str, repo_url: str, filenames: list[str]
) -> str:
    pkgs_lines = [md_pkg_line(filename) for filename in filenames]
    return ARCH_INDEX.format(
        ARCH=arch,
        PUBLIC_KEY_NAME=public_key_name,
        REPO_URL=repo_url,
        pkgs="\n".join(pkgs_lines),
    )


def md_pkg_line(filename: str) -> str:
    return f"* [{filename}]({filename})"


@dataclasses.dataclass(slots=True)
class Repo:
    path: pathlib.Path
    keys: KeyMgr
    repo_url: str = dataclasses.field(
        default_factory=lambda: os.environ["INPUT_ABUILD_REPO_URL"]
    )

    def prepare(self) -> None:
        with with_group("Setup Repo"):
            console.print(f"Preparing repo at '{self.path}'")
            self.path.mkdir(parents=True, exist_ok=True)

    def _create_apk_index(self, arch_path: pathlib.Path) -> pathlib.Path:
        apk_index_path = arch_path / "APKINDEX.tar.gz"
        print(f"Creating APK index at '{apk_index_path}'")
        std = subprocess.run(
            [
                "apk",
                "index",
                "--allow-untrusted",
                "-o",
                apk_index_path,
                *list(arch_path.glob("*.apk")),
            ],
            capture_output=True,
            text=True,
        )
        print(std.stderr)
        print(std.stdout)
        self.keys.sign(apk_index_path)
        return apk_index_path

    def _create_arch_repo(self, arch: str, pkgs: list[SourcePkg]) -> None:
        with with_group(f"Creating repo for arch '{arch}'"):
            arch_path = self.path / arch
            arch_path.mkdir(parents=True, exist_ok=True)

            pkgs.sort(key=lambda p: p.info.pkgname)

            print(f"Copying {len(pkgs)} packages to '{arch_path}'")
            for pkg_src in pkgs:
                dest = arch_path / pkg_src.info.filename
                dest.write_bytes(pkg_src.path.read_bytes())

            index_file = arch_path.joinpath("index.md")
            print(f"Creating '{index_file}'")
            apk_index = self._create_apk_index(arch_path)

            filenames = [apk_index.name] + [pkg.info.filename for pkg in pkgs]
            index_md = md_arch_index(
                arch=arch,
                public_key_name=self.keys.public_key_name,
                repo_url=self.repo_url,
                filenames=filenames,
            )
            index_file.write_text(index_md)

    def create_repo(self, pkgs: dict[str, list[SourcePkg]]) -> None:
        for arch, pkg_list in pkgs.items():
            self._create_arch_repo(arch, pkg_list)
        
        repo_index_file = self.path / "index.md"
        print(f"Creating repo index at '{repo_index_file}'")
        repo_index_file.write_text(
            md_repo_index(
                public_key_name=self.keys.public_key_name,
                repo_url=self.repo_url,
                archs=sorted(list(pkgs.keys())),
            )
        )
        self.keys.install_public_key(self.path)


def print_apk_summary(pkgs: dict[str, list[SourcePkg]]) -> None:
    table = Table(title="APK Summary")
    table.add_column("Filename", justify="left", style="cyan", no_wrap=True)
    table.add_column("Package Name", style="magenta")
    table.add_column("Version", justify="right", style="green")
    table.add_column("Arch", justify="right", style="yellow")
    for pkg_list in pkgs.values():
        for pkg in pkg_list:
            table.add_row(
                pkg.path.name, pkg.info.pkgname, pkg.info.pkgver, pkg.info.arch
            )
    console.print(table)


def scan_dir_for_apks(dir: pathlib.Path) -> dict[str, list[SourcePkg]]:
    with with_group(f"Scanning '{dir}' for APKs"):
        pkgs: dict[str, list[SourcePkg]] = {}
        for apk in dir.glob("**/*.apk"):
            apk_info = get_apk_info(apk)
            apk_src = SourcePkg(path=apk, info=apk_info)
            pkgs.setdefault(apk_info.arch, []).append(apk_src)
        print_apk_summary(pkgs)
        return pkgs


@dataclasses.dataclass(slots=True)
class APKIndexer:
    key: KeyMgr
    repo: Repo

    @classmethod
    def create(cls, path: pathlib.Path):
        keys = KeyMgr(path.joinpath("keys"))
        repo = Repo(
            path=path.joinpath("repo"),
            keys=keys,
        )
        return cls(key=keys, repo=repo)

    def prepare(self):
        self.key.install()
        self.repo.prepare()

    def import_pkgs(self, pkgs: dict[str, list[SourcePkg]]) -> None:
        self.repo.create_repo(pkgs)


def main() -> None:
    build_path = pathlib.Path(".apk")
    apki = APKIndexer.create(build_path)
    apki.prepare()
    pkgs = scan_dir_for_apks(pathlib.Path(os.environ["INPUT_PKGS_PATH"]))
    apki.import_pkgs(pkgs)
    with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
        fh.write(f"repo_path={apki.repo.path}\n")
    

if __name__ == "__main__":
    main()

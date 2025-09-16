import contextlib
import pathlib
import tarfile
import configparser
import dataclasses
import os
from rich.console import Console
from rich.table import Table

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
    name: str = dataclasses.field(default_factory=lambda: os.environ["INPUT_ABUILD_KEY_NAME"])
    private_key: bytes = dataclasses.field(default_factory=lambda: os.environ["INPUT_ABUILD_KEY_PRIV"].encode())
    public_key: bytes = dataclasses.field(default_factory=lambda: os.environ["INPUT_ABUILD_KEY_PUB"].encode())

    @property
    def public_key_name(self) -> str:
        return self.name + ".rsa.pub"

    @property
    def private_key_name(self) -> str:
        return self.name + ".rsa"

    def install(self):
        with with_group("Setup Keys"):
            console.print("Installing keys to", self.path)
            self.path.mkdir(parents=True, exist_ok=True)
            self.install_private_key(self.path)
            self.install_public_key(self.path)

    def install_private_key(self, dest: pathlib.Path) -> pathlib.Path:
        dest_file = dest.joinpath(self.private_key_name)
        console.print("Installing private key to", dest_file)
        dest_file.write_bytes(self.private_key)
        return dest_file

    def install_public_key(self, dest: pathlib.Path) -> pathlib.Path:
        dest_file = dest.joinpath(self.public_key_name)
        console.print("Installing public key to", dest_file)
        dest_file.write_bytes(self.public_key)
        return dest_file


@dataclasses.dataclass(slots=True)
class PKGINFO:
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


ARCH_INDEX = """# List {ARCH}

```bash
# Install key
wget -O "/etc/apk/keys/{PUBLIC_KEY_NAME}" "{REPO_URL}/{PUBLIC_KEY_NAME}"

# Install repo
echo "{REPO_URL}" >> /etc/apk/repositories

{pkgs}

```
"""

PKG_LINE = "* [{pkgname}]({filename})"



@dataclasses.dataclass(slots=True)
class Repo:
    path: pathlib.Path
    keys: KeyMgr
    repo_url: str = dataclasses.field(default_factory=lambda: os.environ["INPUT_ABUILD_REPO_URL"])
    

    def prepare(self) -> None:
        with with_group("Setup Repo"):
            console.print(f"Preparing repo at '{self.path}'")
            self.path.mkdir(parents=True, exist_ok=True)


    def _create_arch_repo(self, arch: str, pkgs: list[SourcePkg]) -> None:
        arch_path = self.path / arch
        arch_path.mkdir(parents=True, exist_ok=True)
        pkg_lines = []
        for pkg_src in pkgs:
            dest = arch_path / pkg_src.info.filename
            dest.write_bytes(pkg_src.path.read_bytes())
            pkg_lines.append(
                PKG_LINE.format(
                    pkgname=pkg_src.info.pkgname, filename=pkg_src.info.filename
                )
            )
        print(list(arch_path.glob("*.apk")))
        arch_path.joinpath("index.md").write_text(
            ARCH_INDEX.format(
                ARCH=arch,
                PUBLIC_KEY_NAME=self.keys.public_key_name,
                REPO_URL=self.repo_url,
                pkgs="\n".join(pkg_lines),
            )
        )

    def create_repo(self, pkgs: dict[str, list[SourcePkg]]) -> None:
        for arch, pkg_list in pkgs.items():
            self._create_arch_repo(arch, pkg_list)

    def add_pkgs_from_dir(self, dir: pathlib.Path) -> None:
        for apk in dir.glob("*.apk"):
            self.add_pkg(apk)

def print_apk_summary(pkgs: dict[str, list[SourcePkg]]) -> None:
    table = Table(title="APK Summary")
    table.add_column("Filename", justify="left", style="cyan", no_wrap=True)
    table.add_column("Package Name", style="magenta")
    table.add_column("Version", justify="right", style="green")
    table.add_column("Arch", justify="right", style="yellow")
    for pkg_list in pkgs.values():
        for pkg in pkg_list:
            table.add_row(pkg.path.name, pkg.info.pkgname, pkg.info.pkgver, pkg.info.arch)
    console.print(table)

def scan_dir_for_apks(dir: pathlib.Path) -> dict[str, list[SourcePkg]]:
    with with_group(f"Scanning '{dir}' for APKs"):
        pkgs: dict[str, list[SourcePkg]] = {}
        for apk in dir.glob("*.apk"):
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
        repo = Repo(path=path.joinpath("repo"), keys=keys,)
        return cls(key=keys, repo=repo)
    
    def prepare(self):
        self.key.install()
        self.repo.prepare()

    def import_pkgs(self, pkgs: dict[str, list[SourcePkg]]) -> None:
        self.repo.create_repo(pkgs)

def main() -> None:
    apki = APKIndexer.create(pathlib.Path(".apk_test"))
    apki.prepare()
    pkgs = scan_dir_for_apks(pathlib.Path(os.environ["INPUT_PKGS_PATH"]))
    apki.import_pkgs(pkgs)
    



if __name__ == "__main__":
    main()

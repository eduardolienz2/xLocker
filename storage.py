"""Vault storage: encrypted file in %APPDATA%\\SecureVault. Holds the key only in memory."""
import base64, json, os, time, uuid
from pathlib import Path
import vault_crypto as vc

b64e = lambda b: base64.b64encode(b).decode()
b64d = lambda s: base64.b64decode(s)


def default_path() -> Path:
    base = Path(os.environ.get("APPDATA") or Path.home())
    return base / "SecureVault" / "vault.dat"


class VaultStore:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else default_path()
        self.items: list[dict] = []
        self._key: bytearray | None = None
        self._salt = b""
        self._kdf = dict(vc.KDF_DEFAULT)

    def exists(self) -> bool:
        return self.path.exists()

    @property
    def unlocked(self) -> bool:
        return self._key is not None

    def create(self, password: str) -> None:
        self._salt, self._kdf, self.items = vc.new_salt(), dict(vc.KDF_DEFAULT), []
        self._key = bytearray(vc.derive_key(password, self._salt, self._kdf))
        self._save()

    def unlock(self, password: str) -> None:
        data = json.loads(self.path.read_text("utf-8"))
        salt, kdf = b64d(data["salt"]), data["kdf"]
        key = vc.derive_key(password, salt, kdf)
        plain = vc.decrypt(key, b64d(data["nonce"]), b64d(data["ct"]))  # raises WrongPassword
        self._salt, self._kdf, self._key = salt, kdf, bytearray(key)
        self.items = json.loads(plain)

    def lock(self) -> None:
        if self._key:
            for i in range(len(self._key)):    # best-effort wipe
                self._key[i] = 0
        self._key, self.items = None, []

    def add(self, site: str, user: str, password: str) -> None:
        self.items.insert(0, {"id": uuid.uuid4().hex, "site": site, "user": user,
                              "password": password, "created": int(time.time())})
        self._save()

    def delete(self, item_id: str) -> None:
        self.items = [i for i in self.items if i["id"] != item_id]
        self._save()

    def _save(self) -> None:
        if self._key is None:
            raise RuntimeError("Cannot save a locked vault.")
        nonce, ct = vc.encrypt(bytes(self._key), json.dumps(self.items).encode("utf-8"))
        blob = {"v": 1, "kdf": self._kdf, "salt": b64e(self._salt), "nonce": b64e(nonce), "ct": b64e(ct)}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(blob), "utf-8")
        os.replace(tmp, self.path)             # atomic: no half-written vault

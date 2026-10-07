# xLocker

xLocker is a Windows desktop password vault and password generator. Vault entries are encrypted locally with AES-256-GCM, using a key derived from the master password with scrypt. Vault data is stored in `%APPDATA%\SecureVault\vault.dat`; it is not synchronized to a server.

## Run from source

Install Python 3.10 or newer, then run:

```powershell
python -m pip install -r requirements.txt
python app.py
```

The master password cannot be recovered if it is forgotten. Back up the encrypted vault file before making system changes.

## Build on Windows

Run `build.bat` to install the listed dependencies, create the application in `dist\xLocker`, and build the installer. Inno Setup 6 must be installed for the installer step.

Generated build output and installer executables are excluded from Git.

# xLocker

xLocker is a Windows desktop password vault built with Python and Tkinter. Vault data is encrypted locally; the application does not synchronize vault contents to a server.

## Download

Download the latest `xLocker_Setup.exe` from the repository's [Releases](../../releases) page. Run the installer and follow the prompts. The app requires a valid, machine-bound license and a master password.

Existing vaults created by earlier versions are migrated to Scrypt after a successful sign-in. The migration requires setting a master password of at least 14 characters. Back up the vault files before upgrading.

## Security and licenses

- The application verifies offline ECDSA license signatures using an embedded public key. The corresponding private signing key must remain outside this repository and all distributed files.
- Offline license checks cannot prevent a determined user from modifying a locally controlled executable.
- Master passwords are processed locally; forgetting the master password can make the vault unrecoverable.
- Passwords copied from the vault are cleared from the clipboard after 30 seconds if they have not been replaced.
- Review the included license terms before use. All rights are reserved; publishing this repository does not grant permission to modify or redistribute the software.

## Building on Windows

Install Python, PyArmor, PyInstaller, and the Python `cryptography` package. Then run `build.bat` from the project directory to create `dist\GerenciadorDeSenhas.exe`.

To create the installer, install Inno Setup 6 and compile `Installer\xlocker_installer.iss`. The generated installer is written to `Installer\Output\xLocker_Setup.exe`. Generated binaries and build files are intentionally excluded from Git; published installers should be attached to GitHub Releases.

## Repository contents

- `src/` — desktop application source
- `assets/` — application icon
- `Installer/` — installer script, license terms, and EULAs
- `build.bat` — Windows executable build script

Never commit private signing keys, customer/license records, `.env` files, vault data, or generated executables to the source repository.

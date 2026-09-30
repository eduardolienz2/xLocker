#define MyAppName "xLocker"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Lienz"
#define MyAppExeName "GerenciadorDeSenhas.exe"

[Setup]
AppId={{9C8F7A21-3B44-4E11-A912-7F98D4C5A111}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://lienz.pt
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=Output
OutputBaseFilename=xLocker_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\xLocker.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"; LicenseFile: "EULA_Portugues.txt"
Name: "english"; MessagesFile: "compiler:Default.isl"; LicenseFile: "EULA_English.txt"

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.TXT"; DestDir: "{app}"
Source: "LICENCA.TXT"; DestDir: "{app}"
Source: "EULA_Portugues.txt"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "EULA_English.txt"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Opções adicionais:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Executar xLocker"; Flags: nowait postinstall skipifsilent

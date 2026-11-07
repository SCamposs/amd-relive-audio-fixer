#define MyAppName "Fixer de Áudio AMD ReLive"
#define MyAppVersion "1.1.0"
#define MyAppExeName "FixerAudioAMD.exe"

[Setup]
AppId={{A7F99BD5-C57E-4C63-A18D-13D55C26BB8A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=SCamposs
AppPublisherURL=https://github.com/SCamposs/amd-relive-audio-fixer
AppSupportURL=https://github.com/SCamposs/amd-relive-audio-fixer/issues
AppUpdatesURL=https://github.com/SCamposs/amd-relive-audio-fixer/releases
DefaultDirName={localappdata}\Programs\FixerAudioAMD
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=.
OutputBaseFilename=FixerAudioAMD-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=assets\app-icon.ico
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar um atalho na área de trabalho"; GroupDescription: "Atalhos adicionais:"; Flags: unchecked

[Files]
Source: "FixerAudioAMD.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir {#MyAppName}"; Flags: nowait postinstall skipifsilent

#define MyAppName "IPAN Optimizer"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "IPAN"
#define MyAppExeName "IPANOptimizer.exe"

[Setup]
AppId={{9D15D005-8022-4CC7-8F9A-7EEC132EF4B5}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\IPAN Optimizer
DefaultGroupName=IPAN Optimizer
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist-installer
OutputBaseFilename=IPANOptimizer-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=yes
RestartApplications=no

[Files]
Source: "..\dist\IPANOptimizer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\IPAN Optimizer"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\IPAN Optimizer"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Buat pintasan desktop"; GroupDescription: "Pintasan:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Jalankan IPAN Optimizer"; Flags: nowait postinstall skipifsilent

[Code]
function WebView2Installed(): Boolean;
var
  Version: String;
begin
  Result :=
    RegQueryStringValue(
      HKLM32,
      'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}',
      'pv',
      Version
    ) or
    RegQueryStringValue(
      HKCU,
      'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}',
      'pv',
      Version
    );
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  if not WebView2Installed() then
  begin
    MsgBox(
      'Microsoft Edge WebView2 Runtime belum terdeteksi.' + #13#10 +
      'Instalasi tidak mengunduh komponen secara diam-diam. ' +
      'Pasang WebView2 Evergreen resmi, lalu jalankan installer ini kembali.',
      mbError,
      MB_OK
    );
    Result := False;
  end;
end;

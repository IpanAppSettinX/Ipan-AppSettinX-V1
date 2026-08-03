#define MyAppName "IPAN Optimizer"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "IPAN"
#define MyAppExeName "IPANOptimizer.exe"
#define WebView2Bootstrapper "MicrosoftEdgeWebview2Setup.exe"

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
Source: "..\dist\IPANOptimizer\_internal\ipan_optimizer\data\{#WebView2Bootstrapper}"; DestDir: "{tmp}"; Flags: deleteafterinstall noregerror skipifsourcedoesntexist

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
  if Result and (Version = '0.0.0.0') then
    Result := False;
end;

function InitializeSetup(): Boolean;
var
  BootstrapperPath: String;
  ResultCode: Integer;
begin
  Result := True;
  if not WebView2Installed() then
  begin
    BootstrapperPath := ExpandConstant('{tmp}\{#WebView2Bootstrapper}');
    { ExtractTemporaryFile copies a file declared in [Files] into {tmp}. The
      bootstrapper ships inside the bundle because we collect the entire
      dist\IPANOptimizer folder (which contains _internal\ipan_optimizer\data). }
    ExtractTemporaryFile('{#WebView2Bootstrapper}');
    MsgBox(
      'Microsoft Edge WebView2 Runtime belum terdeteksi.' + #13#10 +
      'Aplikasi akan menjalankan installer resmi Microsoft WebView2 Evergreen.' + #13#10 +
      'Konfirmasi instalasi pada jendela installer Microsoft yang muncul.',
      mbInformation,
      MB_OK
    );
    if not Exec(BootstrapperPath, '', '', SW_SHOW, ewWaitUntilTerminated, ResultCode) then
    begin
      MsgBox(
        'Gagal menjalankan installer WebView2 (' + IntToStr(ResultCode) + '). ' +
        'Pasang Microsoft Edge WebView2 Runtime Evergreen secara manual, ' +
        'lalu jalankan installer ini kembali.',
        mbError,
        MB_OK
      );
      Result := False;
      Exit;
    end;
    if not WebView2Installed() then
    begin
      MsgBox(
        'Instalasi WebView2 selesai tetapi runtime masih belum terdeteksi. ' +
        'Pasang Microsoft Edge WebView2 Runtime Evergreen secara manual, ' +
        'lalu jalankan installer ini kembali.',
        mbError,
        MB_OK
      );
      Result := False;
    end;
  end;
end;

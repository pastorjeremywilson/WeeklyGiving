; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "Weekly Giving"
#define MyAppVersion "1.4.2"
#define MyAppExeName "Weekly Giving.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{942DB2B1-CC18-435B-8B07-7D8CC8B7B66E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=C:\Users\pasto\Desktop\output\Weekly Giving\_internal\resources\gpl-3.0.rtf
WizardImageFile=C:\Users\pasto\Desktop\output\Weekly Giving\_internal\resources\installImage.bmp
WizardSmallImageFile = C:\Users\pasto\Desktop\output\Weekly Giving\_internal\resources\installImageSmall.bmp
; Uncomment the following line to run in non administrative install mode (install for current user only.)
;PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=C:\Users\pasto\Desktop\output\Weekly Giving
OutputBaseFilename=Setup Weekly Giving v.{#MyAppVersion}
SetupIconFile=C:\Users\pasto\Desktop\output\Weekly Giving\_internal\resources\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "C:\Users\pasto\Desktop\output\Weekly Giving\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\pasto\Desktop\output\Weekly Giving\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\Users\pasto\Desktop\output\Weekly Giving\_internal\README.html"; DestDir: "{app}"; Flags: isreadme
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent


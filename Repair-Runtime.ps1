# Rebuilds ModSwap's private Python (the "runtime" folder) when ModSwap says "Couldn't start the engine ... not a valid application".
# It downloads the official embeddable Python 3.12 from python.org, installs pip, then every package in requirements.txt. Your old runtime folder is kept (renamed), not deleted.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
if (-not (Test-Path (Join-Path $root 'modswap'))) { throw "Put Repair-Runtime.bat and Repair-Runtime.ps1 in your ModSwap folder (the one that has ModSwap.exe and the 'modswap' folder), then run it again." }
$ver = '3.12.8'
$tmp = Join-Path $env:TEMP 'modswap_runtime'
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
$zip = Join-Path $tmp "python-$ver-embed-amd64.zip"
Write-Host "1/5  downloading Python $ver ..."
Invoke-WebRequest "https://www.python.org/ftp/python/$ver/python-$ver-embed-amd64.zip" -OutFile $zip -UseBasicParsing
if (Test-Path (Join-Path $root 'runtime')) {
    $old = 'runtime_broken_' + (Get-Date -Format 'yyyyMMdd_HHmmss')
    Rename-Item (Join-Path $root 'runtime') $old
    Write-Host "     the old runtime folder was kept as '$old' (delete it when everything works)"
}
Write-Host "2/5  unpacking ..."
Expand-Archive -Path $zip -DestinationPath (Join-Path $root 'runtime')
$pth = Get-ChildItem (Join-Path $root 'runtime') -Filter 'python*._pth' | Select-Object -First 1
(Get-Content $pth.FullName) -replace '^#\s*import site', 'import site' | Set-Content $pth.FullName
$py = Join-Path $root 'runtime\python.exe'
Write-Host "3/5  installing pip ..."
$gp = Join-Path $tmp 'get-pip.py'
Invoke-WebRequest 'https://bootstrap.pypa.io/get-pip.py' -OutFile $gp -UseBasicParsing
& $py $gp --no-warn-script-location
if ($LASTEXITCODE -ne 0) { throw 'pip could not be installed' }
Write-Host "4/5  installing ModSwap's packages (a few minutes) ..."
# the embeddable Python has no setuptools, and its sandboxed builds can not see one: install it first and build packages (tpk_ar has no ready-made wheel) with --no-build-isolation
& $py -m pip install --no-warn-script-location setuptools wheel
if ($LASTEXITCODE -ne 0) { throw 'setuptools could not be installed' }
& $py -m pip install --no-warn-script-location --no-build-isolation -r (Join-Path $root 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'a package could not be installed (see the red text above)' }
Write-Host "5/5  checking ..."
& $py -c "import numpy, PIL, lz4.block, etcpak, trimesh, UnityPy, texture2ddecoder; print('runtime OK: Python', __import__('sys').version.split()[0])"
if ($LASTEXITCODE -ne 0) { throw 'the new runtime does not start correctly' }
Write-Host ''
Write-Host 'Done. Open ModSwap.exe again.' -ForegroundColor Green

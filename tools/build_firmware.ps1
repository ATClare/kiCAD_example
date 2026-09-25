param([switch]$Upload, [string]$Port)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$driveName = $null
foreach ($letter in @('R','S','T','U','V','W','X','Y','Z')) {
    if (-not (Test-Path ($letter + ':/'))) { $driveName = $letter + ':'; break }
}
if (-not $driveName) { throw 'No free temporary drive letter for the Windows build workaround.' }
$oldPythonPath = $env:PYTHONPATH
$oldPioDir = $env:PLATFORMIO_CORE_DIR
$buildExit = 1
try {
    subst $driveName $projectRoot
    if ($LASTEXITCODE -ne 0) { throw 'Could not create temporary workspace drive mapping.' }
    if (Test-Path (Join-Path $projectRoot '.tools/python/platformio')) {
        $env:PYTHONPATH = "$driveName/.tools/python"
        $env:PLATFORMIO_CORE_DIR = "$driveName/.tools/platformio"
    }
    $buildArgs = @('-m','platformio','run','-d',"$driveName/firmware",'-j','4')
    if ($Upload) {
        if (-not $Port) { throw 'Specify -Port COMx when uploading.' }
        $buildArgs += @('-t','upload','--upload-port',$Port)
    }
    & python @buildArgs
    $buildExit = $LASTEXITCODE
} finally {
    subst $driveName /D
    $env:PYTHONPATH = $oldPythonPath
    $env:PLATFORMIO_CORE_DIR = $oldPioDir
}
exit $buildExit

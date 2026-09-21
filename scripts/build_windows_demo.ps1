param(
    [string]$PythonCommand = "python"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BuildRoot = Join-Path $ProjectRoot "demo-build"
$DistRoot = Join-Path $ProjectRoot "demo-dist"
$DatabasePath = Join-Path $BuildRoot "news.db"
$PackageDirectory = Join-Path $DistRoot "FastApiVueNews"
$ZipPath = Join-Path $DistRoot "FastApiVueNews-Windows-x64.zip"

function Assert-ProjectChild([string]$PathToCheck) {
    $absolutePath = [System.IO.Path]::GetFullPath($PathToCheck)
    $rootWithSeparator = $ProjectRoot.TrimEnd('\') + '\'
    if (-not $absolutePath.StartsWith($rootWithSeparator, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to operate outside the project directory: $absolutePath"
    }
}

Assert-ProjectChild $BuildRoot
Assert-ProjectChild $DistRoot
Assert-ProjectChild $DatabasePath
Assert-ProjectChild $ZipPath

Push-Location $ProjectRoot
try {
    New-Item -ItemType Directory -Force -Path $BuildRoot | Out-Null
    New-Item -ItemType Directory -Force -Path $DistRoot | Out-Null
    if (Test-Path -LiteralPath $DatabasePath) {
        Remove-Item -LiteralPath $DatabasePath -Force
    }
    if (Test-Path -LiteralPath $ZipPath) {
        Remove-Item -LiteralPath $ZipPath -Force
    }

    Push-Location (Join-Path $ProjectRoot "xwzx-news")
    try {
        npm run build:demo
    }
    finally {
        Pop-Location
    }

    & $PythonCommand -m scripts.build_demo_database --output $DatabasePath
    if ($LASTEXITCODE -ne 0) { throw "Failed to build the demo database" }

    & $PythonCommand -m PyInstaller `
        --noconfirm `
        --clean `
        --distpath $DistRoot `
        --workpath (Join-Path $BuildRoot "pyinstaller") `
        (Join-Path $ProjectRoot "FastApiVueNews.spec")
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller packaging failed" }

    Copy-Item -LiteralPath $DatabasePath -Destination (Join-Path $PackageDirectory "news.db") -Force
    Copy-Item -LiteralPath (Join-Path $ProjectRoot "DEMO_README.txt") -Destination $PackageDirectory -Force
    Compress-Archive -Path (Join-Path $PackageDirectory "*") -DestinationPath $ZipPath -CompressionLevel Optimal
    Write-Host "Demo package created: $ZipPath"
}
finally {
    Pop-Location
}

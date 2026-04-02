param(
    [ValidateSet("dongfeng","huangshi")]
    [string]$Edition = "dongfeng",

    [string]$GitUrl = "",

    [string]$InstallDir = ""
)

# 默认仓库映射
$repoMap = @{
    dongfeng = "https://github.com/Infitidy/light-transfer-dongfeng.git"
    huangshi = "https://github.com/Infitidy/light-transfer-skill-huangshi.git"
}

if (-not $GitUrl) {
    $GitUrl = $repoMap[$Edition]
}

if (-not $InstallDir) {
    $baseDir = "F:\u-claw\portable\app\core\node_modules\openclaw\skills"
    $InstallDir = Join-Path $baseDir "light-transfer-$Edition"
}

Write-Host "=== Light Transfer Skill Installer ===" -ForegroundColor Cyan
Write-Host "Edition: $Edition"
Write-Host "Git URL: $GitUrl"
Write-Host "Install Dir: $InstallDir"
Write-Host ""

# 确保目标父目录存在
$parentDir = Split-Path $InstallDir -Parent
if (-not (Test-Path $parentDir)) {
    New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
}

# 检查并备份现有目录
if (Test-Path $InstallDir) {
    Write-Host "Target directory already exists. Backing up..." -ForegroundColor Yellow
    $backup = "$InstallDir.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Rename-Item $InstallDir $backup -Force
    Write-Host "Backed up to: $backup"
}

# 克隆仓库
Write-Host "Cloning repository..." -ForegroundColor Green
git clone $GitUrl $InstallDir
if ($LASTEXITCODE -ne 0) {
    Write-Host "Git clone failed. Make sure git is installed and you have network access." -ForegroundColor Red
    exit 1
}

# 安装 Python 依赖
Write-Host "Installing Python dependencies..." -ForegroundColor Green
Push-Location $InstallDir
try {
    # 检查 python
    $pyVer = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found. Please install Python 3.10+ and add to PATH."
    }
    Write-Host "Found Python: $pyVer"

    # 升级 pip
    python -m pip install --upgrade pip
    # 安装依赖
    pip install -r requirements.txt
    Write-Host "Dependencies installed." -ForegroundColor Green
}
catch {
    Write-Host "Failed to install dependencies: $_" -ForegroundColor Red
    Pop-Location
    exit 1
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "✅ Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Ensure RUNNINGHUB_API_KEY environment variable is set"
Write-Host "   PowerShell: `$env:RUNNINGHUB_API_KEY='your_key'"
Write-Host "2. Go to: $InstallDir"
Write-Host "3. Dry run: python scripts/light_transfer_cli.py --dry-run"
Write-Host "4. Run: python scripts/light_transfer_cli.py"
Write-Host "5. Optional log: python scripts/light_transfer_cli.py 2>&1 | Tee-Object -FilePath 'F:\光线迁移\run.log'"
Write-Host ""
Write-Host "For documentation, see README.md or README_HUANGSHI.md in the installed directory."
Write-Host ""

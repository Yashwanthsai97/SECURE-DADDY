param(
    [switch]$RunApp
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPath = Join-Path $projectRoot ".venv"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"
$pipExe = Join-Path $venvPath "Scripts\pip.exe"
$envPath = Join-Path $projectRoot ".env"
$envExamplePath = Join-Path $projectRoot ".env.example"

Write-Host ""
Write-Host "SecureDaddy setup starting..." -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python is not installed or not available in PATH. Install Python 3 first."
}

if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor DarkYellow
}

Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
& $pythonExe -m pip install --upgrade pip
& $pipExe install -r (Join-Path $projectRoot "requirements.txt")

if (-not (Test-Path $envPath)) {
    Write-Host ""
    Write-Host "No .env file found. Let's create one." -ForegroundColor Yellow

    $defaultHost = "localhost"
    $defaultPort = "3306"
    $defaultUser = "root"
    $defaultDatabase = "secure_daddy"
    $defaultServiceName = "MySQL80"

    $mysqlHost = Read-Host "MySQL host [$defaultHost]"
    if ([string]::IsNullOrWhiteSpace($mysqlHost)) { $mysqlHost = $defaultHost }

    $mysqlPort = Read-Host "MySQL port [$defaultPort]"
    if ([string]::IsNullOrWhiteSpace($mysqlPort)) { $mysqlPort = $defaultPort }

    $mysqlUser = Read-Host "MySQL username [$defaultUser]"
    if ([string]::IsNullOrWhiteSpace($mysqlUser)) { $mysqlUser = $defaultUser }

    $mysqlPassword = Read-Host "MySQL password"
    $mysqlDatabase = Read-Host "MySQL database [$defaultDatabase]"
    if ([string]::IsNullOrWhiteSpace($mysqlDatabase)) { $mysqlDatabase = $defaultDatabase }

    $autoStartAnswer = Read-Host "Auto-start local MySQL Windows service when app runs? (Y/n)"
    $autoStartService = if ($autoStartAnswer -match '^(n|no)$') { "false" } else { "true" }

    $mysqlServiceName = $defaultServiceName
    if ($autoStartService -eq "true") {
        $serviceInput = Read-Host "Windows MySQL service name [$defaultServiceName]"
        if (-not [string]::IsNullOrWhiteSpace($serviceInput)) {
            $mysqlServiceName = $serviceInput
        }
    }

    @(
        "MYSQL_HOST=$mysqlHost"
        "MYSQL_PORT=$mysqlPort"
        "MYSQL_USER=$mysqlUser"
        "MYSQL_PASSWORD=$mysqlPassword"
        "MYSQL_DATABASE=$mysqlDatabase"
        "MYSQL_AUTO_START_SERVICE=$autoStartService"
        "MYSQL_WINDOWS_SERVICE_NAME=$mysqlServiceName"
    ) | Set-Content -Path $envPath -Encoding UTF8

    Write-Host ".env created." -ForegroundColor Green
} else {
    Write-Host ".env already exists. Leaving it unchanged." -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Start the app with:" -ForegroundColor Cyan
Write-Host "  .\.venv\Scripts\python.exe app.py"

if ($RunApp) {
    Write-Host ""
    Write-Host "Starting SecureDaddy..." -ForegroundColor Cyan
    Push-Location $projectRoot
    try {
        & $pythonExe (Join-Path $projectRoot "app.py")
    } finally {
        Pop-Location
    }
}

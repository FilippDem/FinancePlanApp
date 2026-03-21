# =====================================================
# Deploy Financial Planning Suite to TerraMaster NAS
# Run from PowerShell: .\deploy.ps1
# =====================================================

$NAS_IP = "192.168.68.102"
$NAS_USER = "Gonzik"
$NAS_SSH_PORT = "9222"
$NAS_APP_DIR = "/Volume1/docker/financial-planner"
$SMB_TRANSFER = "\\$NAS_IP\Gonzik\Transfer"

Write-Host ""
Write-Host "=== Deploying Financial Planning Suite to NAS ===" -ForegroundColor Cyan
Write-Host ""

# Copy files via SMB share
$files = @("FinancialApp_V14.py", "Dockerfile", "docker-compose.yml", "docker-compose-local.yml", "requirements.txt", "streamlit_config.toml")

Write-Host "Copying files to NAS via SMB..."
foreach ($f in $files) {
    if (Test-Path $f) {
        Copy-Item $f "$SMB_TRANSFER\$f" -Force
        Write-Host "  -> $f" -ForegroundColor Green
    } else {
        Write-Host "  MISSING: $f" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Files copied to SMB. Now run these commands in SSH:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  ssh -p $NAS_SSH_PORT $NAS_USER@$NAS_IP" -ForegroundColor White
Write-Host ""
Write-Host "Then type:" -ForegroundColor Yellow
Write-Host "  cd $NAS_APP_DIR" -ForegroundColor White
Write-Host "  cp ~/Transfer/* ." -ForegroundColor White
Write-Host "  docker-compose -f docker-compose-local.yml build --no-cache" -ForegroundColor White
Write-Host "  docker-compose -f docker-compose-local.yml up -d" -ForegroundColor White
Write-Host ""

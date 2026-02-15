# ============================================================================
# DLT Framework - Environment Variable Secret Setup
# ============================================================================
# This script sets environment variables instead of storing secrets in files
# More secure than secrets.toml, but less robust than Azure Key Vault
# ============================================================================

Write-Host "Setting up DLT Framework Secrets as Environment Variables..." -ForegroundColor Cyan

# PostgreSQL
[System.Environment]::SetEnvironmentVariable('DLT_POSTGRESQL_HOST', 'localhost', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_POSTGRESQL_PORT', '5432', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_POSTGRESQL_DATABASE', 'poc_db', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_POSTGRESQL_USERNAME', 'poc_user', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_POSTGRESQL_PASSWORD', 'poc_pwd', 'User')

# Oracle
[System.Environment]::SetEnvironmentVariable('DLT_ORACLE_HOST', 'localhost', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_ORACLE_PORT', '1521', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_ORACLE_SID', 'XE', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_ORACLE_USERNAME', 'system', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_ORACLE_PASSWORD', 'YourPassword123', 'User')

# MSSQL
[System.Environment]::SetEnvironmentVariable('DLT_MSSQL_HOST', 'localhost', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_MSSQL_PORT', '1433', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_MSSQL_DATABASE', 'master', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_MSSQL_USERNAME', 'sa', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_MSSQL_PASSWORD', 'StrongPassword!123', 'User')

# Azure SQL
[System.Environment]::SetEnvironmentVariable('DLT_AZURE_SQL_HOST', 'testsqlserver123.database.windows.net', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_AZURE_SQL_PORT', '1433', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_AZURE_SQL_DATABASE', 'TestDatabase', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_AZURE_SQL_USERNAME', 'azureadmin', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_AZURE_SQL_PASSWORD', 'YOUR_PASSWORD', 'User')

# ADLS Gen2
[System.Environment]::SetEnvironmentVariable('DLT_ADLS_STORAGE_ACCOUNT', 'dltpoctest', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_ADLS_STORAGE_KEY', 'Bybm0f9Upxmlhvb9vBDS2s9K2xnQl8nXHZbtQzQ4pKKkqAq7s34QLa0rgeYuM+kHmKREapRfm12E+AStAaWF+w==', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_ADLS_BUCKET_URL', 'az://raw-data', 'User')

# CoinGecko API
[System.Environment]::SetEnvironmentVariable('DLT_COINGECKO_BASE_URL', 'https://api.coingecko.com/api/v3', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_COINGECKO_API_KEY', 'CG-YourAPIKeyHere', 'User')

Write-Host "`n✅ Environment variables set successfully!" -ForegroundColor Green
Write-Host "`n⚠️  IMPORTANT: Close and reopen your terminal for changes to take effect" -ForegroundColor Yellow
Write-Host "`nTo verify, run:" -ForegroundColor Cyan
Write-Host "  `$env:DLT_POSTGRESQL_HOST" -ForegroundColor White

Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Update src/config/loader.py to read from environment variables" -ForegroundColor White
Write-Host "  2. Rename .dlt/secrets.toml to .dlt/secrets.toml.backup" -ForegroundColor White
Write-Host "  3. Test with: python run.py" -ForegroundColor White

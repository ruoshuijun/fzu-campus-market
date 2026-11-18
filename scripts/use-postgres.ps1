# 在项目根目录用点源加载：. .\scripts\use-postgres.ps1
$env:DB_ENGINE = 'postgres'
$env:POSTGRES_DB = 'fzu_market'
$env:POSTGRES_USER = 'fzu'
if (-not $env:POSTGRES_PASSWORD) { $env:POSTGRES_PASSWORD = 'local-demo-password' }
$env:POSTGRES_HOST = '127.0.0.1'
$env:POSTGRES_PORT = '5432'
Write-Output '当前终端已切换 PostgreSQL。切回 SQLite：Remove-Item Env:DB_ENGINE'

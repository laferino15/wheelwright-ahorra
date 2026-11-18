$ErrorActionPreference = 'Stop'
$python = 'C:/Users/LaferinoX/Desktop/odoo19-local/odoo/.venv/Scripts/python.exe'
$odoo = 'C:/Users/LaferinoX/Desktop/odoo19-local/odoo/odoo-bin'
$config = 'C:/Users/LaferinoX/Desktop/odoo19-local/wheelwright-ahorra.conf'
$existing = Get-NetTCPConnection -LocalPort 8070 -State Listen -ErrorAction SilentlyContinue
if ($existing) { Write-Output 'Odoo ya tiene abierto el puerto 8070.'; exit 0 }
Start-Process -FilePath $python -ArgumentList @($odoo,'-c',$config,'-d','wheelwright_ahorra_dev','--http-interface=127.0.0.1','--max-cron-threads=0','--limit-time-real=0') -WindowStyle Hidden -WorkingDirectory $PSScriptRoot -RedirectStandardOutput (Join-Path $PSScriptRoot 'odoo-estable.out.log') -RedirectStandardError (Join-Path $PSScriptRoot 'odoo-estable.err.log') -PassThru | Select-Object Id

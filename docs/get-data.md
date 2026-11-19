# Getting the 1-minute data (run on your PC)

Dukascopy refuses downloads from the cloud server, so this runs on your Windows PC.
**Not tested yet**: I could not run the downloader from the cloud. If any step fails, send me the exact error text.

## Once only: install Node.js
Download the "LTS" installer from nodejs.org and install with default options. Close and reopen PowerShell.

## Download (PowerShell)
First go to a normal folder, not C:\Windows\system32:
```powershell
cd $HOME\Documents
mkdir crt-data
cd crt-data
```
If PowerShell says "running scripts is disabled", that is why the commands below use `npx.cmd` instead of `npx`.

```powershell
npx.cmd dukascopy-node -i gbpusd -from 2021-11-01 -to 2026-11-19 -t m1 -f csv -v -dir .\raw
```
```powershell
npx.cmd dukascopy-node -i xauusd -from 2021-11-01 -to 2026-11-19 -t m1 -f csv -v -dir .\raw
```
Each takes a while (five years of minutes, about 1.8 million rows per symbol). Prices are Dukascopy **bid** prices, spot.

## Check the files
```powershell
python scripts\check_data.py raw
```
Send me the printed report, or upload the two CSV files and I'll run it.

## What the check looks for
Date range, duplicate times, rows where high/low don't contain open/close, gaps of more than 30 minutes on weekdays (holidays and outages), and how many H1/H4/D1 candles are missing minutes.

@echo off
cd /d "%~dp0"
py -3 -m pip install -r requirements.txt
start "" pyw -3 odyssey_nodes.pyw

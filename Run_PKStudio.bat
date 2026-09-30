@echo off
rem Start PK Studio with the Python that has CUDA (3.12); fall back to the default Python.
cd /d "%~dp0"
py -3.12 PKStudio.py || py PKStudio.py
pause

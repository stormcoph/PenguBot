@echo off
start cmd /k "cd /d %~dp0 && .venv\Scripts\activate && python -m gui.GUI"
@echo off

cd %~dp0
set virtualenv_dir=venv_windows

IF NOT EXIST %virtualenv_dir% (
		Rem create virtualenv if not exists
		echo %virtualenv_dir% not found at %cd%. creating it ...
		virtualenv %virtualenv_dir%
		"%virtualenv_dir%\Scripts\pip" install pipenv
		echo "virtualenv created. installing requirments."
		"%virtualenv_dir%/Scripts/activate" find_proxy.py
		pipenv install --python="%virtualenv_dir%/Scripts/python.exe"
)

"%virtualenv_dir%/Scripts/python" find_proxy.py

#!/bin/bash

cd `dirname $0`
virtualenv_dir="venv_linux"
if [ ! -d "${virtualenv_dir}" ];
then
	# create virtualenv if not exists
	echo "${virtualenv_dir} not found at $(pwd). creating it ..."
	virtualenv "${virtualenv_dir}";
	ls "${virtualenv_dir}/bin/activate";
	echo "virtualenv created. installing requirments."
	"${virtualenv_dir}/bin/pip" install -r requirements.txt
fi
venv_linux/bin/python find_proxy.py

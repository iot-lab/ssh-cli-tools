Installing ssh-cli-tools
========================

You may install on:
- your dev PC, or
- an iotlab ssh frontend


Installing on an iotlab ssh frontend
------------------------------------

we recommend using a virtualenv

	virtualenv xx
	. xx/bin/activate
	git clone git@github.com:iot-lab/ssh-cli-tools.git
	cd ssh-cli-tools/
	pip install pip --upgrade
	pip install .
	open-a8-cli


Installing on your dev PC
-------------------------

we recommend using a virtual environment

you will need pip (version 9.0.1+ known to work)
you will need python-dev and libssh2.1-dev

	sudo apt-get-install virtualenvwrapper
	sudo apt-get install pip
	sudo apt-get install python-dev libssh2.1-dev


	mkvirtualenv xx
	git clone git@github.com:iot-lab/ssh-cli-tools.git
	cd ssh-cli-tools/
	pip install .
	open-a8-cli


Installing / upgrading pip / pip3
---------------------------------

When using virtualenvs, pip comes pre-installed
and you only need to check version and upgrade if needed.

For system-wide pip installs, proceed as follows:
```
$ sudo apt-get install python-pip (or python3-pip)
$ sudo pip install pip --upgrade
$ sudo pip3 install pip --upgrade (Python 3 case)
$ pip --version
pip 9.0.1 from /usr/local/lib/python2.7/dist-packages (python 2.7)
```

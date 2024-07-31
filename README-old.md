Overview
========
SDX API

Kytos Napp to handle the requirements of the AtlanticWave-SDX project.

Requirements
============

* kytos/core
* kytos/topology
* openAPI Specification
* flask
* python 3.9

Preparing the environment:
==========================

Please make sure you're using Debian

lsb_release -a


``Installing Python``

``Please make sure that you're using python3.9``

sudo rm -rf /var/lib/apt/lists/*; sudo apt-get purge -y --auto-remove; sudo apt-get autoremove; sudo apt-get clean;
sudo rm -rf /etc/apt/sources.list.d/*

sudo apt update && sudo apt upgrade

sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libsqlite3-dev libreadline-dev libffi-dev curl libbz2-dev -y

wget https://www.python.org/ftp/python/3.9.17/Python-3.9.17.tar.xz

sudo mv Python-3.9.17 /usr/local/share/python3.9

cd /usr/local/share/python3.9

./configure --enable-optimizations --enable-shared

make

make -j 5

sudo make altinstall

sudo ldconfig /usr/local/share/python3.9

sudo ln -s /usr/local/bin/python3.9 python3.9

sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 2

pip3.9 install --upgrade pip

pip3 install pytest==7.2.1

pip3 install pytest-cov==4.0.0

pip3 install black==23.3.0

pip3 install isort==5.12.0

pip3 install pylint==2.15.0

pip3 install pycodestyle==2.10.0

pip3 install yala==3.2.0

pip3 install tox==3.28.0

pip3 install typing-extensions==4.7.1

mkdir ~/.vim/bundle

cd ~/.vim/bundle

git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim

git clone https://github.com/dense-analysis/ale.git


Installation 
==========================

* For the whole installation process and requirements, please access the AtlanticWave SDX repo in Github: https://github.com/atlanticwave-sdx

* The KytoS SDX Topology Napp is pivotal in the Atlantic Wave SDX system, serving as a cornerstone of the system's architecture. Its functionality and contributions are integral to the system's successful operation. 

* It's important to note that this repository functions as a submodule of the principal repository located at https://github.com/atlanticwave-sdx/sdx-continuous-development. 

* The KytoS SDX Topology Napp is installed within the principal repository as part of the seamless integration process. This interconnected setup allows for a cohesive deployment of the entire system, ensuring that the features and capabilities of the Napp are harnessed effectively within the broader context of the Atlantic Wave SDX system. 

* By maintaining this modular structure and close integration, we can harness the full potential of the KytoS SDX Topology Napp while contributing to the overall robustness and functionality of the Atlantic Wave SDX system. 


# Test

* Install python dependecies requirements

# Asynchronous Lint Engine

* ALE (Asynchronous Lint Engine) is a plugin providing linting (syntax checking and semantic errors)

* Installation in VIM with Vundle

cd ~/.vim/bundle

Set up Vundle:

git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim

git clone https://github.com/dense-analysis/ale.git

* Edit ~/.vimrc

set rtp+=~/.vim/bundle/Vundle.vim

let path='~/.vim/bundle/Vundle.vim'

call vundle#begin()

Plugin 'VundleVim/Vundle.vim'

Plugin 'dense-analysis/ale'

call vundle#end()            " required

filetype plugin indent on    " required

let g:ale_linters = {
        \   'python': ['flake8', 'pylint', 'pycodestyle'],
        \}


``To Activate ALE, run this command inside vim``

:PlugInstall

:source ~/.vimrc

:PluginInstall

# Black

black --check --diff main.py

black main.py
black --line-length 80 main.py

# Isort

isort main.py

# Bandit

bandit --configfile bandit.yaml

* with the following bandit.yaml in the project's root directory

assert_used:
  skips: ['*_test.py', 'test_*.py']


# How to update dependencies versions

* Edit requirements.in/dev.txt if needed.

* Run pip-compile again, exactly as before:

$ <venv>/bin/pip-compile dev.in

# Pytest

python3 -m pytest --cov=app --cov-report=html

# Partial test

pytest -v -k "test_sdx_topology"

# Unit test

pytest tests/unit/test_main.py

pytest --cov app --cov-branch --cov-report term-missing

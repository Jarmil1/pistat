virtualenv -p python3 venv

source ./venv/bin/activate

pip install matplotlib
pip install mysql-connector-python

# dependency: must be installed outside venv, i guess
#sudo apt-get install python3-tk


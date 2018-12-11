virtualenv -p python3 venv

source ./venv/bin/activate

pip install matplotlib
pip install mysql-connector-python
pip install gmplot

# dependency: must be installed outside venv, i guess
#sudo apt-get install python3-tk


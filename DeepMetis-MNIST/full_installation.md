# Test Input Generator for MNIST - Detailed Installation Guide #

## General Information ##
This folder contains the application of the DeepMetis approach to the handwritten digit classification problem.
This tool is developed in Python on top of the DEAP evolutionary computation framework. It has been tested on a machine featuring an i7 processor, 16 GB of RAM, an Nvidia GeForce 940MX GPU with 2GB of memory. These instructions are for Ubuntu 18.04 (bionic) OS and python 3.6.

## Dependencies ##

### Configure Ubuntu ###

DeepMetis-MNIST works on Ubuntu 18.04 (bionic) machines. We suggest to use a fresh Ubuntu machine, since other packages installed on it may interfere with the installation.

However, if you do not have a fresh Ubuntu machine, you can use a virtual machine or docker container. We strongly suggest to pull an Ubuntu Docker image, run and configure it by typing in the terminal:

``` 
docker pull ubuntu:bionic
docker run -it --rm ubuntu:bionic
apt update && apt-get update
apt-get install -y software-properties-common
```


### Installing Python 3.6 ###
Install Python 3.6
``` 
add-apt-repository ppa:deadsnakes/ppa
apt update
apt install -y python3.6
```

And check if it is correctly installed, by typing the following command:

``` 
$ python3
```

You should have a message that tells you are using python 3.6.*, similar to the following:

``` 
Python 3.6.9 (default, Apr 18 2020, 01:56:04) 
[GCC 8.4.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
```

Exit from python.

### Installing pip ###
Use the following commands to install pip and upgrade it to the latest version:
``` 
apt install -y python3-pip
python3 -m pip install --upgrade pip
```

Once the installation is complete, verify the installation by checking the pip version:

``` 
python3 -m pip --version
```

### Installing git ###
Use the following command to install git
``` 
apt install -y git
```

To check the correct installation of git, insert the command `git` in the terminal. If git is correctly installed, the usage information will be shown.

### Cloning this repo ###
Use the following command to clone the repository
``` 
git clone https://github.com/testingautomated-usi/deepmetis.git
```

### Creating a Python virtual environment ###

Install the `venv` module in the docker container:

``` 
apt install -y python3-venv
```

Create the python virtual environment:

```
cd /DeepMetis-MNIST
python3 -m venv .venv
```

Activate the python virtual environment and updated `pip` again (venv comes with an old version of the tool):

```
. .venv/bin/activate
pip install --upgrade pip
```


### Installing Python Binding to the Potrace library ###
Instructions provided by https://github.com/flupke/pypotrace.

Install system dependencies in your environment (it is not needed to install them in the DeepMetis-MNIST folder):

``` 
apt-get install build-essential python-dev libagg-dev libpotrace-dev pkg-config 
```

Install pypotrace (commit `76c76be2458eb2b56fcbd3bec79b1b4077e35d9e`):

```
git clone https://github.com/flupke/pypotrace.git
cd pypotrace
git checkout 76c76be2458eb2b56fcbd3bec79b1b4077e35d9e
pip install numpy
pip install .
cd ..
```

If the following command does not crash, pypotrace is correctly installed:

``` 
python
>>> import potrace
>>>
```

### Installing PyCairo and PyGObject ###
Instructions provided by https://pygobject.readthedocs.io/en/latest/getting_started.html#ubuntu-getting-started.

Open a terminal and execute 

```apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0```

And

```apt-get install libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev gir1.2-gtk-3.0 librsvg2-dev```

### Installing Other Dependencies ###

This tool has other dependencies such as tensorflow and deap.

To easily install the dependencies with pip, we suggest to go in the folder where you extracted DeepMetis-MNIST and then run the command:

```pip install -r requirements.txt```

Otherwise, you can manually install each required library listed in the requirements.txt file using pip.

## Usage ##

### Input ###

* One or more original DL models in h5 format. The default one is in the folder `original_model`;
* One or more mutant DL models in h5 format. The default ones are in the folder `mutant_model`;
* A list of seeds used for the input generation. The default list is in the folder `original_dataset`;
* `config.py` containing the configuration of the tool selected by the user.


### Run the Tool ###

> NOTE: Before starting a run, ensure that you deleted or removed the folder named `results` in the DeepMetis-MNIST main folder

Run the command:
`python main.py`

### Output ###

When the run ends, on the console you should see a message like the following:

```
Final solution N is: X
GAME OVER

Process finished with exit code 0
```

where X is the number of generated mutant-killing inputs.

Moreover, DeepMetis will create a folder `results` which contains: 
* the archive of solutions (`archive` folder); 
* the final report (`report_final.json`);
* the configuration's description (`config.json`).

### Troubleshooting ###

* If tensorflow cannot be installed successfully, try to upgrade the pip version. Tensorflow cannot be installed by old versions of pip. We recommend the pip version 20.1.1.
* If the import of cairo, potrace or other modules fails, check that the correct version is installed. The correct version is reported in the file requirements.txt. The version of a module can be checked with the following command:
```
$ pip show modulename | grep Version
```
To fix the problem and install a specific version, use the following command:
```
$ pip install 'modulename==moduleversion' --force-reinstall
```

* If the command `pip install -r requirements.txt` fails to find the requirements.txt file, please ensure that you are calling it from inside the DeepMetis-MNIST folder.

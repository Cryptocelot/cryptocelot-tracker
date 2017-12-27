# cryptocelot-tracker
Cryptocurrency order tracker and analysis tool

## Installation

### Dependencies
* Python 3 (https://www.python.org/downloads/)
* (Mac OS only) Homebrew (https://brew.sh/)

You may want to install the Python dependencies in a virtual environment (depending on your OS, you may have to). To accomplish this:

    # in the root of this repository
    python -m venv venv
    source venv/bin/activate

Ensure that the `python` and `pip` commands point to the Python 3 versions (check by running `python --version` or `pip --version`). If not, change `python` to `python3` and `pip` to `pip3` in the instructions below.

### Linux
    pip install --upgrade pip wheel setuptools
    pip install 'Cython===0.26.1'
    pip install python-dateutil
    pip install sqlalchemy
    # replace apt-get install with your package manager's install command if not using apt-get
    sudo apt-get install python3-dev libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
    pip install kivy
    pip install https://github.com/cryptocelot/python-bittrex/tarball/master

### Mac OS X
    pip install --upgrade pip wheel setuptools
    pip install 'Cython===0.26.1'
    pip install python-dateutil
    pip install sqlalchemy
    brew install pkg-config sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer
    pip install https://github.com/kivy/kivy/archive/master.zip
    pip install https://github.com/cryptocelot/python-bittrex/tarball/master

### Windows
    pip install --upgrade pip wheel setuptools
    pip install 'Cython===0.26.1'
    pip install python-dateutil
    pip install sqlalchemy
    pip install docutils pygments pypiwin32 kivy.deps.sdl2 kivy.deps.glew
    pip install --upgrade kivy.deps.sdl2
    pip install kivy
    pip install https://github.com/cryptocelot/python-bittrex/tarball/master

## Usage
    python tracker.py

Upon first launch, a `tracker.db` database file will be created in the same directory. Delete this file to clear all program data.

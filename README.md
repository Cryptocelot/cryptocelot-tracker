# cryptocelot-tracker
Cryptocurrency order tracker and analysis tool

## Features

* Automatic detection and processing of order history CSV files downloaded from exchanges
* Hassle-free order retrieval directly from exchanges using API keys
* Duplicate record prevention on import/refresh
* Automatic position creation from exchange and currency pair
* Automatic position closing (optional)
* Break-even price calculation
* Profit/loss calculation per position

## Installation

### Dependencies
* Git (if cloning repository) (https://git-scm.com/downloads)
* Python 3 (https://www.python.org/downloads/)
* (Mac OS only) Homebrew (https://brew.sh/)

### Downloading
In a terminal, navigate to your desired installation directory and clone the repository.

    cd my-folder
    git clone https://github.com/Cryptocelot/cryptocelot-tracker.git

Alternatively, you can download the ZIP from GitHub and unzip it in your desired installation directory.

You may want to install the Python dependencies in a virtual environment (depending on your OS, you may have to). To accomplish this in Linux and Mac OS X:

    cd cryptocelot-tracker
    python -m venv venv
    source venv/bin/activate

If using a virtual environment, run all `pip install` commands after running the activate command above and without closing the terminal window.

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

### Launching
    python tracker.py

Upon first launch, a `tracker.db` database file will be created in the same directory. Delete this file to clear all program data.

### Layout
The main window has a left panel with buttons to import a CSV file downloaded from a supported exchange or retrieve order history from an exchange directly using the API. In this development version, there are refresh buttons for Bittrex and Gemini. These may be replaced by a menu in later versions to support more exchanges.

The main panel has tabs to view all orders, open positions, and closed positions.

### Working with Positions
After orders have been entered into the application either through an exchange API or from a CSV file, open positions will be created based on unique combinations of exchange, currency, and base currency. For example, all orders in Bittrex BTC/ETH will be shown in a single open position. Each item in the Open Positions list will show the exchange, currency pair, net currency, net base currency, and the buy/sell price needed to avoid a loss.

A position can be fully or partially closed by clicking it on the Open Positions tab, selecting orders to put in the closed position, and clicking the New Closed Position button. You can do this whenever you want to finish with a group of orders and calculate the total profit on the position. If all orders in the position are selected, the entire position will be closed and moved to the Closed Positions tab. If not all orders are selected, the selected orders will be used to create a new closed position and the unselected orders will remain in the open position. The percent profit on a closed position is calculated by comparing the sum of the base currency spent and the sum of the base currency received.

### Automatic Position Closing
The application will detect sequences of orders that may be useful to calculate profit on and it will offer to close positions using these orders. In particular, a sequence of orders that results in a net currency of zero will be detected. For example, if you bought 1.0 LTC at some price and later sold 1.0 LTC at a higher price, you would have a net difference of 0 LTC and some profit in the base currency. This would be detected and an offer to close the position will be displayed.

### Using the Refresh Feature
To use the order refresh functionality, generate an API key on your exchange and restrict its permissions to those which allow only read access to orders and balances. Follow the example in keys.py to add your API key and secret. Currently, only Bittrex and Gemini are supported.

## Development

### Running Tests

    # first time
    pip install pytest pytest-cov
    # before running tests in a new terminal
    export PYTHONPATH=.

    py.test tests --cov=. --cov-report term-missing

# Binance Futures Bot

A simple bot that trades futures on binance.

## Installation

### Requirements

Mini conda virtual environment is preferred for smooth installation of TA lib.
```
pip install -r requirements.txt
```

followed by the installation of TA lib which needs to be installed via 

```
conda install -c conda-forge ta-lib
```

## Setup

The bot can be modified for use with any USDT futures market, leverage and time frame combinatiob by editing the settings.json file. 

### Settings.json

You should replace the market, leverage and period with values that are relevant.

```
{
   "market": "BTCUSDT",
   "leverage": "2",
   "trading_periods": "15m",
   "margin_type": "ISOLATED",
   "take_profit": "0.3",
   "stop_loss": "5",
   "api_url": "https://fapi.binance.com/"
}
```

### Keys.json

This file is where you should put your API keys. The API Keys should have Futures access enabled, or the bot won't work. [You can generate a new api key here when logged in to binance](https://www.binance.com/en/my/settings/api-management)

```
{
	"api_key": "fill_api_key_here",
	"api_secret": "fill_api_secret_here"
}
```


## Usage

Once you've modified Keys.json and Settings.json you should be ready to go.

### Running locally

```
python binance_bot\bot.py
```

### Running on a linux server/cloud insance

```
nohup python binance_bot\bot.py &
```
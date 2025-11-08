# OBV Study

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)

A study for trading strategies based on the **On-Balance Volume (OBV)** indicator. This project detects accumulation and distribution patterns in stock data and evaluates trading performance using multiple strategies. We focus on buying just on accumulation points, as distribution could be a arbitrary buy or liquidity needs, while accumulation could be understood as a big player staking on that ticker.

## Project Overview

This tool analyzes stock price movements and volume data to identify potential trading opportunities using the OBV indicator. It implements two backtesting strategies:

1. **Holding Period Strategy**: Buy on accumulation signals and hold for a fixed number of days
2. **Stop-Loss/Take-Profit Strategy**: Exit positions when reaching predefined profit targets or stop-loss levels

## Features

- **Automatic data download** from Yahoo Finance
- **OBV-based accumulation/distribution detection**
- **Interactive visualizations** with Plotly
- **Two backtesting strategies** with customizable parameters
- **Command-line interface** for easy execution
- **Detailed logging** for debugging and analysis

## Quick Start

### Installation

#### 1. Clone repo
```bash
git clone https://github.com/Sarjseg/obv-study.git
cd obv-study
```

##### 2. Create virtual env and install dependencies
**Windows:**
Run prepare_env.bat
**Linux:**
Run prepare_env.sh

### Basic Usage with CLI

Run activate_env.bat or prepare_env.sh depending on os to open terminal with environment activated, then

```bash
# Analyze a stock with default parameters
python main_cli.py AAPL

# Custom analysis
python main_cli.py MSFT --period 2y --hold-period 10

# Run only holding strategy
python main_cli.py TSLA --strategy holding

# Run only stop-loss strategy  
python main_cli.py GOOGL --strategy sl --profit-target 0.08 --stop-loss 0.04

# Run custom analysis with no plot
python main_cli.py AAPL--period 2y --hold-period 45 --no-plot
```

## Configuration

Edit `config.py` to customize default parameters. Some of them are:

```python
# Data download settings
DEFAULT_PERIOD = "1y"
DOWNLOAD_PROGRESS = False

# OBV settings 
DEFAULT_WINDOW_SIZE = 20
VOLUME_THRESHOLD_MULTIPLIER = 2.0 

# Strategy parameters
HOLDING_STRATEGY = {
    "default_hold_period": 20
}

SL_TP_STRATEGY = {
    "default_profit_target": 0.12,  
    "default_stop_loss": 0.08       
}
```

## Python Usage

```python
from src.obva import StockAnalyzerOBV

# Initialize analyzer
analyzer = StockAnalyzerOBV("AAPL")

# Download data and detect signals
analyzer.detect_acc(period="1y", window_size=20)

# Generate visualizations
analyzer.plot_data(dist_show=False, save_html=True)

# Run backtesting strategies
analyzer.calc_pnl_holding(hold_period=21, save_result=True)
analyzer.calc_pnl_sl(profit_target=0.15, stop_loss=0.05, save_result=True)

# Display summaries
analyzer.summary_holding()
analyzer.summary_sl()
```

## Understanding OBV, Accumulation and Distribution

**On-Balance Volume (OBV)** is a momentum indicator that uses volume flow to predict changes in stock price:

- **OBV increases**  → Bullish signal
- **OBV decreases**  → Bearish signal

### Accumulation Signal
Detected when:
- Price is rising
- Volume is above 2x average
- OBV is increasing

### Distribution Signal  
Detected when:
- Price is falling
- Volume is above 2x average
- OBV is not increasing

## CLI Options

```bash
python main.py TICKER [options]

Required:
  TICKER                Stock ticker symbol

Optional:
  -p, --period         Time period (1d, 1mo, 1y, 2y, etc.) [default: 1y]
  -w, --window         Window size for rolling mean [default: 20]
  -s, --strategy       Strategy to run: holding, sl, both [default: both]
  --hold-period        Days to hold position [default: 20]
  --profit-target      Profit target as decimal [default: 0.12]
  --stop-loss          Stop loss as decimal [default: 0.08]
  --buy-on-detection   Buy on detection day (default: False)
  --no-plot            Skip generating plots
  --no-save            Don't save results to files
```

## Disclaimer

This tool is for **educational and research purposes only**. It is not financial advice. Always do your own research and consult with financial professionals before making investment decisions. Past performance does not guarantee future results.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Sergi Arjo**
- GitHub: https://github.com/Sarjseg
- LinkedIn: https://www.linkedin.com/in/sergi-arjo-segovia-b01267208/

## Contact

If you have questions or suggestions, feel free to:
- Open an issue on GitHub
- Connect on LinkedIn

---

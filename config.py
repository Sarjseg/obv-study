"""
Configuration file for OBV Trading Strategy
Contains all configurable parameters for the backtesting system
"""

from pathlib import Path
import os

# paths
BASE_DIR = Path(__file__).parent
RESULTS_DIR = os.path.join(BASE_DIR, "results")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# if directories does not exists, create them
Path(RESULTS_DIR).mkdir(exist_ok=True)
Path(LOGS_DIR).mkdir(exist_ok=True)

# yfinance download settings
DEFAULT_PERIOD = "1y"  
AUTO_ADJUST = True
MULTI_LEVEL_INDEX = False
DOWNLOAD_PROGRESS = False

# obv settings 
DEFAULT_WINDOW_SIZE = 20  # Rolling mean window for volume
VOLUME_THRESHOLD_MULTIPLIER = 2.0  # Volume must be > 2x average to be significant

# backtesting strategies
BUY_ON_DETECTION_DAY = False # False = buy next day

# strategy 1: holding
HOLDING_STRATEGY = {
    "default_hold_period": 30,  # 30 trading days as 6 weeks
}

# Strategy 2: Stop Loss / Take Profit
SL_TP_STRATEGY = {
    "default_profit_target": 0.12, 
    "default_stop_loss": 0.08,      
}


# plot settings
PLOT_CONFIG = {
    "height": 600,
    "show_accumulation": True,
    "show_distribution": False,
    "save_html": True,
    "default_filename": "obv_analysis_{ticker}.html",
    "color_scheme": {
        "price": "blue",
        "accumulation": "green",
        "distribution": "red",
        "volume": "gray",
        "obv": "orange"
    }
}

# logging settings
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "standard",
            "filename": os.path.join(LOGS_DIR, "obv_analyzer.log"),
            "mode": "a"
        }
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": True
        }
    }
}

# validation
def validate_config() -> bool:
    """Validate configuration parameters"""
    errors = []
    
    if VOLUME_THRESHOLD_MULTIPLIER <= 0:
        errors.append("VOLUME_THRESHOLD_MULTIPLIER must be positive")
    
    if DEFAULT_WINDOW_SIZE <= 0:
        errors.append("DEFAULT_WINDOW_SIZE must be positive")
    
    if not (0 <= SL_TP_STRATEGY["default_profit_target"] <= 1):
        errors.append("default_profit_target must be between 0 and 1")
    
    if not (0 <= SL_TP_STRATEGY["default_stop_loss"] <= 1):
        errors.append("default_stop_loss must be between 0 and 1")
    
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True

# validate on import
if not validate_config():
    raise ValueError("Invalid configuration. Please check config.py")
"""
Simple script to run OBV Study
"""

import sys
# # Add src to path in case it is not in main folder
# from pathlib import Path
# sys.path.append(str(Path(__file__).parent))

from src.obva import StockAnalyzerOBV
from src.utils import setup_logging
from config import (
    LOGGING_CONFIG, DEFAULT_PERIOD, DEFAULT_WINDOW_SIZE,
    HOLDING_STRATEGY, SL_TP_STRATEGY, VOLUME_THRESHOLD_MULTIPLIER,
    BUY_ON_DETECTION_DAY
)

# ==================== PARAMETERS CONFIGURATION ====================
# Edit these parameters for your analysis
# Stock to analyze will be asked via prompt if it is left None
TICKER = None
# Data download and calculation settings
PERIOD = DEFAULT_PERIOD # Options: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'
WINDOW_SIZE = DEFAULT_WINDOW_SIZE     
VOLUME_THRESHOLD = VOLUME_THRESHOLD_MULTIPLIER 
# Strategy parameter
BUY_ON_DETECTION = BUY_ON_DETECTION_DAY  
# Strategy 1: Holding Period
RUN_HOLDING_STRATEGY = True
HOLD_PERIOD = HOLDING_STRATEGY["default_hold_period"]       
# Strategy 2: Stop Loss / Take Profit
RUN_SL_STRATEGY = True
PROFIT_TARGET = SL_TP_STRATEGY["default_profit_target"]   
STOP_LOSS =SL_TP_STRATEGY["default_stop_loss"]
# Output settings
SHOW_PLOTS = True
SAVE_RESULTS = True
# ========================================================

def get_ticker_from_user_input():
    """Function to get ticker from user"""
    ticker = input("Enter ticker value: ")
    return ticker

def main(TICKER : None | str):
    """Main execution function"""
    setup_logging(LOGGING_CONFIG)

    if TICKER is None:
        TICKER = get_ticker_from_user_input()
        if TICKER is None:
            return None
    
    print(f"OBV STUDY - {TICKER}")
    
    try:
        print(f"Initializing analyzer for {TICKER}...\n")
        analyzer = StockAnalyzerOBV(TICKER)
        
        print(f"Downloading data for {TICKER} (period: {PERIOD}, , window: {WINDOW_SIZE}))")
        analyzer.detect_acc(period=PERIOD, window_size=WINDOW_SIZE, volume_threshold_multiplier=VOLUME_THRESHOLD)
        
        if analyzer.df_data is None or analyzer.df_data.is_empty():
            print(f"No data available for {TICKER}")
            return 1
        
        print(f"Downloaded {analyzer.df_data.height} rows of data")
        print(f"Detected {analyzer.df_acc.height} accumulation signals")
        print(f"Detected {analyzer.df_dist.height} distribution signals\n")
        
        if SHOW_PLOTS:
            print("Generating plots...")
            analyzer.plot_data(save_html=SHOW_PLOTS)
            print("Plot displayed in browser\n")
        
        if RUN_HOLDING_STRATEGY:
            print(f"Running Holding strategy ({HOLD_PERIOD} days)...")
            analyzer.calc_pnl_holding(
                hold_period=HOLD_PERIOD,
                bool_detect_buy=BUY_ON_DETECTION,
                save_results=SAVE_RESULTS
            )
            analyzer.summary_holding()
            
        if RUN_SL_STRATEGY:
            print(f"Running Stop loss strategy (TP: {PROFIT_TARGET:.1%}, SL: {STOP_LOSS:.1%})...")
            analyzer.calc_pnl_sl(
                profit_target=PROFIT_TARGET,
                stop_loss=STOP_LOSS,
                bool_detect_buy=BUY_ON_DETECTION,
                save_results=SAVE_RESULTS
            )
            analyzer.summary_sl()

        print("Analysis completed successfully!")
    
    except ValueError as e:
        print(f"\n Configuration Error: {str(e)}\n")
        print("Please check your parameters at the top of this script.\n")
    
    except Exception as e:
        print(f"\n Unexpected Error: {str(e)}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main(TICKER)
    
    # to keep console open
    input("\n Press Enter to close...")
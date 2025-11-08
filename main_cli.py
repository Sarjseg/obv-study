"""
Command Line Interface for OBV Study
Usage: python main_cli.py TICKER [options]
"""

import sys
# # Add src to path in case it is not in main folder
# from pathlib import Path
# sys.path.append(str(Path(__file__).parent))

import argparse
from src.obva import StockAnalyzerOBV
from src.utils import setup_logging, get_logger
from config import (
    LOGGING_CONFIG, DEFAULT_PERIOD, DEFAULT_WINDOW_SIZE,
    HOLDING_STRATEGY, SL_TP_STRATEGY, VOLUME_THRESHOLD_MULTIPLIER,
    BUY_ON_DETECTION_DAY
)

setup_logging(LOGGING_CONFIG)
logger = get_logger(__name__)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='OBV Trading Strategy Backtester',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic analysis
  python main.py AAPL
  
  # Custom period and window
  python main.py MSFT --period 2y --window 30
  
  # Run holding strategy
  python main.py TSLA --strategy holding --hold-period 10
  
  # Run stop-loss strategy
  python main.py GOOGL --strategy sl --profit-target 0.08 --stop-loss 0.04
  
  # Run both strategies
  python main.py NVDA --strategy both --hold-period 7 --profit-target 0.06
  
  # Skip plots
  python main.py AMZN --no-plot
        """
    )
    
    # Required arguments
    parser.add_argument(
        'ticker',
        type=str,
        help='Stock ticker symbol (e.g., AAPL, MSFT, TSLA)'
    )
    
    # Data download and calc options
    parser.add_argument(
        '-p', '--period',
        type=str,
        default=DEFAULT_PERIOD,
        help=f'Time period for data (default: {DEFAULT_PERIOD}). Options: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max'
    )
    
    parser.add_argument(
        '-w', '--window',
        type=int,
        default=DEFAULT_WINDOW_SIZE,
        help=f'Window size for rolling mean (default: {DEFAULT_WINDOW_SIZE})'
    )

    parser.add_argument(
        '--volume-threshold',
        type=int,
        default=VOLUME_THRESHOLD_MULTIPLIER,
        help=f'Volume threshold multiplier for accumulation/distribution calculations (default: {VOLUME_THRESHOLD_MULTIPLIER})'
    )
    
    # Strategy selection
    parser.add_argument(
        '-s', '--strategy',
        type=str,
        choices=['holding', 'sl', 'both'],
        default='both',
        help='Backtesting strategy to run (default: both)'
    )

    # Strategy parameters
    parser.add_argument(
        '--buy-on-detection',
        type=bool,
        default=BUY_ON_DETECTION_DAY,
        help='Buy on detection day (default: buy next day)'
    )
    
    # Holding strategy parameters
    parser.add_argument(
        '--hold-period',
        type=int,
        default=HOLDING_STRATEGY["default_hold_period"],
        help=f'Number of days to hold position (default: {HOLDING_STRATEGY["default_hold_period"]})'
    )
    
    # Stop-loss strategy parameters
    parser.add_argument(
        '--profit-target',
        type=float,
        default=SL_TP_STRATEGY["default_profit_target"],
        help=f'Profit target as decimal (default: {SL_TP_STRATEGY["default_profit_target"]})'
    )
    
    parser.add_argument(
        '--stop-loss',
        type=float,
        default=SL_TP_STRATEGY["default_stop_loss"],
        help=f'Stop loss as decimal (default: {SL_TP_STRATEGY["default_stop_loss"]})'
    )
    
    # Output options
    parser.add_argument(
        '--no-plot',
        action='store_true',
        help='Skip generating plots'
    )
    
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save results to Excel files'
    )
    
    
    return parser.parse_args()


def main():
    """Main execution function"""
    args = parse_arguments()
    
    try:
        print(f"OBV STUDY - {args.ticker.upper()}")
        
        logger.info(f"Initializing analyzer for {args.ticker}")
        analyzer = StockAnalyzerOBV(args.ticker)
        
        print(f"Downloading data for {args.ticker} (period: {args.period}, , window: {args.window}))")
        analyzer.detect_acc(period=args.period, window_size=args.window, volume_threshold_multiplier=args.volume_threshold)
        
        if analyzer.df_data is None or analyzer.df_data.is_empty():
            print(f"No data available for {args.ticker}")
            logger.error(f"No data available for {args.ticker}")
            return 1
        
        print(f"Downloaded {analyzer.df_data.height} rows of data")
        print(f"Detected {analyzer.df_acc.height} accumulation signals")
        print(f"Detected {analyzer.df_dist.height} distribution signals\n")
        
        # Plot data
        if not args.no_plot:
            print("Generating plots...")
            analyzer.plot_data(save_html=not args.no_save)
            print("Plot displayed in browser\n")
            
        # Run strategies
        save_results = not args.no_save
        
        if args.strategy in ['holding', 'both']:
            print(f"Running Holding strategy ({args.hold_period} days)...")
            analyzer.calc_pnl_holding(
                hold_period=args.hold_period,
                bool_detect_buy=args.buy_on_detection,
                save_results=save_results
            )
            analyzer.summary_holding()
        
        if args.strategy in ['sl', 'both']:
            print(f"Running Stop loss strategy (TP: {args.profit_target:.1%}, SL: {args.stop_loss:.1%})...")
            analyzer.calc_pnl_sl(
                profit_target=args.profit_target,
                stop_loss=args.stop_loss,
                bool_detect_buy=args.buy_on_detection,
                save_results=save_results
            )
            analyzer.summary_sl()
            
        print("Analysis completed successfully!")
        logger.info(f"Analysis completed successfully for {args.ticker}")

        return 0
    
    except ValueError as e:
        print(f"\n Error: {str(e)}\n")
        logger.error(f"ValueError: {str(e)}")
        return 1
    
    except Exception as e:
        print(f"\n Unexpected error: {str(e)}\n")
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
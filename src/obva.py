"""
Main class and function to make the OBV study
"""

import yfinance as yf
import polars as pl
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import os

# import config and logging
import sys
config_path = str(Path(__file__).parent.parent)
sys.path.append(config_path)
from config import (
    DEFAULT_PERIOD, DEFAULT_WINDOW_SIZE, VOLUME_THRESHOLD_MULTIPLIER,
    PLOT_CONFIG, AUTO_ADJUST, MULTI_LEVEL_INDEX, DOWNLOAD_PROGRESS,
    BUY_ON_DETECTION_DAY, RESULTS_DIR
)
from src.utils import get_logger, log_execution_time, log_method_call

logger = get_logger(__name__)

class StockAnalyzerOBV:
    def __init__(self, ticker: str):
        if not ticker or not isinstance(ticker, str):
            raise ValueError("Ticker must be a non-empty string")
        self.ticker = ticker.upper()
        self.df_data: pl.DataFrame = pl.DataFrame()
        self.df_acc: pl.DataFrame = pl.DataFrame()
        self.df_dist: pl.DataFrame = pl.DataFrame()
        self.df_results_holding:pl.DataFrame = pl.DataFrame()
        self.df_results_sl: pl.DataFrame = pl.DataFrame()
        self.hold_period: int | None = None
        self.profit_target: float | None = None
        self.stop_loss: float | None = None

        logger.info(f"Initialized StockAnalyzerOBV for ticker: {self.ticker}")
    
    @log_execution_time
    @log_method_call
    def detect_acc(self, period : str = DEFAULT_PERIOD, window_size : int = DEFAULT_WINDOW_SIZE, volume_threshold_multiplier : float = VOLUME_THRESHOLD_MULTIPLIER) -> None:
        """
        Download data from ticker and calculate different indicators, specifically accumulation and distribution
        
        Args:
            period (str): period time for stock data (e.g., '1y', '6mo').
            window_size (int): windows size for calculating the rolling mean
        Returns:
            None
        """
        try:

            data = yf.download(
                self.ticker, period=period, multi_level_index=MULTI_LEVEL_INDEX, 
                auto_adjust = AUTO_ADJUST, progress=DOWNLOAD_PROGRESS
            ).reset_index()

            if data.empty:
                raise ValueError(f"No data available for ticker: {self.ticker}")
            
            logger.debug(f"Downloaded {len(data)} rows of data")

            data=pl.DataFrame(data)
            data = data.with_columns(
                ticker = pl.lit(self.ticker),
                mean_volume=pl.col("Volume").rolling_mean(window_size=window_size)
            )

            obv_changes = (
                pl.when(pl.col("Close") > pl.col("Close").shift(1))
                .then(pl.col("Volume"))
                .when(pl.col("Close") < pl.col("Close").shift(1))
                .then(-pl.col("Volume"))
                .otherwise(0)
            )

            data = data.with_columns(
                OBV = obv_changes.cum_sum()
            )

            data = data.with_columns([
                (pl.col("Close") > pl.col("Close").shift(1)).alias("price_up"),
                (pl.col("Close") < pl.col("Close").shift(1)).alias("price_down"),
                (pl.col("Volume") > volume_threshold_multiplier * pl.col("mean_volume")).alias("volume_up"),
                (pl.col("OBV") > pl.col("OBV").shift(1)).alias("obv_up"),
                (pl.col("OBV") <= pl.col("OBV").shift(1)).alias("obv_not_up")
            ])

            data = data.with_columns(
                pl.when(pl.col("price_up") & pl.col("volume_up") & pl.col("obv_up"))
                .then(1)
                .otherwise(0)
                .alias("accumulation")
            )

            data = data.with_columns(
                pl.when(pl.col("price_down") & pl.col("volume_up") & pl.col("obv_not_up"))
                .then(1)
                .otherwise(0)
                .alias("distribution")
            )

            data = data.with_columns(
                pl.col('volume_up').fill_null(False),
                pl.col('price_up').fill_null(False),
                pl.col('obv_up').fill_null(False),
                pl.col('price_down').fill_null(False),
                pl.col('obv_not_up').fill_null(False),
            )

            self.df_data = data
            self.df_acc = self.df_data.filter((pl.col('accumulation') == 1))
            self.df_dist =  self.df_data.filter((pl.col('distribution') == 1))

            logger.info(f"Detected {self.df_acc.height} accumulation days and {self.df_dist.height} distribution days")
        
        except Exception as e:
            logger.error(f"Error in detect_acc for {self.ticker}: {str(e)}", exc_info=True)

        return None
    
    def _create_figure(self, acc_show : bool, dist_show : bool) -> go.Figure:

        colors = PLOT_CONFIG["color_scheme"]

        fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(f'Accumulation analysis for {self.ticker}', 'Volumen and OBV'),
            specs=[[{"secondary_y": False}], [{"secondary_y": True}]]
        )

        # First subplot -> Price and Accumulation
        fig.add_trace(
            go.Scatter(
                x=self.df_data['Date'], y=self.df_data['Close'], 
                mode='lines', name='Close Price',
                line=dict(color=colors["price"])
            ), row=1, col=1
        )

        if acc_show:
            fig.add_trace(
                go.Scatter(
                    x=self.df_acc['Date'], 
                    y=self.df_acc['Close'],
                    mode='markers', name='Accumulation',
                    marker=dict(color=colors["accumulation"], symbol='triangle-up', size=10)
                ), row=1, col=1
            )

        if dist_show:
            fig.add_trace(
                go.Scatter(
                    x=self.df_dist['Date'], 
                    y=self.df_dist['Close'],
                    mode='markers', name='Distribution',
                    marker=dict(color=colors["distribution"], symbol='triangle-down', size=10)
                ), row=1, col=1
            )

        # Second subplot -> Volume (bars) and OBV (line)
        fig.add_trace(
            go.Bar(
                x=self.df_data['Date'], y=self.df_data['Volume'], 
                name='Volumen', marker_color=colors["volume"]
            ), row=2, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=self.df_data['Date'], y=self.df_data['OBV'], 
                mode='lines', name='OBV',
                line=dict(color=colors["obv"])
            ), row=2, col=1, secondary_y=True
        )

        fig.update_layout(
            height=PLOT_CONFIG["height"],
            showlegend=True,
            title_text=f"Accumulation analysis for {self.ticker}",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig.update_yaxes(title_text="Price", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1, secondary_y=False)
        fig.update_yaxes(title_text="OBV", row=2, col=1, secondary_y=True, showgrid=False)
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_xaxes(showgrid=True)
        fig.update_yaxes(showgrid=True)
        
        return fig

    @log_method_call
    def plot_data(
            self, acc_show : bool = True, dist_show : bool = True, save_html : bool = True,
            output_dir : str = RESULTS_DIR, filename_prefix : str = 'plot_obv'
            ) -> None:
        """
        Plot price and accumulation, and plot volume and OBV. Write a html with both plots in one.
        
        Args:
            acc_show (bool): boolean to show accumulation or not at the plot
            dist_show (bool): boolean to show distribution or not at the plot
            save_html (bool): boolean to save the plot in a html or not
            filename (str): filename of HTML to save
        
        Returns:
            None
        """

        if self.df_data.is_empty():
            logger.warning(f"No data available to plot for {self.ticker}")
            print(f"No data available to plot for {self.ticker}")
            return None

        fig = self._create_figure(acc_show, dist_show)
        fig.show()

        if save_html:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            filename = os.path.join(output_path, f'{filename_prefix}_{self.ticker}.html')
            fig.write_html(filename)
            logger.info(f"Plot saved to {output_path}")

        return None
    
    def _validate_strategy_requirements(self) -> None:
        """Validate that detect_acc() has been run before calculating PnL"""
        if self.df_data is None or self.df_data.is_empty():
            raise ValueError("No data available. Run detect_acc() first.")
        
        if self.df_acc is None or self.df_acc.is_empty():
            raise ValueError("No accumulation signals detected.")
    
    @log_execution_time
    @log_method_call
    def calc_pnl_holding(
            self, hold_period: int, bool_detect_buy : bool = BUY_ON_DETECTION_DAY, save_results : bool = True,
            output_dir : str = RESULTS_DIR, filename_prefix : str = 'results_holding'
            ) -> None:
        """
        Calculate PnL based on a holding time strategy

        Args:
            save_result (bool): bool if saving results or not in excel file
            hold_period (int): number of holding days
            bool_detect_buy (bool): bool if buying in the day of detection or tomorrow

        Returns:
            None
        """
        self._validate_strategy_requirements()
        
        if hold_period <= 0:
            raise ValueError("hold_period must be positive")

        self.hold_period = hold_period
        df_dict = self.df_data.to_dicts()
        
        # Strategy 1: Hold time
        pnl_holding = []
        
        for row in self.df_acc.to_dicts():
            date_detection = row['Date']
            
            # find start index, date and price
            index_entry = next((i for i, d in enumerate(df_dict) if d['Date'] == date_detection), -1) + int(not bool_detect_buy)

            if index_entry >= len(df_dict):
                print("Accumulation detected for tomorrow, not shown today")
                continue

            date_buy = df_dict[index_entry]['Date']
            price_buy = df_dict[index_entry]['Close'] 

            # find end index, date and price
            index_sell = index_entry + hold_period  
            if 0 <= index_sell < len(df_dict):
                date_sell = df_dict[index_sell]['Date']
                price_sell = df_dict[index_sell]['Close']   

            else:
                date_sell = df_dict[len(df_dict)-1]['Date']
                price_sell = df_dict[len(df_dict)-1]['Close']

            pnl_pu = (price_sell - price_buy)
            rate_return = pnl_pu / price_buy * 100
            pnl_holding.append({
                'date_entry': date_buy,
                'price_buy': price_buy,
                'date_sell': date_sell,
                'price_sell': price_sell,
                'PnL_pu': pnl_pu,
                'rate_return': rate_return
            })
                
        self.df_results_holding = pl.DataFrame(pnl_holding)

        if save_results:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            filename = os.path.join(output_path, f'{filename_prefix}_{self.ticker}.xlsx')
            self.df_results_holding.write_excel(filename)
            logger.info(f"Holding strategy results saved to {output_path}")
        
        return None
    
    @log_execution_time
    @log_method_call
    def calc_pnl_sl(
            self, profit_target: float, stop_loss: float, bool_detect_buy : bool = BUY_ON_DETECTION_DAY, save_results : bool = True,
            output_dir : str = RESULTS_DIR, filename_prefix : str = 'results_stop_loss'
            ) -> None:
        """
        Calculate PnL based on a stop loss strategy

        Args:
            profit_target (float): percentatge of desired earning at max
            stop_loss (float): percentatge of desired loss at max
            bool_detect_buy (bool): bool if buying in the day of detection or tomorrow

        Returns:
            None
        """
        self._validate_strategy_requirements()

        if stop_loss < 0:
            raise ValueError("Stop loss value must be 0 or positive, negative value added on code.")

        self.profit_target = profit_target
        self.stop_loss = stop_loss
        df_dict = self.df_data.to_dicts()
        pnl_sl= []
        
        for row in self.df_acc.to_dicts():
            date_detection = row['Date']
            
            # find start index, date and price
            index_entry = next((i for i, d in enumerate(df_dict) if d['Date'] == date_detection), -1) + int(not bool_detect_buy)
            
            if index_entry >= len(df_dict):
                print("Accumulation detected for tomorrow, not shown today")
                continue

            date_buy = df_dict[index_entry]['Date']
            price_buy = df_dict[index_entry]['Close'] 


            for i in range(index_entry + 1, len(df_dict)):
                price_i = df_dict[i]['Close']
                day_sell = df_dict[i]['Date']
                
                pnl_pu = (price_i - price_buy)
                rate_return = pnl_pu / price_buy * 100
                reason = None
                
                if rate_return/100 >= profit_target:
                    reason = 'Take Profit'
                elif rate_return/100 <= -stop_loss:
                    reason = 'Stop Loss'
                
                if reason is not None:
                    pnl_sl.append({
                        'date_entry': date_buy,
                        'price_buy': price_buy,
                        'day_sell': day_sell,
                        'price_sell': price_i,
                        'reason': reason,
                        'PnL_pu': pnl_pu,
                        'rate_return': rate_return
                    })
                    break
                    
                # If we arrive to the end of data
                if i == len(df_dict) - 1:
                    pnl_pu = (price_i - price_buy)
                    rate_return = (price_i - price_buy) / price_buy
                    pnl_sl.append({
                        'date_entry': date_buy,
                        'price_buy': price_buy,
                        'day_sell': day_sell,
                        'price_sell': price_i,
                        'reason': 'End of data',
                        'PnL_pu': pnl_pu,
                        'rate_return': rate_return
                    })

            
        self.df_results_sl = pl.DataFrame(pnl_sl)

        if save_results:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            filename = os.path.join(output_path, f'{filename_prefix}_{self.ticker}.xlsx')
            self.df_results_sl.write_excel(filename)
            logger.info(f"Stop Loss strategy results saved to {output_path}")
        
        return None
    
    def summary_holding(self) -> None:
        """
        Summary of strategy holding time, it is required to have executed calc_pnl_holding() function before
        """
        if self.df_results_holding.is_empty():
            logger.warning("No holding strategy results available")
            print("No holding strategy results. Run calc_pnl_holding() first.")
            return None

        df_aux = self.df_results_holding
        print(f"Strategy 1: holding {self.hold_period} days for {self.ticker}")
        mean_pnl_pu = df_aux['PnL_pu'].mean()
        mean_rr = df_aux['rate_return'].mean()
        success = df_aux.filter(pl.col('rate_return') > 0).height
        print(f"Mean PnL per unit: {mean_pnl_pu:.2f}")
        print(f"Mean rate of return: {mean_rr:.2f}")
        print(f"Number of successes: {success} de {df_aux.height}")
        print("Details:")
        with pl.Config(tbl_rows=df_aux.height+1):
            print(df_aux)

        logger.info(f"Holding strategy summary calculated")
        
        return None

    def summary_sl(self) -> None:
        """
        Summary of strategy stop loss, it is required to have executed calc_pnl_sl() function before
        """
        if self.df_results_sl is None or self.df_results_sl.is_empty():
            logger.warning("No stop loss strategy results available")
            print("No stop loss strategy results. Run calc_pnl_sl() first.")
            return None
    
        df_aux = self.df_results_sl
        print(f"Strategy 2: profit target {self.profit_target:.2%}, stop loss {self.stop_loss:.2%} for {self.ticker}")
        mean_pnl_pu = df_aux['PnL_pu'].mean()
        mean_rr = df_aux['rate_return'].mean()
        tp_count = df_aux.filter(pl.col('reason') == 'Take Profit').height
        sl_count = df_aux.filter(pl.col('reason') == 'Stop Loss').height

        print(f"Mean PnL per unit: {mean_pnl_pu:.2f}")
        print(f"Mean rate of return: {mean_rr:.2f}")
        print(f"Operations 'Take Profit' ({self.profit_target:.2%}%): {tp_count}")
        print(f"Operations 'Stop Loss' ({self.stop_loss:.2%}%): {sl_count}")
        print("Details:")
        with pl.Config(tbl_rows=df_aux.height+1):
            print(df_aux)
        logger.info(f"Stop loss strategy summary calculated")

        return None
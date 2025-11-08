"""
Utility functions for logging the OBV study
"""

import logging
import logging.config
from functools import wraps
from typing import Callable, Any
import time
import yfinance as yf

def setup_logging(config_dict: dict) -> None:
    """
    Setup logging configuration
    
    Args:
        config_dict: Logging configuration dictionary
    """
    logging.config.dictConfig(config_dict)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance
    
    Args:
        name: Name of the logger (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def log_execution_time(func: Callable) -> Callable:
    """
    Decorator to log execution time of functions
    
    Args:
        func: Function to be decorated
    
    Returns:
        Wrapped function
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        logger.debug(f"Starting execution of {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"Completed {func.__name__} in {execution_time:.2f}s")
            return result
        
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error in {func.__name__} after {execution_time:.2f}s: {str(e)}")
            raise
    
    return wrapper

def log_method_call(func: Callable) -> Callable:
    """
    Decorator to log method calls with arguments
    
    Args:
        func: Method to be decorated
    
    Returns:
        Wrapped method
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs) -> Any:
        logger = get_logger(func.__module__)
        
        # Format arguments for logging
        args_str = ', '.join(repr(arg) for arg in args)
        kwargs_str = ', '.join(f"{k}={v!r}" for k, v in kwargs.items())
        all_args = ', '.join(filter(None, [args_str, kwargs_str]))
        
        logger.info(f"{self.__class__.__name__}.{func.__name__}({all_args})")
        
        try:
            result = func(self, *args, **kwargs)
            return result
        
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise
    
    return wrapper

def validate_ticker(ticker: str) -> str:
    """
    Validate and normalize ticker symbol
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Normalized ticker (uppercase, stripped)
    
    Raises:
        ValueError: If ticker is invalid
    """
    if not ticker or not isinstance(ticker, str):
        raise ValueError("Ticker must be a non-empty string")
    
    ticker = ticker.strip().upper()
    
    if len(ticker) == 0:
        raise ValueError("Ticker cannot be empty after stripping whitespace")
    
    info = yf.Ticker(ticker).history(
        period='7d',
        interval='1d')
    
    if len(info) == 0:
        raise ValueError("Ticker is not avaible in Yahoo Finance")
    
    return ticker

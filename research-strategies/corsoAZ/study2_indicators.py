"""
SPY 52-Week Range Trading Algorithm with Custom SMA Indicator
 
This algorithm implements a trading strategy for SPY (SPDR S&P 500 ETF) based on 52-week highs/lows
and a custom simple moving average indicator. It goes long when price approaches the 52-week high
and is above its moving average, indicating upward momentum.
"""

# region imports
from AlgorithmImports import *
from collections import deque
# endregion

class FocusedFluorescentYellowShark(QCAlgorithm):
    """
    A breakout trading algorithm for SPY using 52-week price ranges and trend confirmation
    
    This algorithm trades SPY based on its proximity to 52-week highs/lows and confirms
    the trend direction using a simple moving average. It goes long when price is within 5%
    of the 52-week high and above its moving average, indicating upward momentum.
    """

    def initialize(self):
        """
        Initialize the algorithm with required data subscriptions and indicators.
        
        Sets up:
        - Backtest start date of January 1, 2017
        - Initial capital of $10,000
        - SPY daily data subscription
        - Historical data for SMA warm-up
        - Custom SMA indicator registration
        """
        self.set_start_date(2017,1,1)
        self.set_cash(10000)

        self.spy = self.add_equity("SPY", resolution=Resolution.DAILY)
        
        #self._sma = self.sma(self.spy.symbol, 30, Resolution.DAILY)
        # History warm up for shortcut helper SMA indicator
        # closing_prices = self.history(self.spy.symbol, 30, Resolution.DAILY)['close']
        
        for time, price in closing_prices.loc[self.spy.symbol].items():
            self._sma.update(time, price)

        # Custom SMA indicator
        self.sma_custom = CustomSimpleMovingAverage() 
        self.register_indicator(self.spy.symbol, self.sma_custom, resolution=Resolution.DAILY)
        
        

    def on_data(self, data: Slice):
        """
        Main trading logic executed on each data update.
        
        Implements 52-week range trading strategy:
        - Gets 52-week high and low from historical data
        - Goes long when price is within 5% of 52-week high and above SMA
        - Liquidates positions otherwise
        - Plots key metrics for analysis
        
        Args:
            data (Slice): The current slice of data with market information
        """
        if not self._sma.is_ready:
            return

        hist = self.history(self.spy.symbol, timedelta(365), Resolution.DAILY)

        # high inefficient, every day I call the self.histry method
        low = min(hist['low'])
        high = max(hist['high'])

        holding = self.securities[self.spy.symbol]
        price = holding.price

        # Go long if near high and uptrending
        if price * 1.05 >= high and self._sma.current.value < price:
            if not self.portfolio[self.spy.symbol].is_long:  # error
                self.set_holdings(self.spy.symbol, 1)
        
        # Go short if near low and downtrending
        # elif price * 0.95 <= low and self._sma.current.value > price:  
        #    if not self.portfolio[self.spy.symbol].is_short:
        #        self.set_holdings(self.spy.symbol, -1)
        
        # Otherwise, go flat
        else:
            self.liquidate()
        
        self.plot("Benchmark", "52w-High", high)
        self.plot("Benchmark", "52w-Low", low)
        self.plot("Benchmark", "SMA", self.sma_custom.current.value)

    class CustomSimpleMovingAverage(PythonIndicator):
        """
        Custom Simple Moving Average indicator implementation.
        
        This indicator calculates a simple moving average of closing prices
        over a specified period using a deque for efficient FIFO operations.
        """
        
        def __init__(self, name, period):
            """
            Initialize the CustomSimpleMovingAverage indicator.
            
            Args:
                name (str): The name of the indicator
                period (int): The lookback period for the moving average calculation
            """
            self.name = name
            self.time = datetime.min
            self.value = 0
            self.queue = deque(maxlen=period)

        def update(self, input):
            """
            Update the indicator with new price data.
            
            Args:
                input: The price bar containing the latest data
                
            Returns:
                bool: True if the indicator has enough data to be valid, False otherwise
            """
            self.queue.appendleft(input.close)
            self.time = input.EndTime
            count = len(self.queue)
            self.value = sum(self.queue) / count
            # returns true if ready
            return (count == self.queue.maxlen)
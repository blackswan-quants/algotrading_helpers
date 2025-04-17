"""
SPY Gap Trading Algorithm
 
This algorithm implements a gap trading strategy for SPY (SPDR S&P 500 ETF) based on price gaps
at market open. It goes long on gap downs and short on gap ups, then exits all positions
15 minutes before market close each day.
"""

# region imports
from AlgorithmImports import *
# endregion

class AdaptableVioletJaguar(QCAlgorithm):
    """
    A mean-reversion gap trading algorithm for SPY
    
    This algorithm trades SPY based on price gaps between the previous day's close
    and the current day's opening price. It goes long when price gaps down by 1% or more
    and short when price gaps up by 1% or more. All positions are liquidated 15 minutes
    before market close each day.
    """

    def initialize(self):
        """
        Initialize the algorithm with required data subscriptions, parameters and scheduling.
        
        Sets up:
        - Backtest start date of January 1, 2018
        - Initial capital of $100,000
        - SPY minute-resolution data subscription
        - 2-bar rolling window for storing daily bars
        - Daily bar consolidation for tracking previous day's closing prices
        - Daily schedule to exit positions before market close
        """
        self.set_start_date(2018, 1, 1)
        self.set_cash(100000)
        self._spy = self.add_equity("SPY", Resolution.MINUTE).symbol

        self._rolling_window = RollingWindow[TradeBar](2) 

        self.consolidate(self._spy, Resolution.DAILY, self._custom_bar_handler)

        self.schedule.on(self.date_rules.every_day(self._spy),
                        self.time_rules.before_market_close(self._spy, 15),
                        self._exit_positions)


    def on_data(self, data: Slice):
        """
        Main trading logic executed on each data update.
        
        Implements gap trading strategy:
        - Only executes at 9:31 AM (1 minute after market open)
        - Goes short when SPY gaps up by 1% or more from previous close
        - Goes long when SPY gaps down by 1% or more from previous close
        
        Args:
            data (Slice): The current slice of data with market information
        """
        if not self._rolling_window.is_ready:
            return

        if not (self.time.hour == 9 and self.time.minute == 31):
            return

        # trade logic
        if data[self._spy].open >= 1.01 * self._rolling_window[0].close:  # gap up
            self.set_holdings(self._spy, -1)
        elif data[self._spy].close <= 0.99 * self._rolling_window[0].close:  # gap down
            self.set_holdings(self._spy, 1)
        

    def _custom_bar_handler(self, bar):
        """
        Handler for consolidated daily bars.
        
        Adds each completed daily bar to the rolling window to track
        previous days' closing prices.
        
        Args:
            bar (TradeBar): The consolidated daily bar
        """
        self._rolling_window.add(bar)

    def _exit_positions(self):
        """
        Scheduled function to exit all positions.
        
        Liquidates all SPY positions 15 minutes before market close each day.
        """
        self.liquidate(self._spy)
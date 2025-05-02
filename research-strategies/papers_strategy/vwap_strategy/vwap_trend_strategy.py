from AlgorithmImports import *

class VwapTrendTrading(QCAlgorithm):
    """
    A trading algorithm that uses intraday VWAP (Volume Weighted Average Price) to determine
    trend direction for the QQQ ETF and executes trades accordingly.

    - Enters a long or short position at 9:31 AM based on VWAP trend.
    - Exits at end of day (4:00 PM) or on intraday VWAP crossover.
    """

    def initialize(self):
        """
        Initializes the algorithm:
        - Sets backtest period and starting capital.
        - Adds QQQ equity with minute resolution.
        - Registers a 1-day VWAP indicator using 1-minute bars.
        - Sets intraday entry and exit times.
        """
        self.set_start_date(2018, 1, 2)
        self.set_end_date(2023, 9, 28)
        self.set_cash(25000)

        self._symbol = self.add_equity("QQQ", Resolution.MINUTE).Symbol
        self._vwap = VolumeWeightedAveragePriceIndicator("VWAP", 390)  # 1 day worth of 1-minute bars

        self.register_indicator(self._symbol, self._vwap, Resolution.MINUTE)
        self.consolidate(self._symbol, timedelta(minutes=1), self.on_data_consolidated)

        self.entry_time = time(9, 31)
        self.exit_time = time(16, 0)
        self.trading = False
        self.direction = None
        self.current_bar = None

    def on_data_consolidated(self, bar):
        """
        Event handler for receiving consolidated 1-minute bars.
        Stores the latest bar for use in trading logic.

        Args:
            bar (TradeBar): The consolidated trade bar.
        """
        self.current_bar = bar

    def on_data(self, data):
        """
        Main event handler for new data. Manages trade entry and exit based on VWAP:
        - Enters trade at 9:31 AM if not already in a trade.
        - Exits at 4:00 PM or on VWAP crossover indicating trend reversal.

        Args:
            data (Slice): The current market data.
        """
        if not self._vwap.is_ready or self.current_bar is None:
            return

        time_now = self.time.time()

        # Close position at end of day
        if time_now >= self.exit_time and self.portfolio[self._symbol].invested:
            self.liquidate(self._symbol, "EOD Exit")
            self.trading = False
            self.direction = None
            return

        # Entry logic at 9:31 AM
        if time_now == self.entry_time and not self.trading:
            price = self.current_bar.Close
            vwap_val = self._vwap.current.value

            if price > vwap_val:
                self.set_holdings(self._symbol, 1.0)
                self.direction = "long"
                self.trading = True

            elif price < vwap_val:
                self.set_holdings(self._symbol, -1.0)
                self.direction = "short"
                self.trading = True

        # Exit on VWAP crossover
        elif self.trading:
            price = self.current_bar.Close
            vwap_val = self._vwap.current.value

            if self.direction == "long" and price < vwap_val:
                self.liquidate(self._symbol, "Long Stop Loss")
                self.trading = False
                self.direction = None

            elif self.direction == "short" and price > vwap_val:
                self.liquidate(self._symbol, "Short Stop Loss")
                self.trading = False
                self.direction = None

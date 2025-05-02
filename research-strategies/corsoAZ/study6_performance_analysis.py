# region imports
from AlgorithmImports import *
# endregion

class CrawlingFluorescentPinkAntelope(QCAlgorithm):
    """
    A trading algorithm that switches allocation between SPY and BND
    based on a simple moving average (SMA) trend-following strategy.

    The algorithm allocates 80% to SPY and 20% to BND when SPY's price is above its SMA,
    and vice versa when below, with a 30-day rebalance cooldown period.
    """

    def initialize(self):
        """
        Initialize the algorithm settings, including the start/end dates,
        initial cash, added equities, and the SMA indicator with a configurable length.

        Also sets the initial rebalance time and trend direction flag.
        """
        self.set_start_date(2018, 1, 1)
        self.set_end_date(2021, 1, 1)
        self.set_cash(100000)
        self._spy = self.add_equity("SPY", Resolution.DAILY).symbol
        self._bnd = self.add_equity("BND", Resolution.DAILY).symbol

        length = self.get_parameter("sma_length")
        length = 30 if length is None else int(length)

        self._sma = self.sma(self._spy, length, Resolution.DAILY)
        self.rebalance_time = datetime.min
        self.uptrend = True

    def on_data(self, data: Slice):
        """
        Event handler for new market data.

        Implements logic to rebalance the portfolio based on whether SPY is
        trading above or below its SMA. Rebalancing occurs at most every 30 days.

        Args:
            data (Slice): The latest market data.
        """
        if not self._sma.is_ready or self._spy not in data or self._bnd not in data:
            return

        if data[self._spy].price >= self._sma.current.value:
            if self.time >= self.rebalance_time or not self.uptrend:
                self.set_holdings(self._spy, 0.8)
                self.set_holdings(self._bnd, 0.2)
                self.uptrend = True
                self.rebalance_time = self.time + timedelta(30)
        elif self.time >= self.rebalance_time or self.uptrend:
            self.set_holdings(self._spy, 0.2)
            self.set_holdings(self._bnd, 0.8)
            self.uptrend = False
            self.rebalance_time = self.time + timedelta(30)

        self.plot("benchmark", "SMA", self._sma.current.value)

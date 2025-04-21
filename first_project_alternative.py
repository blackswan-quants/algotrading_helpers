from AlgorithmImports import *

class ManualSmaStrategy(QCAlgorithm):
    """
    A manual trading strategy based on comparing the recent 30-day average price
    to a 210-day Simple Moving Average (SMA).

    The strategy rebalances once per month:
    - If 30-day average > SMA ➝ take a long position
    - If 30-day average < SMA ➝ take a short position
    - If equal ➝ stay flat (liquidate)

    Positions are equally weighted across all active signals.
    """

    def initialize(self):
        """
        Initialize the algorithm:
        - Set backtest period and starting cash
        - Define the list of ETFs to trade
        - Create SMA indicators and rolling windows for average price calculation
        """
        self.set_start_date(2006, 7, 21)
        self.set_end_date(2025, 1, 1)
        self.set_cash(100000)

        self.tickers = ['SPY', 'EFA', 'IEF', 'GSG', 'VNQ']
        self.symbols = []

        self.sma_period = 210
        self.monthly_avg_days = 30
        self.last_rebalance_month = -1

        self.sma = {}
        self.prices = {}

        for ticker in self.tickers:
            symbol = self.add_equity(ticker, Resolution.DAILY).symbol
            self.symbols.append(symbol)
            self.sma[symbol] = self.sma_indicator(symbol, self.sma_period, Resolution.DAILY)
            self.prices[symbol] = RollingWindow[float](self.monthly_avg_days)

    def sma_indicator(self, symbol, period, resolution):
        """
        Create and return a Simple Moving Average (SMA) indicator.

        Args:
            symbol (Symbol): The asset to track.
            period (int): The number of days in the moving average.
            resolution (Resolution): The data resolution for the indicator.

        Returns:
            Indicator: The SMA indicator object.
        """
        return self.SMA(symbol, period, resolution)

    def on_data(self, data: Slice):
        """
        Main method called daily.
        - Updates rolling windows with recent close prices
        - Once per month, compares the 30-day average price to the SMA
        - Issues long, short, or flat positions based on the signal

        Args:
            data (Slice): The current market data slice.
        """
        # Store recent prices
        for symbol in self.symbols:
            if data.contains_key(symbol) and data[symbol] is not None and data[symbol].close != 0:
                self.prices[symbol].add(data[symbol].close)

        # Rebalance only once per month
        if self.time.month == self.last_rebalance_month:
            return

        # Wait until all indicators and price windows are ready
        if not all(self.sma[s].is_ready and self.prices[s].is_ready for s in self.symbols):
            return

        self.last_rebalance_month = self.time.month

        # Generate signals
        insights = {}
        for symbol in self.symbols:
            sma_value = self.sma[symbol].current.value
            monthly_avg = sum(self.prices[symbol]) / self.monthly_avg_days

            if monthly_avg > sma_value:
                insights[symbol] = 1  # Long
            elif monthly_avg < sma_value:
                insights[symbol] = -1  # Short
            else:
                insights[symbol] = 0  # Flat

        # Count how many positions to allocate
        n_positions = sum(1 for d in insights.values() if d != 0)

        if n_positions == 0:
            for symbol in self.symbols:
                self.liquidate(symbol)
            return

        weight = 1.0 / n_positions

        # Set holdings based on direction
        for symbol in self.symbols:
            direction = insights[symbol]
            if direction == 1:
                self.set_holdings(symbol, weight)
            elif direction == -1:
                self.set_holdings(symbol, -weight)
            else:
                self.liquidate(symbol)

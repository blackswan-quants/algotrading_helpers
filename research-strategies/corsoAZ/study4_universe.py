"""
Small Cap Equities Trading Algorithm
 
This algorithm implements a small-cap equity strategy that selects the 10 smallest market cap stocks
from the top 200 most liquid stocks (by dollar volume) and rebalances the portfolio monthly.
It creates an equally-weighted portfolio of these 10 stocks.
"""

# region imports
from AlgorithmImports import *
# endregion

class CrawlingBrownLion(QCAlgorithm):
    """
    A small-cap investing algorithm that rebalances monthly
    
    This algorithm filters for the top 200 most liquid stocks with price above $10, 
    then selects the 10 stocks with the smallest market capitalization. It creates an 
    equal-weighted portfolio of these stocks and rebalances monthly.
    """

    def initialize(self):
        """
        Initialize the algorithm with required parameters and universe settings.
        
        Sets up:
        - Backtest start date of January 1, 2017
        - Initial capital of $100,000
        - Monthly rebalance schedule
        - Universe selection with coarse and fine filters
        - Hourly resolution for data
        """
        self.set_start_date(2017, 1, 1)
        self.set_cash(100000)

        self._rebalance_time = datetime.min
        self._active_stocks = set() 

        self.add_universe(self._coarse_filter, self._fine_filter)
        self.universe_settings.resolution = Resolution.HOUR

        self._portfolio_targets = []

    def _coarse_filter(self, coarse):
        """
        First-stage universe selection using coarse fundamentals data.
        
        Selects the top 200 stocks by dollar volume that:
        - Have price > $10
        - Have fundamental data available
        - Rebalances monthly (every 30 days)
        
        Args:
            coarse: List of CoarseFundamental objects
            
        Returns:
            List of symbols that pass the filter criteria or unchanged universe if not rebalance time
        """
        if self.time <= self._rebalance_time:
            return self.universe.unchanged

        self._rebalance_time = self.time + timedelta(30)

        sorted_by_dollar_volume = sorted(coarse, key = lambda x: x.dollar_volume,
                                            reverse = True)

        return [x.symbol for x in sorted_by_dollar_volume if x.price > 10 
                                    and x.has_fundamental_data][:200]

    def _fine_filter(self, fine):
        """
        Second-stage universe selection using fine fundamentals data.
        
        Selects the 10 stocks with the smallest market capitalization from
        the stocks that passed the coarse filter and have positive market cap.
        
        Args:
            fine: List of FineFundamental objects
            
        Returns:
            List of 10 symbols with the smallest market cap
        """
        sorted_by_PE = sorted(fine, key= lambda x: x.market_cap)
        return [x.symbol for x in sorted_by_PE if x.market_cap > 0][:10]

    def on_securities_changed(self, changes):
        """
        Handles changes to securities in the algorithm's universe.
        
        - Liquidates positions for securities removed from the universe
        - Adds new securities to the active stocks set
        - Creates equal-weighted portfolio targets for all active stocks
        
        Args:
            changes: SecurityChanges object containing added and removed securities
        """
        for x in changes.removed_securities:
            self.liquidate(x.symbol)
            self._active_stocks.remove(x.symbol)

        for x in changes.added_securities:
                self._active_stocks.add(x.symbol)

        self._portfolio_targets = [PortfolioTarget(symbol, 1/len(self._active_stocks))
                                                for symbol in self._active_stocks]
    def on_data(self, data: Slice):
        """
        Main data event handler executed on each data update.
        
        Implements portfolio allocation logic:
        - Sets holdings according to portfolio targets when all symbols have data
        - Clears portfolio targets after execution
        
        Args:
            data (Slice): The current slice of data with market information
        """
        if self._portfolio_targets == []:
            return

        for symbol in self._active_stocks:
            if symbol not in data:
                return

        self.set_holdings(self._portfolio_targets)
        self._portfolio_targets = []
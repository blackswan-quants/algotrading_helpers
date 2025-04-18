# region imports
from AlgorithmImports import *
from datetime import datetime
# endregion

class MuscularSkyBlueJackal(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2006, 7, 21)
        self.set_end_date(2025, 1, 1)
        self.set_cash(100000)
        self.universe_settings.resolution = Resolution.DAILY
        self.universe_settings.data_normalization_mode = DataNormalizationMode.ADJUSTED

        tickers = ['SPY', 'EFA', 'IEF', 'GSG', 'VNQ']
        symbols = [ Symbol.create(ticker, SecurityType.EQUITY, Market.USA) for ticker in tickers]

        self.set_universe_selection(ManualUniverseSelectionModel(symbols)) #universe initialized
        
        # Set no slippage for each security in the universe
        for symbol in symbols:
            security = self.add_equity(symbol.value, Resolution.DAILY)
            security.set_slippage_model(NullSlippageModel())  # Disable slippage

        self.set_alpha(MyAlpha()) # to create on QuantConnect 

        self.set_portfolio_construction(EqualWeightingPortfolioConstructionModel()) 

        self.set_risk_management(NullRiskManagementModel()) 

        self.set_execution(ImmediateExecutionModel()) 




class MyAlpha(AlphaModel):
    def __init__(self):
        self.last_rebalance = (-1, -1)  # (year, month)
        self.smadict = {}

    def OnSecuritiesChanged(self, algorithm, changes):
        for security in changes.AddedSecurities:
            symbol = security.Symbol
            self.smadict[symbol] = SimpleMovingAverage(210)

    def Update(self, algorithm, data):
        # Only rebalance once per month
        current_ym = (algorithm.Time.year, algorithm.Time.month)
        if current_ym == self.last_rebalance:
            return []
        self.last_rebalance = current_ym
        # Ensure all SMAs are ready before generating insights
        for symbol in data.Keys:
            if symbol not in self.smadict:
                continue
            bar = data[symbol]
            if bar is not None and bar.Close is not None:
                self.smadict[symbol].Update(algorithm.Time, bar.Close)

        for symbol in self.smadict:
            if not self.smadict[symbol].IsReady:
                return []

        # ✅ Time to rebalance


        insights = []
        for symbol in self.smadict:
            # Get historical data (last 30 days of close)
            history = algorithm.History(symbol, 30, Resolution.Daily)
            if history.empty:
                continue

            monthly_avg = history['close'].mean()
            sma_value = self.smadict[symbol].Current.Value

            direction = InsightDirection.Up if monthly_avg > sma_value else InsightDirection.Down
            insights.append(Insight.Price(symbol, timedelta(days=30), direction))

        return insights



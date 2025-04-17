# region imports
from AlgorithmImports import *
# endregion

class VirtualFluorescentYellowGoat(QCAlgorithm):
    """
    QQQ Trading Algorithm with Trailing Stop Loss
    
    This algorithm implements a trading strategy for QQQ (Invesco QQQ Trust ETF) with 
    a trailing stop loss mechanism. It enters positions using limit orders at current 
    market price and implements a 5% trailing stop loss to protect profits.
    
    Key features:
    - Invests 90% of portfolio in QQQ
    - Uses limit orders for entry with dynamic price updates
    - Implements 5% trailing stop loss that moves up with price
    - 30-day cooling period after stop loss triggers
    """

    def initialize(self):
        """
        Initialize the algorithm parameters, data subscriptions, and tracking variables.
        
        Sets up:
        - Backtest period from 2000 to 2024
        - Initial capital of $100,000
        - QQQ subscription with hourly resolution
        - SPY as benchmark
        - Instance variables for order management and price tracking
        """
        self.set_start_date(2000, 1, 1)
        self.set_end_date(2024, 12, 31)
        self.set_cash(100000)

        self.qqq = self.add_equity("QQQ", Resolution.HOUR)

        # Set QQQ as the benchmark
        self.set_benchmark("SPY")

        self.entryTicket = None
        self.stopMarketTicket = None

        self.entryTime = datetime.time
        self.stopMarketOrderFillTime = datetime.min
        self.highestPrice = 0


    def on_data(self, data: Slice):
        """
        Main trading logic executed on each data update.
        
        Implements:
        - Entry logic for placing limit orders when not invested
        - Dynamic limit price updates if orders remain unfilled
        - Trailing stop adjustment as price increases
        
        Args:
            data (Slice): The current slice of data with market information
        """
        # wait 30 days after last exit
        if (self.time - self.stopMarketOrderFillTime).days < 30:
            return

        price = self.securities[self.qqq.Symbol].price

        # send entry limit order
        if not self.portfolio.Invested and not self.transactions.get_open_orders(self.qqq.Symbol):
            quantity = self.calculate_order_quantity(self.qqq.Symbol, 0.9)
            self.entryTicket = self.limit_order(self.qqq.symbol, quantity, price, "Entry Order")
            self.entryTime = self.time

        # move limit price if not filled after 1 day
        if (self.time - self.entryTime).days > 1 and self.entryTicket.Status != OrderStatus.FILLED:
            self.entryTime = self.time
            updateFields = UpdateOrderFields()
            updateFields.limit_price = price
            self.entryTicket.update(updateFields)

        # move up trailing stop price
        if self.stopMarketTicket is not None and self.portfolio.Invested:
            if price > self.highestPrice:
                self.highestPrice = price
                updateFields = UpdateOrderFields()
                updateFields.stop_price = self.highestPrice * 0.95
                self.stopMarketTicket.update(updateFields)
                #self.debug(f"new stop price: {updateFields.stop_price}")

        pass

    def OnOrderEvent(self, orderEvent):
        """
        Handles order events, particularly fill events for entry and stop orders.
        
        Actions:
        - Creates stop loss order when entry order is filled
        - Records exit time when stop loss is triggered
        - Resets tracking variables after exit
        
        Args:
            orderEvent: The order event containing order status and details
        """
        if orderEvent.Status != OrderStatus.FILLED:
            return
        
        # send stop loss order if entry limit order is filled
        if self.entryTicket is not None and self.entryTicket.order_id == orderEvent.order_id:
            self.stopMarketTicket = self.stop_market_order(self.qqq.Symbol, -self.entryTicket.quantity,
                                                    0.95*self.entryTicket.average_fill_price)

        # save fill time of stop loss order
        if self.stopMarketTicket is not None and self.stopMarketTicket.order_id == orderEvent.order_id:
            self.stopMarketOrderFillTime = self.time
            self.highestPrice = 0

        pass
from backtrader import Strategy


class Strategy(Strategy):
    """
    Strategy template use to specify the market type.

    Params

      - ``name``: the strategy name
      - ``market``: the market type
      - ``order_percentage``: the percentage of our availabe cash that will be
      used to fill the order
      - ``ticker``: the ticker
    """

    params = (("name", ""), ("notifytrade", "False"))

    def log(self, txt, dt=None):
        """Logging function fot this strategy"""
        dt = dt or self.datas[0].datetime.date(0)
        print("%s, %s" % (dt.isoformat(), txt))

    def notify_trade(self, trade):
        if self.p.notifytrade == True:
            if trade.justopened:
                self.log(
                    "Trade Opened  - Size {} @Price {}".format(trade.size, trade.price)
                )
            elif trade.isclosed:
                self.log("Trade Closed  - Profit {}".format(trade.pnlcomm))

            else:  # trade updated
                self.log(
                    "Trade Updated - Size {} @Price {}".format(trade.size, trade.price)
                )

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    "BUY EXECUTED - Size: {} @Price: {} Value: {:.2f} Comm: {:.2f}".format(
                        order.executed.size,
                        order.executed.price,
                        order.executed.value,
                        order.executed.comm,
                    )
                )
            elif order.issell():
                self.log("SELL EXECUTED, %.2f" % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        # Write down: no pending order
        self.order = None

from typing import List, Tuple
import backtrader as bt
from backtrader.feeds.pandafeed import PandasData
from backtrader.plot import Plot_OldSync
from datetime import datetime
import pyfolio as pf
import pandas as pd
import os

from strategies.SuperTrend import SuperTrend

from utils import BINANCE_TICKERS, INTERVALS


class CustomPlotScheme(Plot_OldSync):
    def __init__(self):
        super().__init__()
        self.params.scheme.style = "candle"
        self.params.scheme.barup = "green"

    def plot(
        self, strategy, figid=0, numfigs=1, iplot=True, start=None, end=None, **kwargs
    ):
        figs = super().plot(strategy, figid, numfigs, iplot, start, end, **kwargs)

        for i, fig in enumerate(figs):
            width = 100
            height = 16
            dpi = 300
            fig.set_size_inches(width, height)
            filename = "/Users/pons_n/Desktop/" + "test" + str(i) + ".png"
            print("Trying to save the plot")
            fig.savefig(filename, dpi=dpi)

    def show(self):
        print("skip the display")
        return


class Backtest:
    def __init__(
        self,
        cash=1000,
        commission=0.00075,
        path_to_data: str = "",
        path_to_save: str = "",
        intervals: List[str] = INTERVALS,
        tikers: List[str] = BINANCE_TICKERS,
        strategies: List[Tuple[str, bt.Strategy]] = None,
    ) -> None:
        self.cash = cash
        self.intervals = intervals
        self.tickers = tikers
        self.path_to_data = path_to_data
        self.path_to_save = path_to_save
        self.commission = commission
        self.strategies = strategies

    def _preprocessing(self, strategy, feed) -> None:
        self.cerebro = bt.Cerebro()

        # Set cash
        self.cerebro.broker.setcash(self.cash)

        # Set commission
        self.cerebro.broker.setcommission(commission=self.commission, margin=False)

        # Set strategy
        print("Setting the {} strategy".format(strategy[0]))
        self.cerebro.addstrategy(SuperTrend)

        # Set analyser
        print("Setting the analyser pyfolio")
        self.cerebro.addanalyzer(bt.analyzers.PyFolio, _name="pyfolio")

        # Set position size
        #self.cerebro.addsizer(bt.sizers.PercentSizer, percents=100)

        # Add data
        self.cerebro.adddata(feed)

    def _loading_binance_data(self, ticker, interval) -> PandasData:
        filename = os.path.join(self.path_to_data, interval, "{}.csv".format(ticker))

        try:
            data = pd.read_csv(filename, index_col=False)
            data["Open time"] = pd.to_datetime(data["Open time"], unit="s")
            return bt.feeds.PandasData(
                dataname=data,
                datetime="Open time",
                open=1,
                high=2,
                low=3,
                close=4,
                volume=5,
            )
        except FileNotFoundError:
            print("Path {} not found".format(filename))


    def run(self) -> None:
        print("Starting backtest...")

        try:
            print("Backtest {} strategies".format(len(self.strategies))) if len(
                self.strategies > 1
            ) else print("Backtest {} strategies".format(len(self.strategies)))
        except TypeError:
            print("strategies list is None or empty")

        saving_directory = os.path.join(
            self.path_to_save, datetime.now().strftime("%y-%m-%d-%H-%M")
        )
        os.mkdir(saving_directory)

        for strategy in self.strategies:
            print("Backtesting the {} strategy".format(strategy[0]))
            filename = "_".join(strategy[0].lower().split())
            strategy_path = os.path.join(saving_directory, filename)
            for interval in self.intervals:
                print("Backtesting on {} interval".format(interval))
                strategy_statistics_path = "_".join([strategy_path, interval])            
                for ticker in self.tickers:
                    print(ticker)

                    feed = self._loading_binance_data(ticker, interval)
                    self._preprocessing(strategy, feed)
                    results = self.cerebro.run()
                    strat = results[0]
                    pyfoliozer = strat.analyzers.getbyname("pyfolio")

                    (
                        returns,
                        positions,
                        transactions,
                        gross_lev,
                    ) = pyfoliozer.get_pf_items()
                    print("Saving files")
                    self._save_csv(returns, "returns", strategy_statistics_path)
                    self._save_csv(positions, "positions", strategy_statistics_path)
                    self._save_csv(
                        transactions, "transactions", strategy_statistics_path
                    )

                    pf.create_simple_tear_sheet(
                        returns, positions=positions, transactions=transactions
                    )

                    self.cerebro.plot(plotter=CustomPlotScheme(), iplot=False)

    def _save_csv(self, df, filename: str, directory: str) -> None:
        df.to_csv(directory + "_" + filename + ".csv")

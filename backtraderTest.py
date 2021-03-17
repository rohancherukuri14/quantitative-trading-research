from twelvedata import TDClient
import pandas as pd
from backtesting import Strategy, Backtest
from backtesting.lib import crossover
import time

class RSI(Strategy):
    rsiBottom = 30
    rsiTop = 70
    hasStock = 0
    index = 0

    def init(self):
        pass

    def next(self):
        if self.data.rsi[self.index] < self.rsiBottom and not(self.hasStock):
            self.buy()
            self.hasStock = 1
        elif self.data.rsi[self.index] > self.rsiTop and self.hasStock:
            self.sell()
            self.hasStock = 0
        self.index += 1

class SmaCross(Strategy):
    n1 = 10
    n2 = 20

    def init(self):
        self.sma1 = self.I(SMA, self.data.Close, self.n1)
        self.sma2 = self.I(SMA, self.data.Close, self.n2)

    def next(self):
        if crossover(self.sma1, self.sma2):
            self.buy()
        elif crossover(self.sma2, self.sma1):
            self.sell()

class VWAP(Strategy):

    def init(self):
        pass

    def next(self):
        if crossover(self.data.Close, self.data.vwap):
            self.position.close()
            self.buy()
        elif crossover(self.data.vwap, self.data.Close):
            self.position.close()
            self.sell()


class MACDZLCross(Strategy):

    index = 0
    hasStock = 0

    def init(self):
        pass

    def next(self):
        if self.data.macd[self.index] > 0 and not(self.hasStock):
            self.buy()
            self.hasStock = 1
        elif self.data.macd[self.index] < 0  and self.hasStock:
            self.sell()
            self.hasStock = 0
        self.index += 1

class MACDSLCross(Strategy):

    index = 0
    hasStock = 0

    def init(self):
        pass

    def next(self):
        if self.data.macd[self.index] > self.data.macd_signal[self.index] and not(self.hasStock):
            self.buy()
            self.hasStock = 1
        elif self.data.macd[self.index] < self.data.macd_signal[self.index] and self.hasStock:
            self.sell()
            self.hasStock = 0
        self.index += 1

class heikin(Strategy):
    index = 0
    hollow = 0
    momentum_increasing = 0
    initiation_candles = 0
    hasStock = 0
    def init(self):
        self.differences = self.data.heikincloses - self.data.heikinopens
        self.hollow = self.data.heikincloses > self.data.heikinopens

    def next(self):
        if not self.hollow[self.index]:
            if not(self.momentum_increasing) and not(self.hasStock):
                if abs(self.differences[self.index]) < abs(self.differences[self.index-1]) \
                        and abs(self.differences[self.index-1]) < abs(self.differences[self.index-2]) \
                        and self.data.heikincloses[self.index] > self.data.heikinlows[self.index]:
                    self.momentum_increasing = 1
            elif not(self.momentum_increasing) and self.hasStock:
                if (self.data.heikinopens - self.data.heikinhighs) / self.data.heikinhighs < 0.05:
                    self.sell()
                    self.hasStock = 0

        elif self.hollow[self.index]:
            if self.momentum_increasing and not(self.hasStock):
                if self.initiation_candles < 3:
                    if (self.data.heikinopens - self.data.heikinlows) / self.data.heikinlows < 0.05:
                        self.initiation_candles += 1
                else:
                    self.buy()
                    self.hasStock = 1
                    self.momentum_increasing = 0
                    self.initation_candles = 0
        self.index += 1


class overall(Strategy):
    index = 0
    hasStock = False
    def init(self):
        self.differences = self.data.heikincloses - self.data.heikinopens
        self.hollow = self.data.heikincloses > self.data.heikinopens
    def next(self):
        macd = self.data.macd[self.index]
        macd_sig = self.data.macd_signal[self.index]
        sell_cross = crossover(self.data.vwap, self.data.Close)
        sell_macd_sig = macd < macd_sig
        volume_increasing = self.data.Volume[self.index] > self.data.Volume[self.index-1]
        is_hollow = self.hollow[self.index]
        momentum_increasing = abs(self.differences[self.index]) < abs(self.differences[self.index-1]) \
                        and abs(self.differences[self.index-1]) < abs(self.differences[self.index-2]) \
                        and self.data.heikincloses[self.index] > self.data.heikinlows[self.index]
        check_top = (self.data.heikinopens[self.index] - self.data.heikinhighs[self.index]) / self.data.heikinhighs[self.index] < 0.05
        check_bottom = (self.data.heikinopens[self.index] - self.data.heikinlows[self.index]) / self.data.heikinlows[self.index] < 0.05
        buy_heikin = is_hollow and momentum_increasing and not(self.hasStock) and check_bottom
        sell_heikin = not(is_hollow) and not(momentum_increasing) and self.hasStock and check_top
        if buy_heikin:
            self.buy()
            self.hasStock = True
        elif (sell_cross or sell_macd_sig or sell_heikin or not(volume_increasing)) and self.hasStock:
            self.sell()
            self.hasStock = False
        self.index += 1



def SMA(values, n):
    return pd.Series(values).rolling(n).mean()

def testManyStocks(stockList):
    startingCapital = 1000 * len(stockList)
    endCapital = 0
    print("Total Starting Capital: " + str(startingCapital))
    for ticker in stockList:
        print("Starting Capital: 1000")
        print(ticker)
        data = getData(ticker)
        print(data)
        bt = Backtest(data, overall, cash = 1_000, commission = 0.002)
        stats = bt.run()
        endCapital += stats[4]
        print(endCapital)
    return startingCapital, endCapital


def getData(ticker):
    td = TDClient(apikey="b34e89fbda894c4186fdd1db0c4aca4b")
    ts1 = td.time_series(
        symbol=ticker,
        interval="5min",
        outputsize=78
    ).with_vwap().with_macd()
    ts1_p = ts1.as_pandas()
    ts2 = ts1.with_heikinashicandles()
    ts2_p = ts2.as_pandas()
    ts = pd.concat([ts1_p, ts2_p], axis=1).reindex(ts1_p.index)
    ts = ts.rename(columns={"open": "Open", "close": "Close", "high": "High", "low": "Low", "volume": "Volume"})
    for i in ts:
        print(i)
    return ts

testStocks = ["EYES"]
c, s = testManyStocks(testStocks)


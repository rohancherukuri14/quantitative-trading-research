import alpaca_backtrader_api
import backtrader as bt
from datetime import datetime

ALPACA_API_KEY = 'AKSV8IE6PIEJCC0PO5C2'
ALPACA_SECRET_KEY = 'RxXvwZ6bNY9UMO9a0FBaFqY8Jhc0rtrIRgBKZvM7'
ALPACA_PAPER = True

class HeikenAshi(bt.Strategy):
    def __init__(self):
        self.heikinValues = bt.ind.HeikinAshi()
        self.num_increasing = 0
        self.momentum_increasing = False
        self.hasStock = False
        self.initiationCandles = 0
        self.buySize = 0
    def next(self):
        open = self.heikinValues.lines.open[0]
        close = self.heikinValues.lines.close[0]
        high = self.heikinValues.lines.high[0]
        low = self.heikinValues.lines.low[0]
        difference_1 = close - open
        prev_open = self.heikinValues.lines.open[-1]
        prev_close = self.heikinValues.lines.close[-1]
        difference_2 = prev_close - prev_open
        hollow = close > open
        if not hollow:
            if not(self.momentum_increasing) and not(self.hasStock) and difference_1 > difference_2:
                if self.num_increasing < 2:
                    self.num_increasing += 1
                elif self.num_increasing == 2:
                    self.momentum_increasing = True
                    self.num_increasing = 0
            elif not(self.momentum_increasing) and self.hasStock:
                    if (open - high) / high < 0.05:
                        self.hasStock = False
                        self.sell(size = 3000)
        if hollow:
            if self.momentum_increasing and not(self.hasStock):
                if self.initiationCandles < 2:
                    if (open - low) / low < 0.05:
                        self.initiationCandles += 1
                elif self.initiationCandles == 2:
                    self.hasStock = True
                    self.initiationCandles = 0
                    self.buy(size = self.buySize)
            elif not(self.momentum_increasing) and not(self.hasStock):
                if self.initiationCandles < 3:
                    if (open - low) / low < 0.05:
                        self.initiationCandles += 1

cerebro = bt.Cerebro()
cerebro.addstrategy(HeikenAshi)

store = alpaca_backtrader_api.AlpacaStore(
    key_id=ALPACA_API_KEY,
    secret_key=ALPACA_SECRET_KEY,
    paper=ALPACA_PAPER
)

if not ALPACA_PAPER:
  broker = store.getbroker()  # or just alpaca_backtrader_api.AlpacaBroker()
  cerebro.setbroker(broker)

DataFactory = store.getdata  # or use alpaca_backtrader_api.AlpacaData
data0 = DataFactory(dataname='MSFT', historical=True, fromdate=datetime(
    2021, 3, 4),  timeframe=bt.TimeFrame.Minutes)
data0.addfilter(bt.filters.HeikinAshi(data0))
cerebro.adddata(data0)
# cerebro.run()
# cerebro.plot(style='candlestick')


print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
cerebro.run()
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
cerebro.plot()








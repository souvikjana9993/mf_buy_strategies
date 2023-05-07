import backtrader as bt
from setup_logger import logger
import datetime
from utils import xnpv,xirr
import numpy as np


class OHLC(bt.analyzers.Analyzer):
    """This analyzer reports the OHLCV +lines of each of datas.
    Params:
      - timeframe (default: ``None``)
        If ``None`` then the timeframe of the 1st data of the system will be
        used
      - compression (default: ``None``)
        Only used for sub-day timeframes to for example work on an hourly
        timeframe by specifying "TimeFrame.Minutes" and 60 as compression
        If ``None`` then the compression of the 1st data of the system will be
        used
    Methods:
      - get_analysis
        Returns a dictionary with returns as values and the datetime points for
        each return as keys
    """

    def start(self):
        tf = min(d._timeframe for d in self.datas)
        self._usedate = tf >= bt.TimeFrame.Days
        self.rets = {}

    def next(self):

        self.rets[self.data.datetime.datetime()] = [
            #self.datas[0].open[0],
            #self.datas[0].high[0],
            #self.datas[0].low[0],
            self.datas[0].close[0]
            #self.MA1[0],
            #self.MA2[0],
            #self.signal[0],
        ]

    def get_analysis(self):
        return self.rets

class DayslowadjustedSIP(bt.Strategy):
    params = dict(dayscutoff=30)

    def __init__(self):
        self.lowest_price = None
        self.buy_date = datetime.datetime(1900, 1, 1)
        self.dataclose = self.datas[0].close
        self.buy_count = 0
        self.total_deposits = 0
        self.dayslowhit = 0
        self.buy_array = [[self.datas[0].datetime.datetime().date(),float(-self.broker.getvalue())]]
        self.mystats = open('mystats_varsip30lowhit.csv', 'w')
        self.mystats.write('datetime,drawdown, maxdrawdown\n')
        # self.rets = {}


    def next(self):
        # get the current date and time
        dt = self.datas[0].datetime.datetime()
        
        # check if at least 30 days have passed since the last buy order
        if len(self) >= int(self.params.dayscutoff):
            self.lowest_price = min(self.data.close.get(size=int(self.params.dayscutoff)))
            

        # if the current price is equal to the 30-day low price, buy the mutual fund
        if self.data.close[0] == self.lowest_price:
            #print(np.argmin(self.data.close.get(size=9999999999999)))
            navlist = self.data.close.get(size=9999999999999) 
            for i in reversed(navlist):
                if i < navlist[-1]:
                    self.dayslowhit = len(navlist) - navlist.index(i) -1
                    break
                else:
                    pass
            size = max((self.dayslowhit/int(self.params.dayscutoff)),1)*1000
            self.buy(size=size/self.data.close[0])
            self.buy_date = dt
            self.buy_count += 1
            self.total_deposits += size
            self.buy_array.append([dt.date(),float(-size)])
            logger.debug('BUY CREATE, %.2f' % self.dataclose[0])
            logger.debug('Buy Orders Created: %d' % self.buy_count)
            logger.debug('Total Deposits: %.2f' % (self.total_deposits+100000))
            
            
            

        # log
        logger.debug(self.datas[0].datetime.datetime())
        logger.debug('Close, %.2f' % self.dataclose[0])
        logger.debug('value, %.2f' % self.broker.getvalue())


        self.mystats.write(self.data.datetime.date(0).strftime('%Y-%m-%d'))
        self.mystats.write(',%.2f' % self.stats.drawdown.drawdown[-1])
        self.mystats.write(',%.2f' % self.stats.drawdown.maxdrawdown[-1])
        self.mystats.write('\n')

        # self.rets[self.data.datetime.datetime()] = [
        #     self.datas[0].open[0],
        #     self.datas[0].high[0],
        #     self.datas[0].low[0],
        #     self.datas[0].close[0]
        #     #self.MA1[0],
        #     #self.MA2[0],
        #     #self.signal[0],
        # ]

    def stop(self):
        # export the buy array to CSV
        self.buy_array.append([self.datas[0].datetime.datetime().date(),float(self.broker.getvalue())])
#         with open('buy_transactions.csv', 'w', newline='') as f:
#             writer = csv.writer(f)
#             writer.writerows(self.buy_array)
        
        self.xirr = round(xirr(np.array(self.buy_array),guess=0.1)*100,1)
        logger.info('Overall XIRR, %.2f' % self.xirr)

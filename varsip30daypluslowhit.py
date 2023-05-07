## buy at 30 day low and adjust the buy amount with days low hit
import backtrader as bt
import datetime
import numpy as np 
import csv
from scipy import optimize
import sys
from setup_logger import logger
import matplotlib.pyplot as plt

logger.info('-----------------------------------------')
logger.info(' Buy at 30 day low and adjust the buy amount with days low hit')
logger.info('-----------------------------------------')


def xnpv(rate,cashflows):
    chron_order = sorted(cashflows, key = lambda x: x[0])
    t0 = chron_order[0][0]
    return sum([cf/(1+rate)**((t-t0).days/365.0) for (t,cf) in chron_order])

def xirr(cashflows,guess=0.1):
    return optimize.newton(lambda r: xnpv(r,cashflows),guess)

class MyStrategy(bt.Strategy):
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


    def next(self):
        # get the current date and time
        dt = self.datas[0].datetime.datetime()
        
        # check if at least 30 days have passed since the last buy order
        if len(self) >= 30:
            self.lowest_price = min(self.data.close.get(size=30))
            

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
            size = max((self.dayslowhit/30),1)*1000
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

    def stop(self):
        # export the buy array to CSV
        self.buy_array.append([self.datas[0].datetime.datetime().date(),float(self.broker.getvalue())])
#         with open('buy_transactions.csv', 'w', newline='') as f:
#             writer = csv.writer(f)
#             writer.writerows(self.buy_array)
        
        self.xirr = round(xirr(np.array(self.buy_array),guess=0.1)*100,1)
        logger.info('Overall XIRR, %.2f' % self.xirr)

if __name__ == '__main__':
    # create a cerebro entity
    cerebro = bt.Cerebro()
    cerebro.addobserver(bt.observers.DrawDown)

    # add a strategy
    cerebro.addstrategy(MyStrategy)

    # create a data feed
    data = bt.feeds.GenericCSVData(
        dataname=sys.argv[1],
        #fromdate=datetime.datetime(1900, 1, 1),
        #todate=datetime.datetime(2199, 1, 1),
        nullvalue=0.0,
        dtformat=('%Y-%m-%d'),
        datetime=0,
        high=-1,
        low=-1,
        open=-1,
        close=1,
        volume=-1,
        openinterest=-1
    )

    # add the data feed to cerebro
    cerebro.adddata(data)

    # set our desired cash start
    cerebro.broker.setcash(100000.0)

    # add the analyzer
    cerebro.addanalyzer(bt.analyzers.AnnualReturn)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')    

    # print out the starting conditions
    logger.info('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # run over everything
    results = cerebro.run()

    # print out the final result
    logger.info('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Retrieve the drawdown analyzer object
    drawdown = results[0].analyzers.drawdown

    # Plot the drawdown chart
    #drawdown.plot()
    logger.info(drawdown.get_analysis())

    #cerebro.plot()


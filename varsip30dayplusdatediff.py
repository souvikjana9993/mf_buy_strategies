## buy at 30 day low and adjust the buy amount with number of days not bought
import backtrader as bt
import datetime
import numpy as np 
from scipy import optimize
import numpy as np

def xnpv(rate,cashflows):
    chron_order = sorted(cashflows, key = lambda x: x[0])
    t0 = chron_order[0][0]
    return sum([cf/(1+rate)**((t-t0).days/365.0) for (t,cf) in chron_order])

def xirr(cashflows,guess=0.1):
    return optimize.newton(lambda r: xnpv(r,cashflows),guess)

class MyStrategy(bt.Strategy):
    def __init__(self):
        self.lowest_price = None
        self.buy_date = datetime.datetime(2013, 1, 2)
        self.dataclose = self.datas[0].close
        self.buy_count = 0
        self.total_deposits = 0
        self.buy_array = [[self.datas[0].datetime.datetime().date(),float(-self.broker.getvalue())]]
        
    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def next(self):
        # get the current date and time
        dt = self.datas[0].datetime.datetime()
        
        # check if at least 30 days have passed since the last buy order
        if len(self) >= 30:
            self.lowest_price = min(self.data.close.get(size=30))

        # if the current price is equal to the 30-day low price, buy the mutual fund
        if self.data.close[0] == self.lowest_price:
            size = max(((dt - self.buy_date).days/30),1)*1000
            self.buy(size=1000/self.data.close[0])
            self.buy_date = dt
            self.buy_count += 1
            self.total_deposits +=size
            self.buy_array.append([dt.date(),float(-size)])
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.log('Buy Orders Created: %d' % self.buy_count)
            self.log('Total Deposits: %.2f' % (self.total_deposits+100000))

        # log
        self.log('Close, %.2f' % self.dataclose[0])
        self.log('value, %.2f' % self.broker.getvalue())

    def stop(self):
        # export the buy array to CSV
        self.buy_array.append([self.datas[0].datetime.datetime().date(),float(self.broker.getvalue())])
#         with open('buy_transactions.csv', 'w', newline='') as f:
#             writer = csv.writer(f)
#             writer.writerows(self.buy_array)
        
        self.xirr = round(xirr(np.array(self.buy_array),guess=0.1)*100,1)
        self.log('Overall XIRR, %.2f' % self.xirr)
        
        
if __name__ == '__main__':
    # create a cerebro entity
    cerebro = bt.Cerebro()

    # add a strategy
    cerebro.addstrategy(MyStrategy)

    # create a data feed
    data = bt.feeds.GenericCSVData(
        dataname='mf_data.csv',
        fromdate=datetime.datetime(2013, 1, 2),
        todate=datetime.datetime(2022, 12, 14),
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

    # print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # run over everything
    results = cerebro.run()

    # print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
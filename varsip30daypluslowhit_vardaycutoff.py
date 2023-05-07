## buy at 30 day low and adjust the buy amount with days low hit
import backtrader as bt
import datetime
import numpy as np 
import csv
from scipy import optimize
import sys
from setup_logger import logger
import matplotlib.pyplot as plt
from utils import *
from strategies import *

logger.debug('-----------------------------------------')
logger.debug(' Buy at 30 day low and adjust the buy amount with days low hit')
logger.debug('-----------------------------------------')



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
    logger.debug('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # run over everything
    results = cerebro.run()

    # print out the final result
    logger.debug('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Retrieve the drawdown analyzer object
    drawdown = results[0].analyzers.drawdown

    # Plot the drawdown chart
    #drawdown.plot()
    logger.debug(drawdown.get_analysis())

    #cerebro.plot()


import numpy as np
import pandas as pd
from mftool import Mftool
import time
import requests
import json
from datetime import datetime
from functools import cache


mf = Mftool()
scheme_code_list = ['147662','125497','120505','122639','118834','119364','118759','135781','120662','119727','119775','119212','120692','140243','118285','145552','148704']


@cache
def get_nav(schemecode):
    try:
        df= mf.get_scheme_historical_nav(schemecode,as_Dataframe=True)
        df['schemeID'] = schemecode
        df['schemeName'] = mf.get_scheme_details(schemecode)['scheme_name']
        nav_data = df.copy()
        nav_data['nav'] = nav_data['nav'].astype(float)
        nav_data.index = pd.to_datetime(nav_data.index,format="%d-%m-%Y")
        nav_data = nav_data.sort_index()
        return df,nav_data
    except:
        pass

def lowest_in_last_nav_window(df):
    output_nav= []
    date = (df.nav.astype('float').iloc[1:][df.nav.astype('float').iloc[1:] < float(df.nav[0])].index[0])
    days_low = (pd.Timestamp.today().date() - datetime.strptime(date, '%d-%m-%Y').date()).days
    if days_low >= 10:
        output_nav.append(str(df.schemeName[0] + ' hit ' + str(days_low) + ' days low! and SIP mutliplication factor is ' + str(round(max((days_low/30),1),2))))
    return output_nav

def lowest_in_last_nav_window_schemecodelist(schemecodelist):
    output= []
    for i in schemecodelist:
        df = get_nav(i)[0]
        output.append("".join(lowest_in_last_nav_window(df)))
    return output

def sma_bb(schemecode,window,stdmultiplier):
    df = get_nav(schemecode)[1]
    sma = df['nav'].rolling(window = window).mean()
    std = df['nav'].rolling(window = window).std()
    df['upper_bb'] = sma + std * stdmultiplier
    df['lower_bb'] = sma - std * stdmultiplier
    return df

def implement_bb_strategy(schemecode,window,stdmultiplier):
    buy_price = []
    sell_price = []
    bb_signal = []
    signal = 0
    data_f = sma_bb(schemecode,window,stdmultiplier)
    lower_bb = data_f['lower_bb'] 
    upper_bb = data_f['upper_bb'] 
    data = data_f['nav']
    for i in range(len(data)):
        if data[i-1] > lower_bb[i-1] and data[i] < lower_bb[i]:
            if signal != 1:
                buy_price.append(data[i])
                sell_price.append(np.nan)
                signal = 1
                bb_signal.append(signal)
            else:
                buy_price.append(np.nan)
                sell_price.append(np.nan)
                bb_signal.append(0)
        elif data[i-1] < upper_bb[i-1] and data[i] > upper_bb[i]:
            if signal != -1:
                buy_price.append(np.nan)
                sell_price.append(data[i])
                signal = -1
                bb_signal.append(signal)
            else:
                buy_price.append(np.nan)
                sell_price.append(np.nan)
                bb_signal.append(0)
        else:
            buy_price.append(np.nan)
            sell_price.append(np.nan)
            bb_signal.append(0)
            
    return buy_price, sell_price, bb_signal,data_f['schemeName'].unique()[0]

def bb_strategy_push_trigger(schemecodelist,window,stdmultiplier):
    output = []
    for i in schemecodelist:
        b_price,s_price,b_signal,schemename = implement_bb_strategy(str(i),window,stdmultiplier)
        if b_signal[-1] > 0:
            output.append('Bollinger Band buy signal for '+ schemename + ' at ' + str(b_price[-1]))
            #return pushbullet_noti("",'Bollinger Band buy signal for '+ schemename + ' at ' + str(b_price[-1]))
        else:
            pass
    return output


def push_notifications(request):
    lowhittriggers = lowest_in_last_nav_window_schemecodelist(scheme_code_list)
    lowhittriggers = [x for x in lowhittriggers if x]
    for i in lowhittriggers:
        if lowhittriggers:
            msg = {"type": "note", "title": "MF Trigger", "body": i}
            resp = requests.post('https://api.pushbullet.com/v2/pushes',
                                 data=json.dumps(msg),
                                 headers={'Authorization': 'Bearer ' + 'o.xYPYN53luq4BAEHawajtgwQmz424IEdN',
                                          'Content-Type': 'application/json'})
    bb_strategyoutput = bb_strategy_push_trigger(scheme_code_list,20,2)
    for i in bb_strategyoutput:
        if bb_strategyoutput:
            msg = {"type": "note", "title": "MF Trigger", "body": bb_strategyoutput}
            resp = requests.post('https://api.pushbullet.com/v2/pushes',
                                 data=json.dumps(msg),
                                 headers={'Authorization': 'Bearer ' + 'o.xYPYN53luq4BAEHawajtgwQmz424IEdN',
                                          'Content-Type': 'application/json'})
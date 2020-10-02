import yfinance as yf
import pandas as pd
import os
from datetime import date, timedelta, datetime
from time import gmtime, strftime
import numpy as np
import collections
import glob

today = date.today()
today_str = today.strftime("%Y-%m-%d")

# Get list of directory containing list of tickers we want to gather calls and puts from
pathDirs = f'{os.path.dirname(__file__)}/Calls_and_puts'
pathDirs_today = f'{pathDirs}/{today}'
listOfTickers = ["PLUG", "AAPL", "APPL", "TSLA"]

# Creating empty dictionnaries that are going to store the weighted open interests
DictOpenInterest_Call = collections.defaultdict(list)
DictOpenInterest_Put = collections.defaultdict(list)

def DL_calls_and_puts(ticker):
    try:
        fin = yf.Ticker(ticker)    
        print(ticker)
        first_date = fin.options[1]     # fin.options = List of strike dates
        opt = fin.option_chain(first_date)
        calls = opt.calls
        puts = opt.puts
        calls.to_csv(f'{pathDirs}/{today}/{ticker}_{today}_calls.csv')
        puts.to_csv(f'{pathDirs}/{today}/{ticker}_{today}_puts.csv')
    except IndexError:
        print(f"IndexError for {ticker} (options informations probably unavailable)")
        pass



 
def List_of_Calls_and_Puts():
    """
    Goes in pathDirs_today and creates two lists
    """
    extension = 'csv'
    os.chdir(pathDirs_today)
    # glob gets us a list of all the csv files contained in the current directory
    csvs = glob.glob('*.{}'.format(extension)) 
    calls = [calls for calls in csvs if "_calls" in calls]
    puts = [puts for puts in csvs if "_puts" in puts]
    return calls, puts

def calculate_weighted_interest():
    
    calls, puts = List_of_Calls_and_Puts()
    for tickCall in calls:
        # Calls
        df = pd.read_csv(f'{pathDirs_today}/{tickCall}')
        symbol = str(tickCall.split('_')[0])
        date = str(tickCall.split('_')[1])

        CallsNotInMoney = df.loc[df["inTheMoney"] == False]
        Ncontracts = CallsNotInMoney['contractSymbol'].size
        openInterest = CallsNotInMoney['openInterest']
        # Get coefficients
        x=1
        r = list(range(1,Ncontracts+1,1))
        # Let's suppose we have 17 contacts above the currrent price (in money)
        # We give a bigger weight to the contracts that aim a higher price
        # the coefficients to choose are open to discussion
        # Actually, the optimal calibration of the model should be statistically verified
        # in a further back-test
        coefficients = [int(x**2+x-(x/2)) for x in r if x >=2]
        coefficients = np.array([x]+coefficients)
        CallsNotInMoney["weightedInterest"] = coefficients * openInterest.to_numpy()
        colSum = float(CallsNotInMoney['weightedInterest'].sum())
        DictOpenInterest_Call["Ticker"].append(symbol)
        DictOpenInterest_Call["SumOpenInterest_Call"].append(colSum)
        DictOpenInterest_Call["Date"].append(date)

    for tickPut in puts:
        # Puts
        df = pd.read_csv(f'{pathDirs_today}/{tickPut}')
        symbol = str(tickPut.split('_')[0])
        date = str(tickPut.split('_')[1])

        PutsNotInMoney = df.loc[df["inTheMoney"] == False]
        Ncontracts = PutsNotInMoney['contractSymbol'].size
        openInterest = PutsNotInMoney['openInterest']
        # Get coefficients
        x=1
        r = list(range(1,Ncontracts+1,1))
        coefficients = [int(x**2+x-(x/2)) for x in r if x >=2]
        coefficients = np.array([x]+coefficients)[::-1]
        weighted = coefficients * PutsNotInMoney["openInterest"]
        PutsNotInMoney["weightedInterest"] = pd.Series(weighted)
        colSum = float(PutsNotInMoney['weightedInterest'].sum())
        DictOpenInterest_Put["Ticker"].append(symbol)
        DictOpenInterest_Put["SumOpenInterest_Put"].append(colSum)
        DictOpenInterest_Put["Date"].append(date)



def dict_to_DF():
    CallDF = pd.DataFrame.from_dict(DictOpenInterest_Call)
    PutDF = pd.DataFrame.from_dict(DictOpenInterest_Put)
    CallDF = CallDF.set_index(['Date','Ticker'])
    PutDF = PutDF.set_index(['Date','Ticker'])
    CallPutDF = pd.merge(CallDF, PutDF,how="left", on=["Date","Ticker"])
    CallPutDF['CallPut_Ratio'] = CallDF['SumOpenInterest_Call'] / PutDF['SumOpenInterest_Put']
 
 
    print(CallDF)
    print(PutDF)
    print(CallPutDF)


def main():
    if not os.path.exists(pathDirs):
        os.mkdir(pathDirs)
    if not os.path.exists(pathDirs_today):
        os.mkdir(pathDirs_today)
    for ticker in listOfTickers:
        DL_calls_and_puts(ticker)
    calculate_weighted_interest()
    dict_to_DF()



if __name__ == "__main__":
    main()


 


"""
# CALCULATION OF THE EVOLUTION OF WEIGHTED PUT/CALL RATIO
 
# Get DISTINCT values of indexes into Series
indexTickers = CallDF.index.levels[1].to_series().reset_index(name='na')['Ticker']
indexDates = CallDF.index.levels[0].to_series().reset_index(name='na')['Date']
 
# Evolution (%) from T0 to T1 (25 to 26)
evol = ((CallPutDF.loc[[f"{indexDates[1]}"]]['CallPut_Ratio'].to_numpy() - \
    CallPutDF.loc[[f"{indexDates[0]}"]]['CallPut_Ratio'].to_numpy()) / \
    CallPutDF.loc[[f"{indexDates[0]}"]]['CallPut_Ratio'].to_numpy() )
evol = pd.Series(evol)
# Concatenate series
DFevolutions = pd.concat([indexTickers, evol], axis=1)
DFevolutions.rename(columns={DFevolutions.columns[1]:f'{indexDates[0]} to {indexDates[1]}'}, inplace=True)
 
sizeIndexDates = indexDates.size
"""
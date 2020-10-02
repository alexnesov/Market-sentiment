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

listOfTickers = ["PLUG", "AAPL", "APPL", "TSLA"]


def get_calls_and_puts(ticker):
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


# Creating empty dictionnaries
DictOpenInterest_Call = collections.defaultdict(list)
DictOpenInterest_Put = collections.defaultdict(list)
 
for i in dirs:
    # Get list of tickers for which we want the calls

"""     extension = 'csv'
    os.chdir(path)
    csvs = glob.glob('*.{}'.format(extension)) """
    calls = [calls for calls in csvs if "_calls" in calls]
    puts = [puts for puts in csvs if "_puts" in puts]
 
    for tickCall in calls:
        # Calls
 
        df = pd.read_csv(f'C:\\Users\\alexa\\OneDrive\\Desktop\\Finviz downloads\\STRAT 1_21_05_2020\\{i}\\{tickCall}')
        symbol = str(tickCall.split('_')[0])
        date = str(tickCall.split('- ')[1]).replace(' ', '')
 
        CallsNotInMoney = df.loc[df["inTheMoney"] == False]
        Ncontracts = CallsNotInMoney['contractSymbol'].size
        openInterest = CallsNotInMoney['openInterest']
        # Get coefficients
        x=1
        r = list(range(1,Ncontracts+1,1))
        coefficients = [int(x**2+x-(x/2)) for x in r if x >=2]
        coefficients = np.array([x]+coefficients)
        CallsNotInMoney["weightedInterest"] = coefficients * openInterest.to_numpy()
        colSum = float(CallsNotInMoney['weightedInterest'].sum())
        DictOpenInterest_Call["Ticker"].append(symbol)
        DictOpenInterest_Call["SumOpenInterest_Call"].append(colSum)
        DictOpenInterest_Call["Date"].append(date)
 
    for tickPut in puts:
        # Puts
        df = pd.read_csv(f'C:\\Users\\alexa\\OneDrive\\Desktop\\Finviz downloads\\STRAT 1_21_05_2020\\{i}\\{tickPut}')
        symbol = str(tickPut.split('_')[0])
        date = str(tickPut.split('- ')[1]).replace(' ', '')
 
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
 


def main():
    if not os.path.exists(pathDirs):
        os.mkdir(pathDirs)
    if not os.path.exists(f"{pathDirs}/{today}")
        os.mkdir(f"{pathDirs}/{today}")
    for ticker in listOfTickers:
        get_calls_and_puts(ticker)




if __name__ == "__main__":
    main()


 
#Making proper dataframes
CallDF = pd.DataFrame.from_dict(DictOpenInterest_Call)
PutDF = pd.DataFrame.from_dict(DictOpenInterest_Put)
 
CallDF['Date'] = CallDF['Date'].str.replace('.csv','')
PutDF['Date'] = PutDF['Date'].str.replace('.csv','')
CallDF = CallDF.set_index(['Date','Ticker'])
PutDF = PutDF.set_index(['Date','Ticker'])
 
CallPutDF = pd.merge(CallDF, PutDF,how="left", on=["Date","Ticker"])
CallPutDF['CallPut_Ratio'] = CallDF['SumOpenInterest_Call'] / PutDF['SumOpenInterest_Put']
 
 
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

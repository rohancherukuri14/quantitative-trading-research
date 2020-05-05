import yfinance as yf
import tkinter
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import pandas as pd
import quandl
import math
from sklearn import preprocessing, cross_validation, svm
from sklearn.linear_model import LinearRegression
import numpy as np
from datetime import datetime, date, timedelta

auth_tok = 'KYB9U1FCx7EU6wAxteKF'

inflation = pd.read_excel("inflation_data.xls")

gdp = pd.read_excel("GDP_1.xls")

def findSimilarNasdaqIndexDates():
    tickerSymbol = '^IXIC'

    tickerData = yf.Ticker(tickerSymbol)

    tickerDf = tickerData.history(interval='1mo', start='1980-01-01', end = '2020-03-02')

    startDate = str(tickerDf.index.values[0])[0:10]
    
    startIndex = inflation.loc[inflation['observation_date'] == startDate].index.values[0]

    endIndex = len(inflation) - 1

    dates = []

    currentIndexValue = tickerDf.Open.iat[-1]

    currentCpi = inflation.CPIAUCNS.iat[-1]

    for i in range(0, endIndex-startIndex + 1):
        date = inflation.iloc[i+startIndex, 0]
        cpi = inflation.iloc[i+startIndex, 1]
        indexValue = tickerDf.iloc[i, 0]
        adjustedValue = (currentCpi/cpi) * indexValue
        percentDifference = (abs(adjustedValue - currentIndexValue) / currentIndexValue) * 100
        if percentDifference < 10:
            dates.append(date)

    return dates

def findSimilarDOWToGDPRatios():
    
    tickerSymbol = '^DJI'

    tickerData = yf.Ticker(tickerSymbol)

    tickerDf = tickerData.history(interval='3mo', start='1980-01-01', end = '2019-10-01')

    startDate = str(tickerDf.index.values[0])[0:10]
    
    startIndex = gdp.loc[gdp['observation_date'] == startDate].index.values[0]

    endIndex = len(gdp) - 1

    dates = []

    currentIndexValue = tickerDf.Open.iat[-1]

    currentGDP = gdp.GDP.iat[-1]

    currentRatio = currentIndexValue / currentGDP

    for i in range(0, endIndex-startIndex + 1):
        date = gdp.iloc[i+startIndex, 0]
        gdp_value = gdp.iloc[i+startIndex, 1]
        indexValue = tickerDf.iloc[i, 0]
        ratio = indexValue / gdp_value
        percentDifference = (abs(ratio - currentRatio) / currentRatio) * 100
        if percentDifference < 10:
            dates.append(date)

    return dates


def stockGraphRegression(stockSymbol):
    tickerData = yf.Ticker(stockSymbol)

    df = tickerData.history(interval='1d', start='2001-01-01', end = '2020-04-17')

    df = df[['Open',  'High',  'Low',  'Close', 'Volume']]

    df['HL_PCT'] = (df['High'] - df['Low']) / df['Close'] * 100.0
    df['PCT_change'] = (df['Close'] - df['Open']) / df['Open'] * 100.0

    df = df[['Close', 'HL_PCT', 'PCT_change', 'Volume']]
    forecast_col = 'Close'
    df.fillna(value=-99999, inplace=True)
    forecast_out = int(math.ceil(0.01 * len(df)))
    df['label'] = df[forecast_col].shift(-forecast_out)

    X = np.array(df.drop(['label'], 1))
    X = preprocessing.scale(X)
    X_lately = X[-forecast_out:]
    X = X[:-forecast_out]

    df.dropna(inplace=True)

    y = np.array(df['label'])

    X_train, X_test, y_train, y_test = cross_validation.train_test_split(X, y, test_size=0.2)
    clf = LinearRegression(n_jobs=-1)
    clf.fit(X_train, y_train)
    confidence = clf.score(X_test, y_test)

    print(confidence)

    forecast_set = clf.predict(X_lately)
    df['Forecast'] = np.nan

    last_date = df.iloc[-1].name
    last_unix = last_date.timestamp()
    one_day = 86400
    next_unix = last_unix + one_day

    for i in forecast_set:
        next_date = datetime.fromtimestamp(next_unix)
        next_unix += 86400
        df.loc[next_date] = [np.nan for _ in range(len(df.columns)-1)]+[i]

    df['Close'].plot()
    df['Forecast'].plot()
    plt.legend(loc=4)
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.show()

def graphSimpleMovingAverage(stockSymbol, startDate, period):
    currentDate = str(date.today())

    tickerData = yf.Ticker(stockSymbol)

    tickerDf = tickerData.history(interval='1d', start=startDate, end = currentDate)

    movingAverage = tickerDf['Close'].rolling(window=period).mean()

    movingAverage.plot()
    tickerDf['Close'].plot()
    plt.show()

def getAllSimpleMovingAverages(stockSymbol, startDate):
    currentDate = str(date.today())

    startDate1 = datetime.strptime(startDate, "%Y-%m-%d") - timedelta(500)
    tickerData = yf.Ticker(stockSymbol)

    tickerDf = tickerData.history(interval='1d', start=startDate1, end = currentDate)

    tickerDf['10 Day Moving Average'] = tickerDf['Close'].rolling(window=10).mean()
    tickerDf['20 Day Moving Average'] = tickerDf['Close'].rolling(window=20).mean()
    tickerDf['50 Day Moving Average'] = tickerDf['Close'].rolling(window=50).mean()
    tickerDf['100 Day Moving Average'] = tickerDf['Close'].rolling(window=100).mean()
    tickerDf['200 Day Moving Average'] = tickerDf['Close'].rolling(window=200).mean()

    return tickerDf

def graphAllSimpleMovingAverages(stockSymbol, startDate):
    
    currentDate = str(date.today())

    tickerDf = getAllSimpleMovingAverages(stockSymbol, startDate)

    tickerDf['10 Day Moving Average'].loc[startDate:currentDate].plot()
    tickerDf['20 Day Moving Average'].loc[startDate:currentDate].plot()
    tickerDf['50 Day Moving Average'].loc[startDate:currentDate].plot()
    tickerDf['100 Day Moving Average'].loc[startDate:currentDate].plot()
    tickerDf['200 Day Moving Average'].loc[startDate:currentDate].plot()
    tickerDf['Close'].loc[startDate:currentDate].plot()
    plt.legend()

    plt.show()

def calculateExponentialMovingAverage(stockSymbol, period):
    currentDate = str(date.today())
    date200DaysAgo = str(date.today() - timedelta(days=period+1))

    tickerData = yf.Ticker(stockSymbol)

    tickerDf = tickerData.history(interval='1d', start=date200DaysAgo, end = currentDate)

    print(tickerDf['Close'])

    ema = tickerDf['Close'].ewm(span=period, adjust=False).mean()

    print(ema)

def getRegime(stockSymbol, sma1, sma2, startDate):
    currentDate = str(date.today())
    averagesDf = getAllSimpleMovingAverages(stockSymbol, startDate)

    labelString = 'Difference Between ' + sma1 + ' and ' + sma2
    averagesDf[labelString] = averagesDf[sma1] - averagesDf[sma2]
    averagesDf['Regime'] = np.where(averagesDf[labelString] > 0, 1, 0)
    averagesDf['Regime'] = np.where(averagesDf[labelString] < 0, -1, averagesDf['Regime'])

    averagesDf['Regime'].loc[startDate:currentDate].plot()

    plt.show()



# # print(findSimilarNasdaqIndexDates())
# print(findSimilarDOWToGDPRatios())

stockGraphRegression('AAPL')

# calculateExponentialMovingAverage('AAPL', 5)
# getRegime('AAPL', '20 Day Moving Average', '50 Day Moving Average', '2018-1-1')





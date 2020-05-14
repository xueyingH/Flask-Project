# -*- coding: utf-8 -*-
"""
Created on Tue Apr 21 14:57:17 2020

@author: etill
"""

#import statements
import pandas as pd
import numpy as np
import datetime
import yfinance as yf
from yahooquery import Ticker
from pandas_datareader import data as pdr
import matplotlib.pyplot as plt
import seaborn as sns
import os
from flask import Flask, render_template, request


url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
sp500_df = pd.read_html(url, header = 0)[0]
sp500_df.set_index('Symbol', inplace = True)

#Flask app variable
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# A function that plots total stock price return of each stock
def create_returnfig(stock_prices):
        df = stock_prices.iloc[-1,:].sub(stock_prices.iloc[0,:]).sub(1).mul(100).sort_values()
        plt.barh(df.keys(), df.get_values(), align='center', alpha=0.5)
        plt.savefig('static/images/return.png')
        plt.close()
        return
    
def create_capfig(mkt_cap):
        mkt_change = pd.concat([mkt_cap.iloc[0], mkt_cap.iloc[-1]], axis =1)
        mkt_change.columns = mkt_change.columns.date
        mkt_change.plot(kind = 'barh')
        plt.savefig('static/images/mkt_cap.png')
        plt.close()
        return
    
def create_index(mkt_cap_index):
        mkt_cap_index.plot()
        plt.savefig('static/images/index.png')
        plt.close()
        return

def compare_index(index_df):
        index_df.plot()
        plt.savefig('static/images/multi_index.png')
        plt.close()
        return
    
# Create multi_period_return function
def multi_period_return(r):
    return (np.prod(r + 1) - 1) * 100

def index_return(rolling_return_360):
        rolling_return_360.dropna().plot()
        plt.savefig('static/images/index_return.png')
        plt.close()
        return

def stock_corr(daily_return):
        # Plot a heatmap of daily return correlations
        sns.heatmap(daily_return.corr(), annot = True)
        plt.savefig('static/images/stock_corr.png')
        plt.close()
        return
        

#static route
@app.route("/")
def hello():
    return render_template("index.html")

@app.route("/person")
def intro():
    return render_template("personal.html")

portfolio = []
@app.route("/project", methods = ["GET", "POST"])
def selectStock():
    if request.method == "POST":
        stock = request.form.get("stock")
        portfolio.append(stock)
    stock_df = sp500_df.loc[portfolio].reset_index()
    tables = [stock_df.to_html(classes='data', header="true")]
    
    return render_template("project.html", tables = tables)

@app.route('/result')
def getChart():
    yf.pdr_override()
    companies = ' '.join(portfolio)
    # Download the S&P 500 and Dow Jones Industrial Average as benchmarks
    benchmark = pdr.get_data_yahoo('^GSPC ^DJI', start = "2014-01-02", end ="2020-05-01")['Close']
    benchmark.columns = ['DJI', 'SP500']
    # Download close price of stocks in portfolio
    stock_prices = pdr.get_data_yahoo(companies, start="2014-01-02", end="2020-05-01")['Close']
    # Download current market capitalization and calculate outstanding stock shares
    mkt_cap_current = [Ticker(x).price[x]['marketCap'] for x in portfolio]
    mkt_cap_current = np.array(mkt_cap_current)
    current_price = stock_prices.iloc[-1]
    shares = mkt_cap_current/current_price
    mkt_cap = stock_prices.mul(shares)
    # Construct a index for portfolio according to market cap
    raw_index = mkt_cap.sum(axis =1)
    mkt_cap_index = raw_index.div(raw_index[0]).mul(100)
    # Normalize the benchmark
    benchmark_index = benchmark.div(benchmark.iloc[0]).mul(100)
    index_df = pd.concat([mkt_cap_index, benchmark_index], axis =1)
    index_df = index_df.rename(columns = {0:'Portfolio'})
    # Calculate rolling_return_360
    rolling_return_360 = index_df.pct_change().rolling('360D').apply(multi_period_return)
    # Calculate the daily return of each stock in my portfolio
    daily_return = stock_prices.pct_change()
    
    
    create_returnfig(stock_prices)
    create_capfig(mkt_cap)
    create_index(mkt_cap_index)
    compare_index(index_df)
    index_return(rolling_return_360)
    stock_corr(daily_return)
    
    return render_template("result.html")

@app.after_request
def add_header(response):
    # response.cache_control.no_store = True
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

#start the server
if __name__ == "__main__":
    app.run()
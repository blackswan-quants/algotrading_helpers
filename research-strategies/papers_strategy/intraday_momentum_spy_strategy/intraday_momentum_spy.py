# strategy taken from "Beat the Market An Effective Intraday Momentum Strategy for S&P500 ETF (SPY)"

import os
import requests
import time
import pandas as pd
from   datetime import datetime
import numpy as np
import pytz
import math
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from   matplotlib.ticker import FuncFormatter
import statsmodels.api as sm
from polygon_helpers import *

# step 1: initiate the backtest
ticker = 'SPY'
from_date = '2022-05-09'
until_date = '2024-04-22'

spy_intra_data = fetch_polygon_data(ticker, from_date, until_date, 'minute')
spy_daily_data = fetch_polygon_data(ticker, from_date, until_date, 'day')
dividends      = fetch_polygon_dividends(ticker)

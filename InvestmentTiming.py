import yfinance as yf
import pandas as pd
import random
import matplotlib.pyplot as plt
import numpy as np
import os
from pathlib import Path



def investSubannually(tradingDays, yearlyInvestment, startYear, endYear, timesPerYear):
  """
  Creates dictionary of trading days and shares purchased on that day, given some constant yearly investment  dollar amount
  timesPerYear is an int, such that 12%times == 0, for example an investor that invests quarterly will have this
  set to 4. The Investments are made inclusive of years startYear and endYear.
  If there are no trading dates on the tradingMonth then the investor will trade on the following month (e.g. if there are no
  trade days for October, then the investor will try to trade on November, then December).
  If there are no trading days on months for the rest of the year then the investor doesn't trade and the programs fails
  NOTE: this shouldn't happen ever, if it does there is a data integrity error in the tradingDays dictionary

  :param tradingDays: Dictionary of days and share prices, presumed to be the first trading day of each month over a span that includes StartYear and EndYear
  :param yearlyInvestment: dollar amount to trade per year
  :param startYear: year that the investor started trading
  :param endYear: year that the investor stopped trading
  :param timesPerYear: how many times per year this investor invests, this will always assume 12%times == 0
  :return: dictionary and float. Dict of {date:shares} which represents the shares purchased on that date. Float is total number of held shares
  """

  # initialize the return variables
  heldShares = {}  # dictionary, will store investment holdings for the investor that only invests once per year
  totalShares = 0  # stores the total number of shares held by the investor

  # calculate which month this investor starts investing on
  # if an investor invests 4 times per year, then they would invest in march, june, sept, and dec. They DO NOT invest in Jan
  monthSpan = round(12 / timesPerYear)   # if investor invests 4 times per year, then span is 3 = 12 / 4
  monthInvested = 0
  errorMonth = 0
  monthInvestment = yearlyInvestment / timesPerYear

  # for each year in the range provided in the arguments
  for yearInvested in range(startYear, endYear + 1):

    # restart some variables each year
    errorMonth = 0
    monthInvested = 0

    # starts at 0 and executes up to timesPerYear times.
    # Example 0,1,2,3 for "timesPerYear = 4"
    for event in range(timesPerYear):

      # increments the current month investing in by span of months between events
      # ex: if monthInvested = 0 it means we haven't invested yet, and monthSpan = 3 it means we invest 4 times a year
      # timesPerYear = 4
      monthInvested = monthInvested + monthSpan
      errorMonth = monthInvested  # will be unused unless dateKey is notFound

      # # debug point
      # print ("attempting to write for mo / year: " + str(yearInvested) + "//" + str(monthInvested) + "// error month: " + str(errorMonth))

      # Get date key for the first trading day that this investor trades on month
      dateKey = get_first_marketday(tradingDays, yearInvested, monthInvested)

      # ERROR HANDLING - if no date in month found then have the yearly investor invest their sum the following month.
      while dateKey == "notFound":
        errorMonth += 1  # increment the attempted month by 1
        if errorMonth == 13:  # if we've incremented past calendar months in this year then exit program and print error
          print("ERROR: no months for year invested. Exiting program")
          exit()

        print("key not found in share price dictionary")
        dateKey = get_first_marketday(tradingDays, yearInvested, errorMonth)  # try again next month

      # convert investment amount to number of shares
      sp500_value = tradingDays[dateKey]  # get price per single share of SP500
      shares = investment_to_shares(monthInvestment, sp500_value)  # convert price to number shares

      # update investors shares held
      heldShares[dateKey] = shares
      totalShares = totalShares + shares

  # after iterating across all investment years and months, return dictionary of shares purchased and total shares count
  return heldShares, totalShares

def investYearly(tradingDays, yearlyInvestment, startYear, endYear, tradingMonth=1):
  """
  Creates dictionary of trading days and shares purchased on that day, given some constant yearly investment dollar amount
  Trading month is the month that the investor trades in each year, if it is -1 then the investor will trade on a random
  month each year that they trade. The Investments are made inclusive of years startYear and endYear.
  If there are no trading dates on the tradingMonth then the investor will trade on the following month (e.g. if there are no
  trade days for October, then the investor will try to invest double in November, then triple in December)
  If there are no trading days on months for the rest of the year then the investor doesn't trade and the programs fails
  NOTE: this shouldn't happen ever, if it does there is a data integrity error in the tradingDays dictionary

  :param tradingDays: Dictionary of days and share prices, presumed to be the first trading day of each month over a span that includes StartYear and EndYear
  :param yearlyInvestment: dollar amount to trade per year
  :param startYear: year that the investor started trading
  :param endYear: year that the investor stopped trading
  :param tradingMonth: The month that the yearly investor trades on each year.
  :return: dictionary and float. Dict of {date:shares} which represents the shares purchased on that date. Float is total number of held shares
  """

  # initialize the return variables
  heldShares = {}  # dictionary, will store investment holdings for the investor that only invests once per year
  totalShares = 0  # stores the total number of shares held by the investor


  # for each year in the range provided in the arguments
  for yearInvested in range(startYear, endYear + 1):

    # if trading month is -1 that indicates we want to trade on random months every year
    if tradingMonth == -1:
      mon = random.randint(1, 12)
    else :
      mon = tradingMonth

    # Get date key for the first trading day that this investor trades on each year
    dateKey = get_first_marketday(tradingDays, yearInvested, mon)

    # ERROR HANDLING - if no date in month found then have the yearly investor invest their sum the following month.
    while dateKey == "notFound":
      tradingMonth += 1  # increment the attempted month by 1
      if tradingMonth == 13:  # if we've incremented past calendar months in this year then exit program and print error
        print("ERROR: no months for year invested. Exiting program")
        exit()

      print("key not found in share price dictionary")
      dateKey = get_first_marketday(tradingDays, yearInvested, mon)  # try again next month

    # convert investment amount to number of shares
    sp500_value = tradingDays[dateKey]  # get price per single share of SP500
    shares = investment_to_shares(yearlyInvestment, sp500_value)  # convert price to number shares

    # update investors shares held
    heldShares[dateKey] = shares  # update yearly investors holdings
    totalShares = totalShares + shares

  return heldShares, totalShares


def share_purchases_to_portfolio_value (index_prices, purchases):
  """
  Creates a historical view of portfolio value in USD (not inflation adjusted) from a dictionary of share purchases and dates
  and the historical record of index values. All values are in Index Open Price. Forces output dictionary to have
  monthly portfolio values, even if purchases are made less frequently than monthly investments
  NOTE: purchases dates are assumed to exist in index_prices otherwise there will be an error
  :param index_prices: dictionary of monthly prices for the index
  :param purchases: dictionary of {date:shares_purchased}
  :return: dictionary of dates and portfolio values
  """

  dated_portfolio_values = {}
  portfolio_value = 0
  portfolio_held_shares = 0

  # for each date of purchases, append a new entry to the dated_portfolio_values dictionary
  for date in index_prices:
    # increase held shares by the date's purchase, if no purchase was made on date then increase total held by default value (0)
    portfolio_held_shares += purchases.get(date, 0)
    portfolio_value = portfolio_held_shares * index_prices.get(date)  # update portfolio value to be held shares * index value on date
    dated_portfolio_values[date] = portfolio_value  # grow dictionary by new entry

  return dated_portfolio_values



def investment_to_shares(investment, price):
  """
  Converts investment ($) into shares based on the asset price at some given time period
  :param investment: float, investment in dollars
  :param price: float, price per share
  :return: float, number of shares rounded to hundredths of a share
  """
  shares = investment / price
  return shares

def get_first_marketday(kl, yr, mo):
  """
  From a list of keys, gets the first key (thing in list) for the given year and month.
  Returns string "notFound" if no found, else returns the first key in list for the year and month.
  Year and month are passed as ints.
  not found
  :param kl: list of strings to search against, handles <class 'dict_keys'> input (e.g. someDictionary.keys())
  :param yr: int, year for search for
  :param mo: int, month to search for. Example 10 is October.
  :return: String, found match in list else "notFound"
  """

  # error handling - ignore invalid years or months
  if yr < 1920 or yr > 2024:
    print ("cannot pass invalid year: " + str(yr))
    return "notFound"
  if mo < 1 or mo > 12:
    print("cannot pass invalid month: " + str(mo))
    return "notFound"

  # if month is less than 10, then add a leading 0 to month
  if mo < 10:
    searchString = str(yr) + "-0" + str(mo) + "-"  # formats the string in format "yyyy-mm-"
  else:
    searchString = str(yr) + "-" + str(mo) + "-"   # formats the string in format "yyyy-mm-"

  # create a list of matches for the search string
  dateMatches = [index for index in kl if searchString in index]

  # if there are no matches, return error
  if len(dateMatches) < 1:
    print("No matches in keys list found for month:year " + str(mo) + ":" +str(yr))
    return "notFound"
  elif len(dateMatches) > 1:
    # if there are more than one matches, then just pick first match. List is assumed to be ordered
    return dateMatches[0]
  else:
    return dateMatches[0]




def get_index_data(index, starting_year = 1983):
  """
  Returns tuple which is a dictionary of the first trading day in each month of the raw data, starting at 'starting_year' and ending in 2025
  Uses Yahoo Finance to pull financial data from the index history. Dictionary are pairs of {'date':'price'} where
  price is the day's opening index price
  :param index: string, the index that will be pulled using Yahoo Finance API
  :param starting_year: Starting date of data, first date will be the first trading day of the first Jan available since this date
  :return: tuple: dictionary of {first trading days : prices}, first year in dictionary, raw data (pandas dataframe)
  """

  # error handling for argument: starting_year
  # passed year must be in range 1982:2025, and must be four characters
  if starting_year < 1983 or starting_year > 2024:
    print("Error loading data, starting year is invalid: {}".format(starting_year))
    exit()

  # load data using yahoo finance api
  raw_data = yf.download(index, start=(str(starting_year) + "-01-01"), end="2024-12-30")
  raw_data = raw_data.tz_localize(None)  # Remove timezone information

  dictionary_data = {} # initialize returned datastructure

  # Ensure the first year of data is a full year of data:
  # Data structure must start with the earliest trading day in Jan of each year that is available in the YF dataset
  earliest_year_in_data = raw_data.index.min().year  # raw_data is a pandas dataframe with TIMESTAMP as the index
  # if the earliest year of data does not begin with Jan, then skip that earliest year and proceed with
  # the next available full year of data
  if raw_data.index.min().month != 1:
    earliest_year_in_data += 1

  # iterates through valid years and all months in range (years)
  # if the dataset (raw_data) doesn't contain data for YEAR:MONTH then nothing is added
  # for year in range from starting_year to 2025
  for year in range(earliest_year_in_data, 2025):

    # for each month in range 1-12
    # attempt to write to the growing dictionary
    for month in range(1, 13):

      # Get the first business day of the month
      first_day = pd.to_datetime(f'{year}-{month}-01')

      # if the first date in trading month is a weekend then shift it to monday
      if first_day.weekday() >= 5:
        first_day += pd.Timedelta(days=7 - first_day.weekday())
      while first_day not in raw_data.index: # If it's a holiday, move to the next day
        first_day += pd.Timedelta(days=1)

      # Store the date and opening price
      # value (float) is open price from pandas series object
      dictionary_data[first_day.strftime('%Y-%m-%d')] = float(raw_data.loc[first_day]['Open'].iloc[0])

  return dictionary_data, earliest_year_in_data, raw_data


# def get_sp500_data():
#   """
#   Downloads historical S&P 500 data from Yahoo Finance and returns a dictionary
#   with the first trading day of each month and the opening price on that day.
#   """
#
#   sp500 = yf.download("^GSPC", start="1983-01-01", end="2024-12-14")
#   sp500 = sp500.tz_localize(None)  # Remove timezone information
#   sp500_data = {}
#
#   for year in range(1983, 2025):
#     for month in range(1, 13):
#       # Get the first business day of the month
#       first_day = pd.to_datetime(f'{year}-{month}-01')
#       if first_day.weekday() >= 5:  # Weekend, shift to next Monday
#         first_day += pd.Timedelta(days=7 - first_day.weekday())
#       while first_day not in sp500.index:  # If it's a holiday, move to the next day
#         first_day += pd.Timedelta(days=1)
#
#       # Store the date and opening price
#       sp500_data[first_day.strftime('%Y-%m-%d')] = float(sp500.loc[first_day]['Open'].iloc[0])  # get the float open price from pandas series object
#
#       ## debugging - print out values when appending to dictionary
#       # print(sp500.loc[first_day]['Open'])
#       # print(float(sp500.loc[first_day]['Open'].iloc[0]))
#
#       ## getting min date in dataframe:
#       ## sp500.index.min()
#
#   return sp500_data
#
#
# def get_QQQ_data():
#   """
#   Downloads historical TQQQ - High Beta Index data from Yahoo Finance and returns a dictionary
#   with the first trading day of each month and the opening price on that day.
#   """
#
#   tqqq = yf.download("TQQQ", start="1999-01-01", end="2024-12-14")
#   tqqq = tqqq.tz_localize(None)  # Remove timezone information
#   tqqq_data = {}
#
#   for year in range(1999, 2025):
#     for month in range(1, 13):
#       # Get the first business day of the month
#       first_day = pd.to_datetime(f'{year}-{month}-01')
#       if first_day.weekday() >= 5:  # Weekend, shift to next Monday
#         first_day += pd.Timedelta(days=7 - first_day.weekday())
#       while first_day not in tqqq.index:  # If it's a holiday, move to the next day
#         first_day += pd.Timedelta(days=1)
#
#       # Store the date and opening price
#       tqqq_data[first_day.strftime('%Y-%m-%d')] = float(tqqq.loc[first_day]['Open'].iloc[0])  # get the float open price from pandas series object
#
#   return tqqq_data
#
# def get_btc_data():
#   """
#   Downloads historical Bitcoin USD - data from Yahoo Finance and returns a dictionary
#   with the first trading day of each month and the opening price on that day.
#   """
#   btc = yf.download("BTC-USD", start="2015-01-01", end="2024-12-14")
#   btc = btc.tz_localize(None)  # Remove timezone information
#   btc_data = {}
#
#   for year in range(2011, 2025):
#     for month in range(1, 13):
#       # Get the first business day of the month
#       first_day = pd.to_datetime(f'{year}-{month}-01')
#       if first_day.weekday() >= 5:  # Weekend, shift to next Monday
#         first_day += pd.Timedelta(days=7 - first_day.weekday())
#       while first_day not in btc.index:  # If it's a holiday, move to the next day
#         first_day += pd.Timedelta(days=1)
#
#       # Store the date and opening price
#       btc_data[first_day.strftime('%Y-%m-%d')] = float(btc.loc[first_day]['Open'].iloc[0])  # get the float open price from pandas series object
#
#   return btc_data


def monteCarlo(earliest_year, index, yearly_investment, iterations, sub_annual_times_per_year):
  """
  Monte Carlo returns ratios of (yearly / subannual investors) total holdings over the span of variable investment terms.
  Runs a monte carlo simulation over (iterations), creating an index of the ratio of yearly to subannual investor holdings
  at the end of the investment period. The investment period is the random variable, each iteration will attempt to create
  a random span of (starting year --> end year). SubAnnual Frequency argument is how frequently the non-annual investor
  will invest their investment amount
  :param earliest_year: Earliest year available for the index, ex: 1983 for SP500
  :param index: dictionary of dates (first day of each trading month) over span of (earliest year) - 2024
  :param yearly_investment: Amount each investor will invest per year
  :param iterations: number of iterations in the monte carlo sim
  :param sub_annual_times_per_year: any of (2,3,4,6). Ex "6" means the investor invests every 2 months. if -1 then this is random selected each iteration
  :return:  list of lists, each element is [start year, end year, ratio] where ratio = (total shares yearly investor) / (total shares monthly investor)
  """

  # list of lists, each entry is a pair of (years in market), (yearly / monthly shares held)
  returns_ratio = []

  # assign default values for tradingMonth and timesPerYear, if random variable is 0 then these are the preset values
  # for the trading month the yearly investor invests in (by default Jan) and the frequency the monthly investor
  # invests in (by default 12 times per year, meaning monthly contributions to investment fund)
  trading_month = 1   # yearly investor always invests in Jan
  # times_per_year = 12  # by default the sub-annual investor invests 12 times per year, i.e. every month
  valid_trading_frequencies = [2, 3, 4, 6, 12]  # 12 % frequency must be == 0 in order for trading subannually to work

  # checks whether the random variable is within the supported values list
  if sub_annual_times_per_year not in valid_trading_frequencies:
    print("value passed as subAnnual_frequency for Monte Carlo simulator is not supported")
    exit()

  # run monte carlo over the number of iterations the user selected
  for it in range(iterations):
    start_year = 0   # initialize start and end as invalid years
    end_year = -1

    # If subAnnual_frequency is passed as -1, it means that the monte carlo should use a random valid frequency each iteration
    if sub_annual_times_per_year == -1 :
      times_per_year = random.choice(valid_trading_frequencies)
    else:
      # if sub_annual_times_per_year is not -1, then it represents the frequency of sub-annual trading
      # ex: sub_annual_times_per_year = 12, means the investor invests every month, or 12 times per year
      times_per_year = sub_annual_times_per_year


    # try new random ints until end_year comes after start_year
    while end_year < start_year:
      # generate random start and end years for investing
      start_year = random.randint(earliest_year, 2024)
      end_year = random.randint(earliest_year, 2024)

    # calculate the total number of shares held by each investor over the lifetime of their investing in the market
    sharePurchasesY, totalSharesY = investYearly(index, yearly_investment, start_year, end_year, trading_month)
    sharePurchasesM, totalSharesM = investSubannually(index, yearly_investment, start_year, end_year, times_per_year)

    # add the datapoints to the dictionary of return ratios
    returns_ratio.append([start_year, end_year, (totalSharesY / totalSharesM)])

  return returns_ratio




if __name__ == "__main__":
  yearlyInvestment = 12000  # int, how much each investor will invest over the course of the year

  # used for saving files
  current_directory = Path(os.path.dirname(os.path.abspath(__file__)))

  # create dictionary of market index values keyed on dates
  # dates are the first day of each month that the market was open
  # NOTE: this returns a tuple {[dictionary of date:open prices], earliest year in dataset as an int}
  sp500_data = get_index_data("^GSPC", 1983)
  qqq_data = get_index_data("TQQQ", 1983)  # high beta index
  sp500Beta_data = get_index_data("HIBL", 1983)  # sp500 high beta index, 3x leverage high beta
  btc_data = get_index_data("BTC-USD", 1983)  # get bitcoin data




  # SP500 TESTING ===================================================================================
  # Use SP500 as the index for both investors, Simple example - investing over 30 years
  sharePurchasesY, totalSharesY = investYearly(sp500_data[0], yearlyInvestment, sp500_data[1], 2024, 1)
  sharePurchasesM, totalSharesM = investSubannually(sp500_data[0], yearlyInvestment, sp500_data[1], 2024, 12)

  print("Total shares held by yearly investor: ", totalSharesY)
  print("Total shares held by monthly investor: ", totalSharesM)
  print("Portfolio Values Ratio (yearly/monthly): ", (totalSharesY / totalSharesM))
  print(" ")

  # MONTE CARLO SIM - SP500 =========================================================================
  # each monte carlo sim is run for it (iterations), varying the number of times the sub-annual investor invests per year
  returns_ratio2 = monteCarlo(sp500_data[1], sp500_data[0], yearlyInvestment, 1000, 2)  # investing every 6 mo
  returns_ratio4 = monteCarlo(sp500_data[1], sp500_data[0], yearlyInvestment, 1000, 4)
  # returns_ratio6 = monteCarlo(sp500_data[1], sp500_data[0], yearlyInvestment, 500, 6)
  returns_ratio12 = monteCarlo(sp500_data[1], sp500_data[0], yearlyInvestment, 1000, 12)  # investing every month

  # Plot SP500 Monte Carlo sims
  # Plot for investor that invests every 6 months
  x = [end - start for start, end, _ in returns_ratio2]
  y = [value for _, _, value in returns_ratio2]
  # Calculate the trend line
  z = np.polyfit(x, y, 1)  # Fit a first-degree polynomial (linear)
  p = np.poly1d(z)  # Create a polynomial object
  # plot data and trend line
  plt.style.use('Solarize_Light2')
  plt.plot(x, y, 'ro', label = 'Ratio: Biannual')
  plt.plot(x, p(x), "r--", label='Biannual, Trend Line')  # Plot the trend line

  # Plot for investor that invests quarterly
  # plots o that are green
  x = [end - start for start, end, _ in returns_ratio4]
  y = [value for _, _, value in returns_ratio4]
  # Calculate the trend line
  z = np.polyfit(x, y, 1)  # Fit a first-degree polynomial (linear)
  p = np.poly1d(z)  # Create a polynomial object
  # plot data and trend line
  plt.plot(x, y, 'bx', label = 'Ratio: Quarterly')
  plt.plot(x, p(x), "b--", label='Quarterly, Trend Line')  # Plot the trend line

  # # Plot for investor that invests every 2 months
  # # plots o that are blue
  # x = [end - start for start, end, _ in returns_ratio6]
  # y = [value for _, _, value in returns_ratio6]
  # plt.plot(x, y, 'bo')

  # Plot for investor that invests every month
  x = [end - start for start, end, _ in returns_ratio12]
  y = [value for _, _, value in returns_ratio12]
  # Calculate the trend line
  z = np.polyfit(x, y, 1)  # Fit a first-degree polynomial (linear)
  p = np.poly1d(z)  # Create a polynomial object
  # plot data and trend line
  plt.plot(x, y, 'gx', label = 'Ratio: Monthly Investor')
  plt.plot(x, p(x), "g--", label='Monthly, Trend Line')  # Plot the trend line

  # Add labels and title, save plot in current directory
  plt.xlabel('Time (End Year - Start Year)')
  plt.ylabel('Portfolio Ratio, Ratio = (yearly investor / sub-annual investor)')
  plt.title('S&P500 - Portfolio Ratios')
  plt.legend(loc='lower right')
  plt.grid(True)
  plt.savefig(current_directory / 'sp500_monteCarlo_yearly_monthly_ratio.png')
  # plt.show()
  plt.close()




  # COMPARING PORTFOLIO VALUES  ==============================================================
  # Plot Yearly and Monthly portfolio values over time
  sp500_yearly_portfolio_value = share_purchases_to_portfolio_value(sp500_data[0], sharePurchasesY)
  sp500_monthly_portfolio_value = share_purchases_to_portfolio_value(sp500_data[0], sharePurchasesM)

  # Convert the dictionary to a pandas Series
  sp500_yearly_series = pd.Series(sp500_yearly_portfolio_value)
  sp500_monthly_series = pd.Series(sp500_monthly_portfolio_value)

  # Convert the index to datetime objects
  sp500_yearly_series.index = pd.to_datetime(sp500_yearly_series.index)
  sp500_monthly_series.index = pd.to_datetime(sp500_monthly_series.index)

  # Plotting
  plt.figure(figsize=(10, 6))
  plt.style.use('Solarize_Light2')
  plt.plot(sp500_yearly_series.index, sp500_yearly_series.values, 'r-', label = 'Yearly Investor') # Use .values to get 1D array
  plt.plot(sp500_monthly_series.index, sp500_monthly_series.values, 'b--', label = 'Monthly Investor')
  plt.xlabel("Dates")
  plt.ylabel("Portfolio Values")
  plt.title("Investors portfolio values over time")
  plt.grid(True)
  plt.legend(loc='lower right')
  plt.savefig(current_directory / 'sp500_yearly_monthly_portfolio_values.png')
  # plt.show()
  plt.close()







  # ===================================================================================
  # COMPARING INDEXES - 10yr INVESTMENT HORIZON
  # Comparison will run for investors who started investing in 2014 and have invested for 10 years
  # If a dataset does not contain data for 2014, then the next available investing year is used (e.g. BTC data starts 2015)
  # ===================================================================================
  sp500_sharePurchasesY, sp500_totalSharesY = (
    investYearly(sp500_data[0], yearlyInvestment,max(2014, sp500_data[1]), 2024, 1))
  sp500_sharePurchasesM, sp500_totalSharesM = (
    investSubannually(sp500_data[0], yearlyInvestment, max(2014, sp500_data[1]), 2024, 12))

  # HIGH BETA TESTING =================================================================
  # Compare SP500 vs high Beta index, for this experiment used TQQQ
  qqq_sharePurchasesY, qqq_totalSharesY = (
    investYearly(qqq_data[0], yearlyInvestment, max(2014, qqq_data[1]), 2024, 1))
  qqq_sharePurchasesM, qqq_totalSharesM = (
    investSubannually(qqq_data[0], yearlyInvestment, max(2014, qqq_data[1]), 2024, 12))
  leveraged500_sharePurchasesY, leveraged500_totalSharesY = (
    investYearly(sp500Beta_data[0], yearlyInvestment, max(2014, sp500Beta_data[1]),2024, 1))
  leveraged500_sharePurchasesM, leveraged500_totalSharesM = (
    investSubannually(sp500Beta_data[0], yearlyInvestment, max(2014, sp500Beta_data[1]), 2024, 12))

  # BTC TESTING  ===================================================================================
  # Compare SP500 vs BTC
  btc_sharePurchasesY, btc_totalSharesY = (
    investYearly(btc_data[0], yearlyInvestment, max(2014, btc_data[1]), 2024, 1))
  btc_sharePurchasesM, btc_totalSharesM = (
    investSubannually(btc_data[0], yearlyInvestment, max(2014, btc_data[1]), 2024, 12))

  print("SP500 Investor started investing in ...... {}".format(max(2014, sp500_data[1])))
  print("QQQ Investor started investing in ........ {}".format(max(2014, qqq_data[1])))
  print("HIBL Investor started investing in ....... {}".format(max(2014, sp500Beta_data[1])))
  print("BTC Investor started investing in ........ {}".format(max(2014, btc_data[1])))
  print("Investor ratios = total portfolio value of yearly / monthly")
  print("SP500 investor ratio ............ {}".format(sp500_totalSharesY/sp500_totalSharesM))
  print("QQQ investor ratio .............. {}".format(qqq_totalSharesY/qqq_totalSharesM))
  print("HIBL investor ratio ............. {}".format(leveraged500_totalSharesY/leveraged500_totalSharesM))
  print("BTC investor ratio .............. {}".format(btc_totalSharesY/btc_totalSharesM))




  # MONTE CARLO SIM - HIGH BETA - QQQ   =======================================================
  # Runs monte calro sims for high beta indexes: QQQ and BTC
  high_beta_monteCarlo_qqq = monteCarlo(qqq_data[1], qqq_data[0], yearlyInvestment, 500, 12)
  high_beta_monteCarlo_btc = monteCarlo(btc_data[1], btc_data[0], yearlyInvestment, 500, 12)


  # Plot High Beta Monte Carlo sims
  # Plot QQQ
  x = [end - start for start, end, _ in high_beta_monteCarlo_qqq]
  y = [value for _, _, value in high_beta_monteCarlo_qqq]
  # Calculate the trend line
  z = np.polyfit(x, y, 1)  # Fit a first-degree polynomial (linear)
  p = np.poly1d(z)  # Create a polynomial object
  # plot data and trend line
  plt.plot(x, y, 'rx', label = 'Ratio: Monthly QQQ')
  plt.plot(x, p(x), "r--", label='QQQ Trend Line')  # Plot the trend line
  # plot BTC
  x = [end - start for start, end, _ in high_beta_monteCarlo_btc]
  y = [value for _, _, value in high_beta_monteCarlo_btc]
  # Calculate the trend line
  z = np.polyfit(x, y, 1)  # Fit a first-degree polynomial (linear)
  p = np.poly1d(z)  # Create a polynomial object
  # plot data and trend line
  plt.plot(x, y, 'bx', label = 'Ratio: Monthly BTC')
  plt.plot(x, p(x), "b--", label='BTC Trend Line')  # Plot the trend line

  # Add labels and title, save plot in current directory
  plt.xlabel('Time (End Year - Start Year)')
  plt.ylabel('Portfolio Ratio, Ratio = (yearly investor / monthly investor)')
  plt.title('High Beta Portfolio Ratios')
  plt.legend(loc='lower right')
  plt.grid(True)
  plt.savefig(current_directory / 'highBeta_monteCarlo_yearly_monthly_ratio.png')
  plt.show()
  plt.close()














# Stock Market Technical Analysis with Python and SQL

## Introduction
This project is a simple look at performing "_technical analysis_" on stock market time series data using Python 3 and SQLite.

### Goals
1. Acquire data from external data source
2. Integrate and organize the data into owned database
3. Perform data analysis to derive technical indicators

To accomplish this, we will retrieve time series (and other stock market data such as earnings reports) from external sources. Since external data sources may not be 100% reliable, we will make use of two different sources: Twelve Data https://twelvedata.com/ and AlphaVantage https://www.alphavantage.co/

Data will be retrieved with API calls made with the "requests" Python library, and then loaded into a SQLite database. The SQLite module is part of the standard library for Python 3, and provides "...a small, fast, self-contained, high-reliability, full-featured, SQL database engine." https://www.sqlite.org/index.html

After data is loaded into the SQLite DB, SQL queries can be used to calculate for a variety of "_technical indicators_" such as the Relative Strength Index (RSI), Moving Average Convergence/Divergence indicator (MACD), and other metrics such as the Price/Earnings Ratio and Earnings Yield. This information may then be used to _attempt_ to predict future price changes and assist in making trading decisions.

## Requirements
This project requires a Python 3 environment plus the following packages:
1. requests (for API calls) https://pypi.org/project/requests/
2. pandas (nicer looking table output) https://pypi.org/project/pandas/

Both can be conveniently installed via PIP
1. `pip install requests`
2. `pip install pandas`

Additionally, to retrieve new data, you will need to get your own free API keys from Twelve Data https://twelvedata.com/ and AlphaVantage https://www.alphavantage.co/ and put them into the appropriate locations in the _keys.json_ file.
(If you want to skip this part, you can use the provided sample database pre-loaded with data located in /samples/data1.sqlite)

## Usage
1. Download the _src_ files into the same directory
2. Sign up for your free API keys from TwelveData and optionally, AlphaVantage, if you want to get earnings data which is used to calculate PEratio and Earnings Yield
3. Add your API keys to _keys.json_ in the same dir. If you don't have the _keys.json_ file, the script will create it and prompt you for your API keys.
4. Add some stock symbols into _stocklist.txt_ (one per line, following the format: symbol,exchange  Ex.: NVDA,NASDAQ)
5. Run `GetData.py` to load data into the DB. (A new SQLite DB file named _data1.sqlite_ will be created if it doesn't already exist.)
6. Follow the prompts. Answer Y to download new time series data based on the stocks listed in the _stocklist.txt_ file. Optionally, answer Y when prompted to download earnings data used for some calculations.
7. Run `Demo.py` to view results from a variety of saved queries. Results will output into Excel or whichever default app your system uses to view .CSV files. These files will be placed in your `%TEMP%` dir. You may change this behavior and output the results to the terminal window by choosing X from the menu.

### Optionally
* You may use the provided _/samples/data1.sqlite_ SQLite DB file that already has some sample data loaded into it. If so, you may skip steps 2=6. Make sure the file is in the same dir as the .py files.
* You may use the provided _/samples/stocklist.txt_ file which already contains some stock symbols. If so, you may skip step 4. Make sure the file is in the same dir as the .py files.

## More Info
### Limitations
This project currently has the following limitations:
1. Only checks for stocks listed on the NASDAQ and NYSE. This can be updated in the future.
2. The 'free' API access from Twelve Data and AlphaVantage both have varying API request limits. For the exact rate and daily API limits, please visit the respective website.

### Additional Documentation
[Metadata/Data Dictionary](https://github.com/mike-remo/stock-analysis/blob/main/docs/data-dictionary.md)

### LICENSE
GNU General Public License v3.0

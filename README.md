# Stock Market Technical Analysis with Python and SQL

## Introduction
This project is a simple look at performing "_technical analysis_" on stock market time series data using Python 3 and SQLite.

### Goals
1. Acquire data from external data source
2. Integrate and organize the data into owned database
3. Perform data analysis to derive technical indicators

To accomplish this, we will retrieve time series (and other stock market data such as earnings reports) from external sources. Since external data sources are not 100% reliable, we will make use two different sources: Twelve Data https://twelvedata.com/ and AlphaVantage https://www.alphavantage.co/

Data will be retrieved with API calls made with the "requests" Python library, then loaded into a SQLite database. The SQLite module is part of the standard library for Python 3, and provides "...a small, fast, self-contained, high-reliability, full-featured, SQL database engine." https://www.sqlite.org/index.html

After data is loaded into the SQLite DB, SQL queries can be used to calculate for a variety of "_technical indicators_" such as the Relative Strength Index (RSI), and other metrics such as the Price/Earnings Ratio and Earnings Yield. This information may then be used to attempt to predict future changes on stock markets.

## Requirements
This project requires a Python 3 environment plus the following packages:
1. requests (for API calls) https://pypi.org/project/requests/
2. pandas (nicer looking table output) https://pypi.org/project/pandas/
(Both can be conveniently installed via PIP)

Additionally, to retrieve new data, you will need to get your own free API keys from Twelve Data https://twelvedata.com/ and AlphaVantage https://www.alphavantage.co/ and put them into the appropriate locations in the keys.json file.
(If you want to skip this part, you can use the provided sample database preloaded with data.)

## Usage
1. Download the files into the same directory
2. Sign up for your free API keys from TwelveData and AlphaVantage, then add your API keys to _keys.json_
3. Add some stock symbols (one per line and in ALL CAPS) into _stocklist.txt_
4. Run _GetData.py_ to load data into the DB. (A new SQLite DB file named data1.sqlite will be created if it doesn't already exist.)
5. Run _Demo.py_ to view results from a variety of pre-written queries.

### Optionally
* You may use the provided _samples/data1.sqlite_ SQLite DB file that already has some sample data loaded into it. If so, you may skip steps 2 and 4.
* You may use the provided _samples/stocklist.txt_ file which already contains some stock symbols. If so, you may skip step 3

## Details
TO DO

## More Info
### Limitations
This project currently has the following limitations:
1. Only checks for securities on the NASDAQ. Any others will return an error.
2. The Free API access from Twelve Data and AlphaVantage both have API call limits. For the exact rate and daily API limits, please visit the website of each.

### Additional Documentation
_docs/data-dictionary.md_

### LICENSE
GNU General Public License v3.0

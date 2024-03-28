# Get Data for Technical Analysis of Stocks
# Copyright (C) 2023 Michael Remollino (mikeremo at g mail dot com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from time import sleep
from os.path import isfile
import requests
import datetime
import sqlite3
import json

def getKey(keyFor="", keyFile="keys.json"):
    """Get API key from JSON file stored locally"""
    with open(keyFile, 'r') as file:
        contents = json.load(file)
        return contents[keyFor]

def APIcallTD(symbol: str, days = 1, exch = "NASDAQ"):
    """Get timeseries data from Twelve Data"""
    url = "http://api.twelvedata.com/time_series"
    querystring = {"exchange":exch,
                   "symbol":symbol,
                   "interval":"1day",
                   "outputsize":days,
                   "timezone":"exchange",
                   "format":"json"
                   }
    header = {"Authorization":"apikey "+getKey("TD")}
    response = requests.get(url, headers=header, params=querystring)
    return response.json()

def APIcallAV(symbol: str):
    """Get data from AlphaVantage"""
    url = "https://www.alphavantage.co/query"
    querystring = {"function":"EARNINGS",
                   "symbol":symbol,
                   "apikey":getKey("AV")
                   }
    response = requests.get(url, params=querystring)
    return response.json()

def APIcallTD2(symbol: str, exchange="NASDAQ"):
    """Get stock description info from Twelve Data"""
    url = "http://api.twelvedata.com/stocks"
    querystring = {"symbol":symbol,"exchange":exchange,"format":"json"}
    headers = {"Authorization":"apikey "+getKey("TD")}
    response = requests.get(url, headers=headers, params=querystring)
    return response.json()

def saveData(file: str, data):
    """For optionally saving raw data to file for archiving"""
    with open(file, 'w') as open_file:
        print("Writing to: " + file)
        json.dump(data, open_file)

def writeDB(file: str, option = 0, data = None):
    """
    Function for writing and updating SQLite DB.
    Option specifies:
    1 for initializing DB and defining schema
    2 for writing stock data to the staging table, then transfer to main table
    3 for writing earnings data to the staging table, then transfer to main table
    4 for writing stock description info
    5 to flush eps tables first for data to be refreshed
    6 to update quarter_eps table with the calculated ttm values
    """
    if option not in [1,2,3,4,5,6]: return
    print("Opening SQLite DB...")
    connection = sqlite3.connect(file)
    cursor = connection.cursor()
    print("Writing to DB...")

    if option == 1:
        SQLddl = [
            # Schema DDL:
            "CREATE TABLE stock_staging (datetime, symbol, open, high, low, close, volume);",
            "CREATE TABLE stocks (datetime, symbol, open, high, low, close, volume, CONSTRAINT uq_pk PRIMARY KEY (datetime, symbol));",
            "CREATE TABLE stock_descr (symbol, name, currency, exchange, mic_code, country, type, CONSTRAINT uq_pk PRIMARY KEY (symbol,exchange));",
            "CREATE TABLE annual_eps_staging (symbol, fiscalDateEnding, reportedEPS);",
            "CREATE TABLE annual_eps (symbol, fiscalDateEnding, reportedEPS, CONSTRAINT uq_pk PRIMARY KEY (symbol, fiscalDateEnding));",
            "CREATE TABLE quarter_eps_staging (symbol, fiscalDateEnding, reportedEPS, estimatedEPS, surprise, surprisePercentage);",
            "CREATE TABLE quarter_eps (symbol, fiscalDateEnding, reportedEPS, estimatedEPS, surprise, surprisePercentage, ttm, CONSTRAINT uq_pk PRIMARY KEY (symbol, fiscalDateEnding));",
            # P/E Ratio and Earnings Yield:
            "DROP VIEW IF EXISTS vw_pe_and_ey;",
            "CREATE VIEW vw_pe_and_ey AS SELECT stk.symbol, datetime as close_date, (close/ttm) AS PEratio, (ttm/close) AS EarnYield FROM stocks AS stk "
            "LEFT JOIN quarter_eps AS eps ON stk.symbol = eps.symbol AND fiscalDateEnding = ( "
            "SELECT MAX(fiscalDateEnding) FROM quarter_eps WHERE fiscalDateEnding <= datetime AND symbol = stk.symbol);",
            # Simple Moving Averages:
            "DROP VIEW IF EXISTS vw_SMA15d;",
            "CREATE VIEW vw_SMA15d AS SELECT symbol, datetime AS close_date, "
            "SUM(close) OVER (PARTITION BY symbol ORDER BY datetime DESC ROWS BETWEEN CURRENT ROW AND 14 FOLLOWING) / 14 as MovAVG FROM stocks;",
            # Gain/Loss for RSI:
            "DROP VIEW IF EXISTS vw_gainloss14d;",
            "CREATE VIEW vw_gainloss14d AS "
            "WITH cte AS (SELECT symbol, datetime AS close_date, close AS close_price, LEAD(close,1) OVER (PARTITION BY symbol ORDER BY datetime DESC) prev_close FROM stocks) "
            "SELECT symbol, close_date, close_price,"
            "CASE WHEN (close_price - prev_close) > 0 THEN (close_price - prev_close) ELSE 0 END gain, "
            "CASE WHEN (close_price - prev_close) < 0 THEN (prev_close - close_price) ELSE 0 END loss, "
            "AVG(CASE WHEN (close_price - prev_close) > 0 THEN (close_price - prev_close) ELSE 0 END) "
            "OVER (PARTITION BY symbol ORDER BY close_date DESC ROWS BETWEEN CURRENT ROW AND 13 FOLLOWING) avg_gain14, "
            "AVG(CASE WHEN (close_price - prev_close) < 0 THEN (prev_close - close_price) ELSE 0 END) "
            "OVER (PARTITION BY symbol ORDER BY close_date DESC ROWS BETWEEN CURRENT ROW AND 13 FOLLOWING) avg_loss14 "
            "FROM cte GROUP BY symbol, close_date ORDER BY close_date DESC;",
            # Relative Strength Index:
            "DROP VIEW IF EXISTS vw_rsi;",
            "CREATE VIEW vw_rsi AS "
            "WITH RECURSIVE cte_gainloss AS ( "
            "SELECT ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY close_date) AS rownum, * "
            "FROM vw_gainloss14d  WHERE close_date > date('now','-180 days') "
            "), cte_recur AS ( "
            "SELECT *, avg_gain14 AS avg_gain, avg_loss14 AS avg_loss FROM cte_gainloss WHERE rownum = 14 "
            "UNION ALL SELECT curr.*, (prev.avg_gain * 13 + curr.gain) / 14, (prev.avg_loss * 13 + curr.loss) / 14 "
            "FROM cte_gainloss AS curr INNER JOIN cte_recur AS prev "
            "ON curr.rownum = prev.rownum + 1 AND curr.symbol = prev.symbol "
            ") SELECT symbol, close_date, close_price, avg_gain, avg_loss, "
            "(avg_gain / avg_loss) AS RS, 100 - (100 / (1 + (avg_gain / avg_loss))) AS RSI "
            "FROM cte_recur ORDER BY close_date DESC;",
            # SMA used for calc EMA:
            "DROP VIEW IF EXISTS vw_macd_sma;",
            "CREATE VIEW vw_macd_sma AS "
            "SELECT symbol, datetime AS close_date, close AS close_price, "
            "SUM(close) OVER (PARTITION BY symbol ORDER BY datetime DESC ROWS BETWEEN CURRENT ROW AND 25 FOLLOWING) / 26 AS SMA26, "
            "SUM(close) OVER (PARTITION BY symbol ORDER BY datetime DESC ROWS BETWEEN CURRENT ROW AND 11 FOLLOWING) / 12 AS SMA12 "
            "FROM stocks;",
            # EMA26:
            "DROP VIEW IF EXISTS vw_macd_ema26;",
            "CREATE VIEW vw_macd_ema26 AS "
            "WITH RECURSIVE cte_sma AS ( "
            "SELECT ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY close_date) AS rownum, symbol, close_date, close_price, SMA26 "
            "FROM vw_macd_sma WHERE close_date > date('now','-360 days') "
            "), cte_recur AS ( "
            "SELECT *, SMA26 AS EMA26 FROM cte_sma WHERE rownum = 26 "
            "UNION ALL "
            "SELECT curr.*, (curr.close_price * (2.0/27)) + (prev.EMA26 * (1-2.0/27)) "
            "FROM cte_sma AS curr INNER JOIN cte_recur AS prev ON curr.rownum = prev.rownum + 1 AND curr.symbol = prev.symbol "
            ") SELECT * FROM cte_recur ORDER BY close_date DESC;",
            # EMA12:
            "DROP VIEW IF EXISTS vw_macd_ema12;",
            "CREATE VIEW vw_macd_ema12 AS "
            "WITH RECURSIVE cte_sma AS ( "
            "SELECT ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY close_date) AS rownum, symbol, close_date, close_price, SMA12 "
            "FROM vw_macd_sma WHERE close_date > date('now','-360 days') "
            "), cte_recur AS ( "
            "SELECT *, SMA12 AS EMA12 FROM cte_sma WHERE rownum = 12 "
            "UNION ALL "
            "SELECT curr.*, (curr.close_price * (2.0/13)) + (prev.EMA12 * (1-2.0/13)) "
            "FROM cte_sma AS curr INNER JOIN cte_recur AS prev ON curr.rownum = prev.rownum + 1 AND curr.symbol = prev.symbol "
            ") SELECT * FROM cte_recur ORDER BY close_date DESC;",
            # MACD:
            "DROP VIEW IF EXISTS vw_macd;",
            "CREATE VIEW vw_macd AS "
            "SELECT ema26.symbol, ema26.close_date, ema26.close_price, (EMA12-EMA26) AS MACD "
            "FROM vw_macd_ema26 ema26 "
            "INNER JOIN vw_macd_ema12 ema12 "
            "ON ema26.symbol = ema12.symbol AND ema26.close_date = ema12.close_date "
            "ORDER BY ema26.close_date DESC;",
            # MACD w/ Signal
            "DROP VIEW IF EXISTS vw_macd2;",
            "CREATE VIEW vw_macd2 AS "
            "WITH RECURSIVE cte_macd AS ( "
            "SELECT ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY close_date) AS rownum, symbol, close_date, close_price, MACD "
            "FROM vw_macd "
            "), cte_recur AS ( "
            "SELECT *, MACD AS signal FROM cte_macd WHERE rownum = 9 "
            "UNION ALL "
            "SELECT curr.*, (curr.MACD * (2.0/10)) + (prev.signal * (1-2.0/10)) "
            "FROM cte_macd AS curr INNER JOIN cte_recur AS prev ON curr.rownum = prev.rownum + 1 AND curr.symbol = prev.symbol "
            ") SELECT symbol, close_date, close_price, MACD, signal FROM cte_recur ORDER BY close_date DESC;"
        ]
        for c in SQLddl: cursor.execute(c)

    elif option == 2 and data != None:
        cursor.execute("DELETE FROM stock_staging;")
        for i in data["values"]:
            cursor.execute("INSERT INTO stock_staging (datetime, symbol, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, ?);",
                           (i["datetime"], data["meta"]["symbol"], i["open"], i["high"], i["low"], i["close"], i["volume"]))
        cursor.execute("INSERT OR IGNORE INTO stocks (datetime, symbol, open, high, low, close, volume) SELECT datetime, symbol, open, high, low, close, volume FROM stock_staging;")

    elif option == 3 and data != None:
        SQLdml = (
            "DELETE FROM annual_eps_staging;",
            "DELETE FROM quarter_eps_staging;"
        )
        for c in SQLdml: cursor.execute(c)

        symbol = data["symbol"]
        for i in data["annualEarnings"]:
            cursor.execute("INSERT INTO annual_eps_staging (symbol, fiscalDateEnding, reportedEPS) VALUES (?, ?, ?);",
                           (symbol, i["fiscalDateEnding"], i["reportedEPS"]))
        cursor.execute("INSERT OR IGNORE INTO annual_eps (symbol, fiscalDateEnding, reportedEPS) SELECT symbol, fiscalDateEnding, reportedEPS FROM annual_eps_staging;")
        
        for j in data["quarterlyEarnings"]:
            cursor.execute("INSERT INTO quarter_eps_staging (symbol, fiscalDateEnding, reportedEPS, estimatedEPS, surprise, surprisePercentage) VALUES (?, ?, ?, ?, ?, ?);",
                           (symbol, j["fiscalDateEnding"], j["reportedEPS"], j["estimatedEPS"], j["surprise"], j["surprisePercentage"]))
        cursor.execute("INSERT OR IGNORE INTO quarter_eps (symbol, fiscalDateEnding, reportedEPS, estimatedEPS, surprise, surprisePercentage) "
                       "SELECT symbol, fiscalDateEnding, reportedEPS, estimatedEPS, surprise, surprisePercentage FROM quarter_eps_staging WHERE reportedEPS != 'None';")

    elif option == 4 and data != None:
        for d in data["data"]:
            cursor.execute("INSERT OR IGNORE INTO stock_descr (symbol, name, currency, exchange, mic_code, country, type) VALUES (?, ?, ?, ?, ?, ?, ?);",
                           (d["symbol"], d["name"], d["currency"], d["exchange"], d["mic_code"], d["country"], d["type"]))
    
    elif option == 5:
        SQLdml = (
            "DELETE FROM annual_eps;",
            "DELETE FROM quarter_eps;"
        )
        for c in SQLdml: cursor.execute(c)
    
    elif option == 6:
        cursor.execute("UPDATE quarter_eps SET ttm = sub.ttm FROM (SELECT symbol, reportedEPS, fiscalDateEnding, "
                       "SUM(reportedEPS) OVER (PARTITION BY symbol ORDER BY fiscalDateEnding DESC ROWS BETWEEN CURRENT ROW AND 3 FOLLOWING) AS ttm "
                       "FROM quarter_eps) sub WHERE quarter_eps.symbol = sub.symbol AND quarter_eps.fiscalDateEnding = sub.fiscalDateEnding;")
    
    print("Closing DB...")
    connection.commit()
    connection.close()

def readDB(file: str, option = 0, symbol = None):
    """
    Read data out of DB
    Option specifies:
    1 for querying DB for any stock symbol not in the stock_descr table
    2 for querying DB for the latest date of specified symbol from the stocks table
    """
    if option not in [1,2]: return
    print("Opening SQLite DB...")
    connection = sqlite3.connect(file)
    cursor = connection.cursor()
    if option == 1:
        cursor.execute("SELECT DISTINCT symbol FROM stocks WHERE symbol NOT IN (SELECT symbol FROM stock_descr);")
        results = cursor.fetchall()
    elif option == 2 and symbol != None:
        cursor.execute("SELECT symbol, MAX(datetime) from stocks WHERE symbol = ?;",(symbol,))
        results = cursor.fetchall()
    print("Closing DB...")
    connection.close()
    return results

def fileChecks(keyFile = "keys.json", stockListFile = "stocklist.txt", fileDB = "data1.sqlite"):
    """Check for required files, and if necessary, create missing files"""
    if isfile(keyFile) == False:
        print("API keys file not found, creating new file...")
        with open(keyFile, 'w') as open_file:
            keys_placeholder = {}
            keys_placeholder["TD"] = input("Enter your 12 Data API Key here, or ENTER to skip: ")
            if(keys_placeholder["TD"] == ''): keys_placeholder["TD"] = "YOUR-TWELVE-DATA-API-KEY-HERE"
            keys_placeholder["AV"] = input("Enter your AlphaVantage API Key here, or ENTER to skip: ")
            if(keys_placeholder["AV"] == ''): keys_placeholder["AV"] = "YOUR-ALPHA-VANTAGE-API-KEY-HERE"
            print("If you need to edit your API keys, do so in the file: " + keyFile)
            json.dump(keys_placeholder, open_file)
    
    if isfile(stockListFile) == False:
        print("Stock list file not found, creating new file...")
        with open(stockListFile, 'w') as open_file:
            add_symbol = input("Enter in one stock symbol to check: ")
            open_file.write(add_symbol)

    if isfile(fileDB) == False:
        print("DB file not found, creating new file...")
        writeDB(fileDB, 1)

def main():
    delay = 30 # How many seconds to delay subsequent API calls
    today = datetime.datetime.today()
    keyFile = "keys.json" # Path to API keys file
    stockListFile = "stocklist.txt" # List of stock symbols to check, one per line
    fileDB = "data1.sqlite" # Path to SQLite DB file

    fileChecks(keyFile, stockListFile, fileDB)

    stocks = []
    print("Reading: " + stockListFile)
    with open(stockListFile, 'r') as open_file:
        for l in open_file:
            stocks.append(l.rstrip('\n'))
    listCount = len(stocks)

    choice = input("Update daily price data? [Y] ")
    if choice == 'y' or choice == 'Y' :
        counter = 0
        countSuccess = 0
        
        for stock in stocks:
            counter = counter + 1
            now = datetime.datetime.now()
            filename = "12Data-"+str(stock)+"-"+now.strftime("%Y%m%d-%H%M%S")+".json"
            
            lastestDate = readDB(fileDB, 2, stock) # Calculate how much historical data to fetch based on last timestamp
            if lastestDate == [(None, None)]:
                print("No existing data. New request.")
                lastNdays = 3652 # ~10y
            else:
                lastDate = datetime.datetime.strptime(lastestDate[0][1],'%Y-%m-%d')
                datediff = today.date() - lastDate.date()
                print("Symbol: " + str(lastestDate[0][0]) + " - days since last update: " + str(datediff.days))
                lastNdays = int(datediff.days + 1)

            buffer = APIcallTD(stock, lastNdays)
            print("Getting Market Data for " + stock + " #" + str(counter) + " of " + str(listCount))
            print("API status: " + buffer["status"])
            if(buffer["status"] == "ok"):
                writeDB(fileDB, 2, buffer)
                #saveData(filename, buffer) # Optionally sava output to file
                countSuccess += 1
            else:
                print("Possible error. Check output.")
                print(buffer)

            if(counter != listCount): # Throttle requests so we don't hit API limits
                print("Waiting...")
                sleep(delay)
        
        print("Successfully loaded: " + str(countSuccess) + " -- Failed to load: " + str(counter - countSuccess))
    else:
        print("Skipping price data update.")
    
    missing_list = readDB(fileDB, 1) # Looking for recently added stock symbols not in the stock_descr table
    print("Checking for new stock metadata...")
    if missing_list:
        for m in missing_list:
            stock_d = str(*m)
            print("Missing additional data for: " + stock_d)
            buffer = APIcallTD2(stock_d)
            print("API status: " + buffer["status"])
            if(buffer["status"] == "ok"):
                writeDB(fileDB, 4, buffer)
            else:
                print("Possible error. Check output.")
                print(buffer)
            if(m != missing_list[-1]):
                print("Waiting...")
                sleep(delay)
    else: print("No missing stock metadata.")
    
    choice = input("Update Earnings data? [Y] ")
    if choice == 'y' or choice == 'Y' : # Optionally update earnings report data
        counter = 0
        countSuccess = 0
        writeDB(fileDB, 5) # Flush old earnings data first

        for stock in stocks:
            counter += 1
            now = datetime.datetime.now()
            filename = "AVdata-"+str(stock)+"-"+now.strftime("%Y%m%d-%H%M%S")+".json"
            print("Getting Earnings Data for " + stock + " #" + str(counter) + " of " + str(listCount))
            buffer = APIcallAV(stock)
            if(list(buffer.keys())[0] == "symbol"):
                print("Data received...")
                writeDB(fileDB, 3, buffer)
                #saveData(filename, buffer) # Optionally sava output to file
                countSuccess += 1
            else:
                print("Possible error. Check output.")
                print(buffer)
            
            if(counter != listCount):
                print("Waiting...")
                sleep(delay)
        
        writeDB(fileDB, 6) # Update EPS TTM
        print("Successfully loaded: " + str(countSuccess) + " -- Failed to load: " + str(counter - countSuccess))
    else:
        print("Skipping earnings report update.")

if __name__ == "__main__":
    main()
    print("Script execution complete.")

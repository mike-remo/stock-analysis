from time import sleep
from os.path import isfile
import requests
import datetime
import sqlite3
import json

# Get API key from TXT/JSON file stored locally
def getKey(keyFor=""):
    with open("keys.json", 'r') as file:
        contents = json.load(file)
        return contents[keyFor]

# API call to get data from Twelve Data
def APIcallTD(symbol: str, days = 1, exch = "NASDAQ"):
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

# API call to get data from AlphaVantage
def APIcallAV(symbol: str):
    url = "https://www.alphavantage.co/query"
    querystring = {"function":"EARNINGS",
                   "symbol":symbol,
                   "apikey":getKey("AV")
                   }
    response = requests.get(url, params=querystring)
    return response.json()

# API call to get stock description info from Twelve Data
def APIcallTD2(symbol: str, exchange="NASDAQ"):
    url = "http://api.twelvedata.com/stocks"
    querystring = {"symbol":symbol,"exchange":exchange,"format":"json"}
    headers = {"Authorization":"apikey "+getKey("TD")}
    response = requests.get(url, headers=headers, params=querystring)
    return response.json()

# For optionally saving raw data to file for archiving/data lake
def saveData(file: str, data):
    with open(file, 'w') as open_file:
        print("Writing to: " + file)
        json.dump(data, open_file)

# Function for writing and updating SQLite DB.
# Option specifies:
# 1 for initializing DB and defining schema
# 2 for writing TD stock data to the staging table then transfer to main table
# 3 for writing AV earnings data to the staging table, then transfer to main table
# 4 for writing stock description info from TD
def writeDB(file: str, option = 0, data = None):
    if option not in [1,2,3,4]: return # invalid options
    print("Opening SQLite DB...")
    connection = sqlite3.connect(file)
    cursor = connection.cursor()
    print("Writing to DB...")

    if option == 1:
        SQLtables = [
            "CREATE TABLE stock_staging (datetime, symbol, open, high, low, close, volume);",
            "CREATE TABLE stocks (datetime, symbol, open, high, low, close, volume, CONSTRAINT uq_pk PRIMARY KEY (datetime, symbol));",
            "CREATE TABLE stock_descr (symbol, name, currency, exchange, mic_code, country, type, CONSTRAINT uq_pk PRIMARY KEY (symbol,exchange));",
            "CREATE TABLE annual_eps_staging (symbol, fiscalDateEnding, reportedEPS);",
            "CREATE TABLE annual_eps (symbol, fiscalDateEnding, reportedEPS, CONSTRAINT uq_pk PRIMARY KEY (symbol, fiscalDateEnding));",
            "CREATE TABLE quarter_eps_staging (symbol, fiscalDateEnding, reportedEPS, estimatedEPS, surprise, surprisePercentage);",
            "CREATE TABLE quarter_eps (symbol, fiscalDateEnding, reportedEPS, estimatedEPS, surprise, surprisePercentage, ttm, CONSTRAINT uq_pk PRIMARY KEY (symbol, fiscalDateEnding));",
        ]
        for c in SQLtables: cursor.execute(c)

    elif option == 2 and data != None:
        cursor.execute("DELETE FROM stock_staging;")
        for i in data["values"]:
            cursor.execute("INSERT INTO stock_staging (datetime, symbol, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, ?);",
                           (i["datetime"], data["meta"]["symbol"], i["open"], i["high"], i["low"], i["close"], i["volume"]))
        cursor.execute("INSERT OR IGNORE INTO stocks (datetime, symbol, open, high, low, close, volume) SELECT datetime, symbol, open, high, low, close, volume FROM stock_staging;")

    elif option == 3 and data != None:
        cursor.execute("DELETE FROM annual_eps_staging;")
        symbol = data["symbol"]
        for i in data["annualEarnings"]:
            cursor.execute("INSERT INTO annual_eps_staging (symbol, fiscalDateEnding, reportedEPS) VALUES (?, ?, ?);",
                           (symbol, i["fiscalDateEnding"], i["reportedEPS"]))
        cursor.execute("INSERT OR IGNORE INTO annual_eps (symbol, fiscalDateEnding, reportedEPS) SELECT symbol, fiscalDateEnding, reportedEPS FROM annual_eps_staging;")
        
        cursor.execute("DELETE FROM quarter_eps_staging;")
        for j in data["quarterlyEarnings"]:
            cursor.execute("INSERT INTO quarter_eps_staging (symbol, fiscalDateEnding, reportedEPS, estimatedEPS, surprise, surprisePercentage) VALUES (?, ?, ?, ?, ?, ?);",
                           (symbol, j["fiscalDateEnding"], j["reportedEPS"], j["estimatedEPS"], j["surprise"], j["surprisePercentage"]))
        cursor.execute("INSERT OR IGNORE INTO quarter_eps (symbol, fiscalDateEnding, reportedEPS, estimatedEPS, surprise, surprisePercentage) SELECT symbol, fiscalDateEnding, reportedEPS, estimatedEPS, surprise, surprisePercentage FROM quarter_eps_staging WHERE reportedEPS != 'None';")

    elif option == 4 and data != None:
        for d in data["data"]:
            cursor.execute("INSERT OR IGNORE INTO stock_descr (symbol, name, currency, exchange, mic_code, country, type) VALUES (?, ?, ?, ?, ?, ?, ?);",
                           (d["symbol"], d["name"], d["currency"], d["exchange"], d["mic_code"], d["country"], d["type"]))
    
    print("Closing DB...")
    connection.commit()
    connection.close()

# Read data out of DB
# Option specifies:
# 1 for querying DB for any stock symbol not in the stock_descr table
# 2 for querying DB for the latest date of specified symbol from the stocks table
def readDB(file: str, option = 0, symbol = None):
    if option not in [1,2]: return # invalid options
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

def main():
    delay = 30 # How many seconds to delay subsequent API calls
    today = datetime.datetime.today()
    stocks = []
    
    stockListFile = "stocklist.txt" # List of stock symbols to check, one per line.
    if isfile(stockListFile) == False:
        print("Stock list file not found, creating new file...")
        with open(stockListFile, 'w') as open_file:
            add_symbol = input("Enter in one stock symbol to check: ")
            open_file.write(add_symbol)

    print("Reading: " + stockListFile)
    with open(stockListFile, 'r') as open_file:
        for l in open_file:
            stocks.append(l.rstrip('\n'))
    listCount = len(stocks)

    fileDB = "data1.sqlite" # Path to SQLite DB file
    if isfile(fileDB) == False:
        print("DB file not found, creating new file...")
        writeDB(fileDB, 1)

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
                lastNdays = 3652 # 10y
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
            
        print("Successfully loaded: " + str(countSuccess) + " -- Failed to load: " + str(counter - countSuccess))
    else:
        print("Skipping earnings report update.")

if __name__ == "__main__":
    main()
    print("Script execution complete.")
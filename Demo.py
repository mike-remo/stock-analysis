from os.path import isfile
import sqlite3
import pandas

def execDB(file: str, commands: list):
    print("Opening DB...")
    connection = sqlite3.connect(file)
    cursor = connection.cursor()
    print("Writing to DB...")
    for c in commands: cursor.execute(c)
    connection.commit()
    print("Closing DB.")
    connection.close()

def readDB(file: str, command):
    print("\nFetching data from DB...")
    connection = sqlite3.connect(file)
    results = pandas.read_sql_query(command, connection)
    connection.close()
    return results

def getSymbol(file: str, symbol = 0):
    if symbol != 0: # Bypass if a stock symbol was previously chosen
        return symbol

    SQLinfo = "SELECT symbol, name, currency, exchange FROM stock_descr ORDER BY symbol ASC;"
    table = readDB(file, SQLinfo)
    stocks = table['symbol'].tolist()

    while(True):
        print("\nAvailable stock to check:")
        print(table)
        choice = input("Enter stock symbol *ALL CAPS* to query: ")
        if choice in ['q','Q']:
            return None
        elif choice in stocks:
            print(choice + " set.")
            return choice
        else:
            print("Invalid choice.")

def main():
    SQLflush = [
        "DELETE FROM stock_staging;",
        "DELETE FROM stocks;",
        "DELETE FROM stock_descr;",
        "DELETE FROM annual_eps_staging;",
        "DELETE FROM annual_eps;",
        "DELETE FROM quarter_eps_staging;",
        "DELETE FROM quarter_eps;"
    ]
    SQLcalc = [
        # Update quarter_eps table with the calculated ttm values
        "UPDATE quarter_eps SET ttm = sub.ttm FROM (SELECT symbol, reportedEPS, fiscalDateEnding, "
         "SUM(reportedEPS) OVER (PARTITION BY symbol ORDER BY fiscalDateEnding DESC ROWS BETWEEN CURRENT ROW AND 3 FOLLOWING) AS ttm "
         "FROM quarter_eps) sub WHERE quarter_eps.symbol = sub.symbol AND quarter_eps.fiscalDateEnding = sub.fiscalDateEnding;",
        # Views for calculations: P/E Ratio, Earnings Yield, Simple Moving Averages, Relative Strength Index
        "DROP VIEW IF EXISTS vw_pe_and_ey;",
        "CREATE VIEW vw_pe_and_ey AS SELECT stk.symbol, datetime as close_date, (close/ttm) AS PEratio, (ttm/close) AS EarnYield FROM stocks AS stk "
         "LEFT JOIN quarter_eps AS eps ON stk.symbol = eps.symbol AND fiscalDateEnding = ( "
         "SELECT MAX(fiscalDateEnding) FROM quarter_eps WHERE fiscalDateEnding <= datetime AND symbol = stk.symbol);",
        "DROP VIEW IF EXISTS vw_SMA15d;",
        "CREATE VIEW vw_SMA15d AS SELECT symbol, datetime AS close_date, "
         "SUM(close) OVER (PARTITION BY symbol ORDER BY datetime DESC ROWS BETWEEN CURRENT ROW AND 14 FOLLOWING) / 14 as MovAVG FROM stocks;",
        "DROP VIEW IF EXISTS vw_gainloss14d;",
        "CREATE VIEW vw_gainloss14d AS "
         "WITH cte AS (SELECT symbol, datetime AS close_date, close AS close_price, LEAD(close,1) OVER (PARTITION BY symbol ORDER BY datetime DESC) prev_close FROM stocks) "
         "SELECT symbol, close_date, close_price,"
         "CASE WHEN (close_price - prev_close) > 0 THEN (close_price - prev_close) ELSE 0 END gain, "
         "CASE WHEN (close_price - prev_close) < 0 THEN (prev_close - close_price) ELSE 0 END loss, "
         "AVG(CASE WHEN (close_price - prev_close) > 0 THEN (close_price - prev_close) ELSE 0 END) OVER (PARTITION BY symbol ORDER BY close_date DESC ROWS BETWEEN CURRENT ROW AND 13 FOLLOWING) avg_gain14, "
         "AVG(CASE WHEN (close_price - prev_close) < 0 THEN (prev_close - close_price) ELSE 0 END) OVER (PARTITION BY symbol ORDER BY close_date DESC ROWS BETWEEN CURRENT ROW AND 13 FOLLOWING) avg_loss14 "
         "FROM cte GROUP BY symbol, close_date ORDER BY close_date DESC;",
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
         "FROM cte_recur ORDER BY close_date DESC;"
    ]

    fileDB = "data1.sqlite" # Specify existing SQLite DB file location here
    if isfile(fileDB) == False:
        print("DB file not found, please generate the DB using GetData.py")
        return

    choice = 0
    symbol = 0
    while(True):
        print("\nMenu:")
        print("1: Perform calculations for data analysis")
        print("2: Set/Change stock symbol to query")
        print("3: Report latest daily prices for all")
        print("4: Overview of specific stock")
        print("5: P/E ratio and Earnings Yield")
        print("6: Simple Moving Average over 15d")
        print("7: Relative Strength Index 14d")
        print('C: Custom query')
        print("F: Flush data from tables")
        print("Q: Quit")
        choice = input("Input choice: ")

        if choice in ['q','Q']:
            print("Exiting.")
            return
        elif choice == "1":
            print("Performing calculations...")
            execDB(fileDB, SQLcalc)
        elif choice == "2":
            symbol = getSymbol(fileDB, 0) # Manually set symbol to query
        elif choice == "3":
            SQL1 = ("SELECT stk.symbol, stk.datetime AS close_date, stk.open, stk.low, stk.high, stk.close FROM stocks stk "
                    "INNER JOIN (SELECT symbol, MAX(datetime) AS date FROM stocks GROUP BY symbol) last "
                    "ON stk.symbol = last.symbol AND stk.datetime = last.date;")
            table = readDB(fileDB, SQL1)
            print("Most recent daily prices for stock in DB:")
            print(table)
        elif choice == "4":
            symbol = getSymbol(fileDB, symbol) # Automatically set symbol if previously set
            SQL1 = ("SELECT stk.symbol, datetime AS close_date, open, low, high, close, "
                    "pe.PEratio, pe.EarnYield, sma.MovAVG, rsi.avg_gain, rsi.avg_loss, rsi.RS, rsi.RSI "
                    "FROM stocks AS stk "
                    "INNER JOIN vw_pe_and_ey AS pe ON stk.symbol = pe.symbol AND stk.datetime = pe.close_date "
                    "INNER JOIN vw_SMA15d AS sma ON stk.symbol = sma.symbol AND stk.datetime = sma.close_date "
                    "INNER JOIN vw_rsi AS rsi ON stk.symbol = rsi.symbol AND stk.datetime = rsi.close_date "
                    f"WHERE stk.symbol = '{symbol}' ORDER BY datetime DESC LIMIT 10;")
            table = readDB(fileDB, SQL1)
            print("OVerview for " + symbol)
            print(table.to_string())
        elif choice == "5":
            symbol = getSymbol(fileDB, symbol)
            SQL1 = f"SELECT * FROM vw_pe_and_ey WHERE symbol = '{symbol}' ORDER BY close_date DESC LIMIT 60;"
            table = readDB(fileDB, SQL1)
            print("P/E ratio and Earnings Yield Report:")
            print(table.to_string())
        elif choice == "6":
            symbol = getSymbol(fileDB, symbol)
            SQL1 = f"SELECT * FROM vw_SMA15d WHERE symbol = '{symbol}' ORDER BY close_date DESC LIMIT 60;"
            table = readDB(fileDB, SQL1)
            print("SMA 15d report:")
            print(table.to_string())
        elif choice == "7":
            symbol = getSymbol(fileDB, symbol)
            SQL1 = (f"SELECT * FROM vw_rsi WHERE symbol = '{symbol}' LIMIT 60;")
            table = readDB(fileDB, SQL1)
            print("RSI 14d Report:")
            print(table.to_string())
        elif choice in ['f','F']:
            confirm = input("Flush data: ARE YOU SURE? [Y] to confirm: ")
            if confirm in ['y','Y']:
                print("Flushing data from tables.")
                execDB(fileDB, SQLflush)
            else: print("Canceled.")
        elif choice in ['c','C']:
            print("Custom SQL query: ")
            SQL1 = input("-> ")
            try:
                table = readDB(fileDB, SQL1)
                print("Results of: " + SQL1)
                print(table.to_string())
            except Exception as e:
                print(e)
                pass
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()

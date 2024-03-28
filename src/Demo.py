# Demo for Technical Analysis of Stocks
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

from os.path import isfile
from os import startfile
import sqlite3
import pandas
import tempfile

def execDB(file: str, commands: list):
    """Execute SQL statements from a list on the specified DB"""
    print("Opening DB...")
    connection = sqlite3.connect(file)
    cursor = connection.cursor()
    print("Writing to DB...")
    for c in commands: cursor.execute(c)
    connection.commit()
    print("Closing DB.")
    connection.close()

def readDB(file: str, command):
    """Read from DB and return results of query"""
    print("\nFetching data from DB...")
    connection = sqlite3.connect(file)
    results = pandas.read_sql_query(command, connection)
    connection.close()
    return results

def getSymbol(file: str, symbol = 0):
    """View available stock symbols in DB to query and allow user to select one"""
    if symbol != 0: return symbol # Bypass if a stock symbol was previously chosen
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

def outputEditor(output: pandas.DataFrame):
    """
    Output results to CSV file and open it with default app
    Will open in Excel assuming it is your default CSV editor
    """
    tmpFile = tempfile.NamedTemporaryFile(suffix = '.csv', delete = False)
    print("Opening " + tmpFile.name + " in external editor.")
    output.to_csv(tmpFile.name)
    startfile(tmpFile.name)

def main():
    fileDB = "data1.sqlite" # Specify existing SQLite DB file location here
    if isfile(fileDB) == False:
        print("DB file not found, please generate the DB using GetData.py")
        return

    choice = 0
    symbol = 0
    external = 'Y'

    while(True):
        print("\nMenu:")
        print("1: Set/Change stock symbol to query (Currently: " + str(symbol) + ")")
        print("2: Report latest daily prices for all")
        print("3: Overview of specific stock")
        print("4: P/E ratio and Earnings Yield")
        print("5: Simple Moving Average over 15d")
        print("6: Relative Strength Index 14d")
        print("7: MACD 12d-26d w/ 9d Signal")
        print('C: Custom query')
        print("F: Flush data from tables")
        print("X: Open in external editor? (Currently: " + external + ")")
        print("Q: Quit")
        choice = input("Input choice: ")

        if choice in ['q','Q']:
            print("Exiting.")
            return
        elif choice == "1":
            symbol = getSymbol(fileDB, 0) # Manually set symbol to query
        elif choice == "2":
            SQL1 = ("SELECT stk.symbol, stk.datetime AS close_date, stk.open, stk.low, stk.high, stk.close FROM stocks stk "
                    "INNER JOIN (SELECT symbol, MAX(datetime) AS date FROM stocks GROUP BY symbol) last "
                    "ON stk.symbol = last.symbol AND stk.datetime = last.date;")
            table = readDB(fileDB, SQL1)
            print("Most recent daily prices for stock in DB:")
            if external in ['y','Y']: outputEditor(table)
            else: print(table)
        elif choice == "3":
            symbol = getSymbol(fileDB, symbol) # Automatically set symbol if previously set
            SQL1 = ("SELECT stk.symbol, datetime AS close_date, open, low, high, close, "
                    "pe.PEratio, pe.EarnYield, sma.MovAVG, rsi.RSI "
                    "FROM stocks AS stk "
                    "INNER JOIN vw_pe_and_ey AS pe ON stk.symbol = pe.symbol AND stk.datetime = pe.close_date "
                    "INNER JOIN vw_SMA15d AS sma ON stk.symbol = sma.symbol AND stk.datetime = sma.close_date "
                    "INNER JOIN vw_rsi AS rsi ON stk.symbol = rsi.symbol AND stk.datetime = rsi.close_date "
                    f"WHERE stk.symbol = '{symbol}' ORDER BY datetime DESC LIMIT 30;")
            table = readDB(fileDB, SQL1)
            print("OVerview for " + symbol)
            if external in ['y','Y']: outputEditor(table)
            else: print(table.to_string())
        elif choice == "4":
            symbol = getSymbol(fileDB, symbol)
            SQL1 = f"SELECT * FROM vw_pe_and_ey WHERE symbol = '{symbol}' ORDER BY close_date DESC LIMIT 60;"
            table = readDB(fileDB, SQL1)
            print("P/E ratio and Earnings Yield Report:")
            if external in ['y','Y']: outputEditor(table)
            else: print(table.to_string())
        elif choice == "5":
            symbol = getSymbol(fileDB, symbol)
            SQL1 = f"SELECT * FROM vw_SMA15d WHERE symbol = '{symbol}' ORDER BY close_date DESC LIMIT 60;"
            table = readDB(fileDB, SQL1)
            print("SMA 15d report:")
            if external in ['y','Y']: outputEditor(table)
            else: print(table.to_string())
        elif choice == "6":
            symbol = getSymbol(fileDB, symbol)
            SQL1 = (f"SELECT * FROM vw_rsi WHERE symbol = '{symbol}' LIMIT 60;")
            table = readDB(fileDB, SQL1)
            print("RSI 14d Report:")
            if external in ['y','Y']: outputEditor(table)
            else: print(table.to_string())
        elif choice == "7":
            symbol = getSymbol(fileDB, symbol)
            SQL1 = (f"SELECT * FROM vw_macd2 WHERE symbol = '{symbol}' LIMIT 60;")
            table = readDB(fileDB, SQL1)
            print("MACD:")
            if external in ['y','Y']: outputEditor(table)
            else: print(table.to_string())
        elif choice in ['f','F']:
            confirm = input("Flush data: ARE YOU SURE? [Y] to confirm: ")
            if confirm in ['y','Y']:
                print("Flushing data from tables.")
                SQLflush = [
                    "DELETE FROM stock_staging;",
                    "DELETE FROM stocks;",
                    "DELETE FROM stock_descr;",
                    "DELETE FROM annual_eps_staging;",
                    "DELETE FROM annual_eps;",
                    "DELETE FROM quarter_eps_staging;",
                    "DELETE FROM quarter_eps;"
                ]
                execDB(fileDB, SQLflush)
            else: print("Operation canceled.")
        elif choice in ['c','C']:
            print("Custom SQL query: ")
            SQL1 = input("-> ")
            try:
                table = readDB(fileDB, SQL1)
                print("Results of: " + SQL1)
                if external in ['y','Y']: outputEditor(table)
                else: print(table.to_string())
            except Exception as e:
                print(e)
                pass
        elif choice in ['x','X']:
            print("Open results in external editor? ")
            print("(This will use the default app set for CSV files.)")
            external = input("Input 'y' or 'Y' for YES, any other for NO: ")
            if external not in ['y','Y']: external = 'N'
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()

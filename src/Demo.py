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

import os
import math
import tempfile
import sqlite3
import pandas
from plotly import graph_objects as go, subplots as sp

def exec_db(file: str, commands: list):
    """Execute SQL statements from a list on the specified DB"""
    print("Opening DB...")
    connection = sqlite3.connect(file)
    cursor = connection.cursor()
    print("Writing to DB...")
    for c in commands:
        cursor.execute(c)
    print("Closing DB.")
    cursor.close()
    connection.commit()
    connection.close()

def read_db(file: str, command):
    """Read from DB and return results of query"""
    print("\nFetching data from DB...")
    connection = sqlite3.connect(file)
    results = pandas.read_sql_query(command, connection)
    connection.close()
    return results

def get_symbol(file: str, symbol = 0):
    """View available stock symbols in DB to query and allow user to select one"""
    if symbol != 0: return symbol # Bypass if a stock symbol was previously chosen
    SQLinfo = "SELECT symbol, name, currency, exchange FROM stock_descr ORDER BY symbol ASC;"
    table = read_db(file, SQLinfo)
    stocks = table['symbol'].tolist()

    while(True):
        print("\nAvailable stock to check:")
        print(table)
        choice = input("Enter stock symbol to query: ").upper()
        if choice in ['q','Q']:
            return None
        elif choice in stocks:
            print(choice + " set.")
            return choice
        else:
            print("Invalid choice.")

def output_editor(output: pandas.DataFrame):
    """
    Output results to CSV file and open it with default app.
    Will open in Excel assuming it is your default CSV editor.
    """
    tmpfile = tempfile.NamedTemporaryFile(suffix = '.csv', delete = False)
    print("Opening " + tmpfile.name + " in external editor.")
    output.to_csv(tmpfile.name)
    os.startfile(tmpfile.name)

def visualizer(raw_data: pandas.DataFrame, style: int):
    """
    Generate graphs with plotly lib.
    Output is HTML file that auto opens in default browser.

    Parameters:
    raw_data (dataframe): Data to plot.
    Style (int): refers to the following
    1- Line charts, including candlestick chart for OHLC.
    2- Indicators arranged in a grid.

    Returns: None
    """
    output_file = "visualized.html"

    if style == 1:
        print("Generating graph...")
        raw_data.sort_values(by = ['close_date'], inplace = True)
        chart = sp.make_subplots(rows = 3, cols = 1, row_heights=[0.5, 0.25, 0.25])
        chart.add_trace(go.Candlestick(
            name = "OHLC",
            x = raw_data["close_date"],
            open = raw_data["open"],
            high = raw_data["high"],
            low = raw_data["low"],
            close = raw_data["close"] ),
            row = 1, col = 1)
        chart.add_trace(go.Scatter(
            name = "SMA50",
            marker = dict(color = 'blue'),
            x = raw_data["close_date"],
            y = raw_data["SMA50"] ),
            row = 1, col = 1)
        chart.add_trace(go.Scatter(
            name = "RSI",
            x = raw_data["close_date"],
            y = raw_data["RSI"] ),
            row = 2, col = 1)
        chart.add_trace(go.Scatter(
            name = "P/E ratio",
            x = raw_data["close_date"],
            y = raw_data["PEratio"] ),
            row = 2, col = 1)
        chart.add_trace(go.Scatter(
            name = "MACD",
            x = raw_data["close_date"],
            y = raw_data["MACD"] ),
            row = 3, col = 1)
        chart.add_trace(go.Scatter(
            name = "MACD signal",
            x = raw_data["close_date"],
            y = raw_data["signal"] ),
            row = 3, col = 1)
        chart.update_layout(
            title = "Charts for " + raw_data["symbol"][1],
            title_font_size = 24,
            legend_title_text='Legend',
            #yaxis_title = "$ USD",
            xaxis_rangeslider_visible = False)
        chart.update_yaxes(title_text = "OHLC & SMA50 ($ USD)", row = 1, col = 1)
        chart.update_yaxes(title_text = "RSI & PEr", row = 2, col = 1)
        chart.update_yaxes(title_text = "MACD w/ Signal", row = 3, col = 1)
        chart.write_html(output_file, auto_open = True)
    
    elif style == 2:
        print("Generating graph...")
        count = len(raw_data)
        maxcol = 4
        chart = go.Figure()
        for n in range(count):
            rowno = math.floor(n / maxcol)
            colno = n % maxcol
            chart.add_trace(go.Indicator(
                mode = "number+delta",
                value = float(raw_data["close"][n]),
                number = {'prefix': "$",
                          'valueformat': ".2f"},
                delta = {'position': "right",
                         'reference': float(raw_data["open"][n]),
                         'valueformat': ".2%",
                         'relative': True},
                title = {'text': raw_data["symbol"][n]},
                domain = {'row': rowno, 'column': colno} ))
        chart.update_layout(
            title = "Indicators " + raw_data["close_date"][0],
            title_font_size = 24,
            grid = {'rows': math.ceil(count / maxcol),
                    'columns': maxcol,
                    'pattern': "independent"} )
        chart.write_html(output_file, auto_open = True)

def main():
    file_db = "data1.sqlite" # Specify existing SQLite DB file location here
    if os.path.isfile(file_db) == False:
        print("DB file not found, please generate the DB using GetData.py")
        return
    
    choice = 0
    symbol = 0
    external = 'N'
    visualize = 'Y'

    while(True):
        print("\nMenu:")
        print("1: Set/Change stock symbol to query (Currently: " + str(symbol) + ")")
        print("2: Report latest daily prices for all (Visuals available)")
        print("3: Overview of specific stock (Visuals available)")
        print("  (Includes OHLC, P/E Ratio, SMA 50d, RSI 14d, MACD)")
        print("4: Simple Moving Averages")
        print("5: Relative Strength Index 14d")
        print("6: MACD 12d-26d w/ 9d Signal")
        print("C: Custom query (Ex.: SELECT * FROM stocks LIMIT 100;)")
        print("X: Open in external editor? (Currently: " + external + ")")
        print("V: Create graph of results? (Currently: " + visualize + ")")
        print("Q: Quit")
        choice = input("Input choice: ")

        if choice in ['q','Q']:
            print("Exiting.")
            return
        elif choice == "1":
            symbol = get_symbol(file_db, 0) # Manually set symbol to query
        elif choice == "2":
            sqlcmd = ("SELECT stk.symbol, stk.datetime AS close_date, stk.open, stk.low, stk.high, stk.close "
                      "FROM stocks stk "
                      "INNER JOIN (SELECT symbol, MAX(datetime) AS date FROM stocks GROUP BY symbol) last "
                      "ON stk.symbol = last.symbol AND stk.datetime = last.date;")
            table = read_db(file_db, sqlcmd)
            print("Most recent daily prices for stock in DB:")
            if external in ['y','Y']: output_editor(table)
            else: print(table)
            if visualize in ['y','Y']: visualizer(table, 2)
        elif choice == "3":
            symbol = get_symbol(file_db, symbol) # Automatically set symbol if previously set
            sqlcmd = ("SELECT stk.symbol, datetime AS close_date, open, low, high, close, volume, "
                    "pe.PEratio, pe.EarnYield, sma.SMA50, rsi.RSI, macd.MACD, macd.signal "
                    "FROM stocks AS stk "
                    "LEFT JOIN vw_pe_and_ey AS pe ON stk.symbol = pe.symbol AND stk.datetime = pe.close_date "
                    "LEFT JOIN vw_SMA AS sma ON stk.symbol = sma.symbol AND stk.datetime = sma.close_date "
                    "LEFT JOIN vw_rsi AS rsi ON stk.symbol = rsi.symbol AND stk.datetime = rsi.close_date "
                    "LEFT JOIN vw_macd2 AS macd ON stk.symbol = macd.symbol AND stk.datetime = macd.close_date "
                    f"WHERE stk.symbol = '{symbol}' ORDER BY datetime DESC LIMIT 126;")
            table = read_db(file_db, sqlcmd)
            print("OVerview for " + symbol)
            if external in ['y','Y']: output_editor(table)
            else: print(table.to_string())
            if visualize in ['y','Y']: visualizer(table, 1)
        elif choice == "4":
            symbol = get_symbol(file_db, symbol)
            sqlcmd = f"SELECT * FROM vw_SMA WHERE symbol = '{symbol}' ORDER BY close_date DESC LIMIT 252;"
            table = read_db(file_db, sqlcmd)
            print("Simple Moving Averages:")
            if external in ['y','Y']: output_editor(table)
            else: print(table.to_string())
        elif choice == "5":
            symbol = get_symbol(file_db, symbol)
            sqlcmd = (f"SELECT * FROM vw_rsi WHERE symbol = '{symbol}' LIMIT 252;")
            table = read_db(file_db, sqlcmd)
            print("RSI 14d Report:")
            if external in ['y','Y']: output_editor(table)
            else: print(table.to_string())
        elif choice == "6":
            symbol = get_symbol(file_db, symbol)
            sqlcmd = (f"SELECT * FROM vw_macd2 WHERE symbol = '{symbol}' LIMIT 252;")
            table = read_db(file_db, sqlcmd)
            print("MACD 12d-26d w/ 9d Signal:")
            if external in ['y','Y']: output_editor(table)
            else: print(table.to_string())
        elif choice in ['c','C']:
            print("Custom SQL query: ")
            sqlcmd = input("-> ")
            try:
                table = read_db(file_db, sqlcmd)
                print("Results of: " + sqlcmd)
                if external in ['y','Y']: output_editor(table)
                else: print(table.to_string())
            except Exception as ex:
                print(ex)
                pass
        elif choice in ['x','X']:
            print("Open results in external editor? ")
            print("(This will use the default app set for CSV files.)")
            external = input("Input 'y' or 'Y' for YES, any other for NO: ")
            if external not in ['y','Y']: external = 'N'
        elif choice in ['v','V']:
            print("Create graph of query results? ")
            print("(This will use the default browser or app set for HTML files.)")
            visualize = input("Input 'y' or 'Y' for YES, any other for NO: ")
            if visualize not in ['y','Y']: visualize = 'N'
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()

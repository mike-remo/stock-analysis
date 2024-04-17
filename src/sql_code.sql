/*
 Simple Stock Technical Analysis (SQL code)
 Copyright (C) 2024 Michael Remollino (mikeremo at g mail dot com)

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <https://www.gnu.org/licenses/>.
*/

/*
  SUMMARY:
    SQL code used in project.
    This code does not need to be executed if using the python scripts.
    It is presented here to be more convenient to analyze the SQL statements.
*/

/* Schema DDL: */
CREATE TABLE stock_staging (datetime, symbol, open, high, low, close, volume);
CREATE TABLE stocks (datetime, symbol, open, high, low, close, volume,
  CONSTRAINT uq_pk PRIMARY KEY (datetime, symbol));
CREATE TABLE stock_descr (symbol, name, currency, exchange, mic_code, country, type,
  CONSTRAINT uq_pk PRIMARY KEY (symbol,exchange));
CREATE TABLE annual_eps_staging (symbol, fiscalDateEnding, reportedEPS);
CREATE TABLE annual_eps (symbol, fiscalDateEnding, reportedEPS,
  CONSTRAINT uq_pk PRIMARY KEY (symbol, fiscalDateEnding));
CREATE TABLE quarter_eps_staging (symbol, fiscalDateEnding, reportedEPS, estimatedEPS, surprise, surprisePercentage);
CREATE TABLE quarter_eps (symbol, fiscalDateEnding, reportedEPS, estimatedEPS, surprise, surprisePercentage, ttm,
  CONSTRAINT uq_pk PRIMARY KEY (symbol, fiscalDateEnding));

/* P/E Ratio and Earnings Yield: */
DROP VIEW IF EXISTS vw_pe_and_ey;
CREATE VIEW vw_pe_and_ey AS
SELECT stk.symbol, datetime as close_date, (close/ttm) AS PEratio, (ttm/close) AS EarnYield
FROM stocks AS stk
LEFT JOIN quarter_eps AS eps
ON stk.symbol = eps.symbol
AND fiscalDateEnding = (
    SELECT MAX(fiscalDateEnding)
    FROM quarter_eps
    WHERE fiscalDateEnding <= datetime
    AND symbol = stk.symbol);

/* Simple Moving Averages: */
DROP VIEW IF EXISTS vw_SMA;
CREATE VIEW vw_SMA AS
SELECT symbol, datetime AS close_date,
       SUM(close) OVER (PARTITION BY symbol ORDER BY datetime DESC ROWS BETWEEN CURRENT ROW AND 9 FOLLOWING) / 10 as SMA10,
       SUM(close) OVER (PARTITION BY symbol ORDER BY datetime DESC ROWS BETWEEN CURRENT ROW AND 19 FOLLOWING) / 20 as SMA20,
       SUM(close) OVER (PARTITION BY symbol ORDER BY datetime DESC ROWS BETWEEN CURRENT ROW AND 49 FOLLOWING) / 50 as SMA50
FROM stocks;

/* Gain/Loss for RSI: */
DROP VIEW IF EXISTS vw_gainloss14d;
CREATE VIEW vw_gainloss14d AS
WITH cte AS (
    SELECT symbol, datetime AS close_date, close AS close_price,
           LEAD(close,1) OVER (PARTITION BY symbol ORDER BY datetime DESC) prev_close
           FROM stocks)
SELECT symbol, close_date, close_price,
       CASE WHEN (close_price - prev_close) > 0 THEN (close_price - prev_close) ELSE 0 END gain,
       CASE WHEN (close_price - prev_close) < 0 THEN (prev_close - close_price) ELSE 0 END loss,
       AVG(CASE WHEN (close_price - prev_close) > 0 THEN (close_price - prev_close) ELSE 0 END)
         OVER (PARTITION BY symbol ORDER BY close_date DESC ROWS BETWEEN CURRENT ROW AND 13 FOLLOWING) avg_gain14,
       AVG(CASE WHEN (close_price - prev_close) < 0 THEN (prev_close - close_price) ELSE 0 END)
         OVER (PARTITION BY symbol ORDER BY close_date DESC ROWS BETWEEN CURRENT ROW AND 13 FOLLOWING) avg_loss14
FROM cte
GROUP BY symbol, close_date
ORDER BY close_date DESC;

/* Relative Strength Index: */
DROP VIEW IF EXISTS vw_rsi;
CREATE VIEW vw_rsi AS
WITH RECURSIVE cte_gainloss AS (
    SELECT ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY close_date) AS rownum, *
    FROM vw_gainloss14d
    WHERE close_date > date('now','-500 days')
), cte_recur AS (
    SELECT *, avg_gain14 AS avg_gain, avg_loss14 AS avg_loss
    FROM cte_gainloss
    WHERE rownum = 14
    UNION ALL
    SELECT curr.*, (prev.avg_gain * 13 + curr.gain) / 14, (prev.avg_loss * 13 + curr.loss) / 14
    FROM cte_gainloss AS curr INNER JOIN cte_recur AS prev
    ON curr.rownum = prev.rownum + 1 AND curr.symbol = prev.symbol
)
SELECT symbol, close_date, close_price, avg_gain, avg_loss,
       (avg_gain / avg_loss) AS RS, 100 - (100 / (1 + (avg_gain / avg_loss))) AS RSI
FROM cte_recur
ORDER BY close_date DESC;

/* SMA used for calc EMA: */
DROP VIEW IF EXISTS vw_macd_sma;
CREATE VIEW vw_macd_sma AS
SELECT symbol, datetime AS close_date, close AS close_price,
       SUM(close) OVER (PARTITION BY symbol ORDER BY datetime DESC ROWS BETWEEN CURRENT ROW AND 25 FOLLOWING) / 26 AS SMA26,
       SUM(close) OVER (PARTITION BY symbol ORDER BY datetime DESC ROWS BETWEEN CURRENT ROW AND 11 FOLLOWING) / 12 AS SMA12
FROM stocks;

/* EMA26: */
DROP VIEW IF EXISTS vw_macd_ema26;
CREATE VIEW vw_macd_ema26 AS
WITH RECURSIVE cte_sma AS (
    SELECT ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY close_date) AS rownum, symbol, close_date, close_price, SMA26
    FROM vw_macd_sma
    WHERE close_date > date('now','-500 days')
), cte_recur AS (
    SELECT *, SMA26 AS EMA26
    FROM cte_sma
    WHERE rownum = 26
    UNION ALL
    SELECT curr.*, (curr.close_price * (2.0/27)) + (prev.EMA26 * (1-2.0/27))
    FROM cte_sma AS curr
    INNER JOIN cte_recur AS prev
    ON curr.rownum = prev.rownum + 1
    AND curr.symbol = prev.symbol
)
SELECT * FROM cte_recur ORDER BY close_date DESC;

/* EMA12: */
DROP VIEW IF EXISTS vw_macd_ema12;
CREATE VIEW vw_macd_ema12 AS
WITH RECURSIVE cte_sma AS (
    SELECT ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY close_date) AS rownum, symbol, close_date, close_price, SMA12
    FROM vw_macd_sma
    WHERE close_date > date('now','-500 days')
), cte_recur AS (
    SELECT *, SMA12 AS EMA12
    FROM cte_sma
    WHERE rownum = 12
    UNION ALL
    SELECT curr.*, (curr.close_price * (2.0/13)) + (prev.EMA12 * (1-2.0/13))
    FROM cte_sma AS curr
    INNER JOIN cte_recur AS prev
    ON curr.rownum = prev.rownum + 1
    AND curr.symbol = prev.symbol
)
SELECT * FROM cte_recur ORDER BY close_date DESC;

/*  MACD: */
DROP VIEW IF EXISTS vw_macd;
CREATE VIEW vw_macd AS
SELECT ema26.symbol, ema26.close_date, ema26.close_price, (EMA12-EMA26) AS MACD
FROM vw_macd_ema26 ema26
INNER JOIN vw_macd_ema12 ema12
ON ema26.symbol = ema12.symbol
AND ema26.close_date = ema12.close_date
ORDER BY ema26.close_date DESC;

/*  MACD w/ Signal */
DROP VIEW IF EXISTS vw_macd2;
CREATE VIEW vw_macd2 AS
WITH RECURSIVE cte_macd AS (
    SELECT ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY close_date) AS rownum, symbol, close_date, close_price, MACD
    FROM vw_macd
), cte_recur AS (
    SELECT *, MACD AS signal
    FROM cte_macd
    WHERE rownum = 9
    UNION ALL
    SELECT curr.*, (curr.MACD * (2.0/10)) + (prev.signal * (1-2.0/10))
    FROM cte_macd AS curr
    INNER JOIN cte_recur AS prev
    ON curr.rownum = prev.rownum + 1
    AND curr.symbol = prev.symbol
)
SELECT symbol, close_date, close_price, MACD, signal FROM cte_recur ORDER BY close_date DESC;
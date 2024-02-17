# METADATA / DATA DICTIONARY
## note
(Note: SQLite uses dynamic data types, so data types here are provided as suggestions for other SQL DBs.)

## stocks
Main fact table. Each record contains the stock price values for each stock symbol on open, close, high, low, and trading volume for each day. Primary key is a composite key on the date and symbol.
| column | data type | description |
| --- | --- | --- |
| datetime | datetime | date of trades |
| symbol | varchar(5) | instrument symbol (ticker) |
| open | decimal | opening price of the day |
| high | decimal | highest price of the day |
| low | decimal | lowest price of the day |
| close | decimal | closing price at end of the day |
| volume | int | trading volume for this day |

## stock_staging
Staging table used to load new data into the DB. We can verify/sanitize/wrangle data here before transferring it into the main table.
| column | data type | description |
| --- | --- | --- |
| datetime | datetime | date of trades |
| symbol | varchar(5) | instrument symbol (ticker) |
| open | decimal | opening price of the day |
| high | decimal | highest price of the day |
| low | decimal | lowest price of the day |
| close | decimal | closing price at end of the day |
| volume | int | trading volume for this day |

## stock_descr
Dimension table containing some details about each stock symbol, such as the company name and the particular exchange. Primary key is a composite key on the symbol and exchange name.
| column | data type | description |
| --- | --- | --- |
| symbol | varchar(5) | instrument symbol (ticker) |
| name | varchar(60) | full name of instrument |
| currency | varchar(5) | currency of the instrument according to the ISO 4217 standard |
| exchange | varchar(10) | name of exchange where symbol is traded |
| mic_code | varchar(10) | market identifier code (ISO 10383 standard) |
| country | varchar(60) | country where exchange is located |
| type | varchar(60) | common issue type |

## annual_eps
Fact table for the annual EPS data. We may cross reference this to the stocks table when performing data analysis.
| column | data type | description |
| --- | --- | --- |
| symbol | varchar(5) | instrument symbol (ticker) |
| fiscalDateEnding | datetime | Fiscal Year end date |
| reportedEPS | decimal | Earnings Per Share (EPS) as reported by company |

## annual_eps_staging
Staging table for the annual EPS data initially loaded into the DB.
| column | data type | description |
| --- | --- | --- |
| symbol | varchar(5) | instrument symbol (ticker) |
| fiscalDateEnding | datetime | Fiscal Year end date |
| reportedEPS | decimal | Earnings Per Share (EPS) as reported by company |

## quarter_eps
Fact table for the quarterly EPS data. We may cross reference this to the stocks table when performing data analysis.
| column | data type | description |
| --- | --- | --- |
| symbol | varchar(5) | instrument symbol (ticker) |
| fiscalDateEnding | datetime | Date Last day of Fiscal Quarter |
| reportedEPS | decimal | Earnings Per Share (EPS) as reported by company |
| estimatedEPS | decimal | Earnings Per Share (EPS) as estimated by analysts |
| surprise | decimal | Deviation between reportedEPS and estimatedEPS |
| surprisePercentage | decimal | Deviation between reportedEPS and estimatedEPS in percent |

## quarter_eps_staging
Staging table for the quarterly EPS data initially loaded into the DB.
| column | data type | description |
| --- | --- | --- |
| symbol | varchar(5) | instrument symbol (ticker) |
| fiscalDateEnding | datetime | Date Last day of Fiscal Quarter |
| reportedEPS | decimal | Earnings Per Share (EPS) as reported by company |
| estimatedEPS | decimal | Earnings Per Share (EPS) as estimated by analysts |
| surprise | decimal | Deviation between reportedEPS and estimatedEPS |
| surprisePercentage | decimal | Deviation between reportedEPS and estimatedEPS in percent |

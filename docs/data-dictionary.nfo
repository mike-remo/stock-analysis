DB SCHEMA:
# METADATA / DATA DICTIONARY:
| stocks | the main fact table. Each record contains the stock price values for each stock symbol on open, close, high, low, and trading volume for each day. Primary key is a composite key on the date and symbol. |
| column | description |
| --- | --- |
| datetime | date of trades |
| symbol | instrument symbol (ticker) |
| open | opening price of the day |
| high | highest price of the day |
| low | lowest price of the day |
| close | closing price at end of the day |
| volume | trading volume for this day |

| stock_staging | staging table used to load new data into the DB. We can verify/sanitize/wrangle data here before transferring it into the main table. |
| column | description |
| --- | --- |
| datetime | date of trades |
| symbol | instrument symbol (ticker) |
| open | opening price of the day |
| high | highest price of the day |
| low | lowest price of the day |
| close | closing price at end of the day |
| volume | trading volume for this day |

| stock_descr | dimension table containing some details about each stock symbol, such as the company name and the particular exchange. Primary key is a composite key on the symbol and exchange name. |
| column | description |
| --- | --- |
| symbol | instrument symbol (ticker) |
| name | full name of instrument |
| currency | currency of the instrument according to the ISO 4217 standard |
| exchange | name of exchange where symbol is traded |
| mic_code | market identifier code (ISO 10383 standard) |
| country | country where exchange is located |
| type | common issue type |

| annual_eps | fact table for the annual EPS data. We may cross reference this to the stocks table when perfmoring data analysis. |
| column | description |
| --- | --- |
| symbol | instrument symbol (ticker) |
| fiscalDateEnding | Fiscal Year end date |
| reportedEPS | Earnings Per Share (EPS) as reported by company |

| annual_eps_staging | staging table for the annual EPS data intially loaded into the DB. |
| column | description |
| --- | --- |
| symbol | instrument symbol (ticker) |
| fiscalDateEnding | Fiscal Year end date |
| reportedEPS | Earnings Per Share (EPS) as reported by company |

| quarter_eps | fact table for the quarterly EPS data. We may cross reference this to the stocks table when perfmoring data analysis. |
| column | description |
| --- | --- |
| symbol | instrument symbol (ticker) |
| fiscalDateEnding | Date Last day of Fiscal Quarter |
| reportedEPS | Earnings Per Share (EPS) as reported by company |
| estimatedEPS | Earnings Per Share (EPS) as estimated by analysts |
| surprise | Deviation between reportedEPS and estimatedEPS |
| surprisePercentage | Deviation between reportedEPS and estimatedEPS in percent |

| quarter_eps_staging | staging table for the quarterly EPS data intially loaded into the DB. |
| column | description |
| --- | --- |
| symbol | instrument symbol (ticker) |
| fiscalDateEnding | Date Last day of Fiscal Quarter |
| reportedEPS | Earnings Per Share (EPS) as reported by company |
| estimatedEPS | Earnings Per Share (EPS) as estimated by analysts |
| surprise | Deviation between reportedEPS and estimatedEPS |
| surprisePercentage | Deviation between reportedEPS and estimatedEPS in percent |

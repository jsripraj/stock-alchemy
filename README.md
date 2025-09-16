# Stock Screener

A full-stack stock screener that lets users define and evaluate custom financial formulas over time.

## Overview
- Python ETL pipeline ingests SEC filings and historical stock prices into a relational database (Postgres).  
- Next.js front-end (in progress) for querying, visualizing, and screening stocks.  
- Supports user-defined formulas to track financial metrics over time.

## Tech Stack
Python, Postgres, Next.js, [yfinance](https://github.com/ranaroussi/yfinance), [EDGAR API](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)

## Future Work  
- Implement user authentication
- Allow users to save custom formulas
- Add more financial concepts and time granularity

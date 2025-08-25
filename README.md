# Stock Screener

A full-stack stock screener that lets users define and evaluate custom financial formulas over time.

## Overview
- ETL pipeline ingests SEC filings and historical stock prices into a relational database (MySQL → Postgres).  
- Next.js front-end (in progress) for querying, visualizing, and screening stocks.  
- Supports user-defined formulas to track financial metrics over time.

## Tech Stack
Python, MySQL/Postgres, Next.js, [yfinance](https://github.com/ranaroussi/yfinance), [EDGAR API](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)

## Future Work
- Complete migration to Postgres  
- Implement user authentication and allow users to save custom formulas
- Optimize ETL performance for large datasets

# StockAlchemy
[stockalchemy.vercel.app](https://stockalchemy.vercel.app/)

A full-stack stock screener that lets users define and evaluate custom financial formulas over time.

## Overview
- Python ETL pipeline ingests SEC filings and historical stock prices into a Postgres database.  
- Next.js front-end (in progress) for querying, visualizing, and screening stocks.  
- Supports user-defined formulas to filter on financial metrics over time.

## Tech Stack
- **Languages & Frameworks:** Python, TypeScript, React, Next.js, Tailwind CSS  
- **Database:** Postgres  
- **APIs:** [EDGAR](https://www.sec.gov/search-filings/edgar-application-programming-interfaces), [yfinance](https://github.com/ranaroussi/yfinance)

## Future Work  
- Implement user authentication
- Allow users to save custom formulas
- Add more financial concepts and increase time granularity

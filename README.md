# Quanta-Mentals · Earnings Call Sentiment

MMA 823 Analytics for Financial Markets, Smith School of Business, Queen's University.

A research app that scores the language of earnings calls, compares it with a benchmark of 22 calls (Bank and Tech), and checks how the stock moved around each call.

## Pages

| Page | Project part |
|---|---|
| Home | The brief, the four-step method, and the headline findings |
| Analyze a call | Part 5. Upload or paste any transcript to get its tone, a sector-adjusted tone, how tone changes into the Q&A, management conviction, and the live price reaction |
| Benchmark explorer | Parts 2–3. Rankings, how the methods agree, scripted vs. live tone, tone through the call, analyst pushback |
| Market reaction | Part 4. Event study (±21 trading days vs. SPY or a sector ETF), correlations, and a long-short test |
| Stock reports | Part 1. One-page profile: business, valuation ratios, price vs. S&P 500, risk, and call sentiment |
| Method & decisions | Methods, measures, sector dictionaries, executive decisions, assumptions, limitations, next steps, and a glossary |

## Run locally

```
pip install -r requirements.txt
streamlit run app.py
```

## Structure

```
app.py              page router
ui.py               styling, components and glossary
data_access.py      cached data loaders
market.py           Yahoo Finance prices and event-study maths
sentiment_core.py   transcript parsing and scoring (same as the notebooks)
views/              one file per page
data/               benchmark scores, sector map, sector dictionary
```

To add a sector, add its tickers to `data/sector_map.csv` and its routine jargon to `data/sector_lexicon.csv`.

## Automated pipeline

`pipeline/run_pipeline.py` does every loading step in one go: it scores all transcripts (same code as the notebooks), downloads prices and runs the event study, trains a model on 2023 calls and tests it on 2024 calls, and writes only derived numbers to `data/`. It runs automatically from the team's **private** transcripts repository through a GitHub Action whenever transcripts are uploaded there, then pushes the updated `data/` files here. To run it by hand:

```
pip install -r requirements.txt scikit-learn
python pipeline/run_pipeline.py --transcripts path/to/transcripts --out data
```

## Data and licensing

Bloomberg and LSEG transcripts are licensed and are **not** included in this repository. Only derived scores are published. Prices come live from Yahoo Finance. Yahoo sometimes limits requests from shared hosts such as Streamlit Cloud. For a reliable demo, run `python scripts/make_prices.py AMZN` on your own computer (add any extra tickers you plan to show), then commit `data/prices.csv`; the app uses that file whenever it covers the tickers and dates needed.

Research prototype. Not investment advice.

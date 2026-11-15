# Earnings Call Sentiment Analyzer

**MMA 823 Analytics for Financial Markets · Smith School of Business, Queen's University**

Upload an earnings call transcript and the app measures how management talks: the overall tone, how tone changes from the scripted presentation to the live Q&A with analysts, how tone moves through the call, and how well management holds its message under questioning. Each call is placed against a benchmark of real earnings calls and flagged as **Positive**, **Neutral** or **Negative**.

**Live demo:** _add your Streamlit Cloud link here_

## How it works

1. **Read.** The transcript (Bloomberg or LSEG PDF, or pasted text) is split by speaker into the prepared presentation, analyst questions and management answers. Legal disclaimers and operator remarks are removed.
2. **Score.** Three methods score the language:
   - the **Loughran-McDonald** finance dictionary (positive, negative and uncertainty words), the main measure;
   - **VADER** and **TextBlob**, two general-purpose sentiment tools used as a cross-check.
3. **Compare.** The scores are standardised against the benchmark calls in `call_sentiment.csv`, ideally against calls from the same sector.

Key measures:

| Measure | Meaning |
|---|---|
| Tone | Positive minus negative finance words per 100 words |
| Overall score | Average of the three methods on a common scale (0 = average benchmark call) |
| Tone change into Q&A | Management tone in live answers minus tone in the scripted presentation |
| Management conviction | Answers more positive than the questions, little hedging, tone holding up in the Q&A |

## Sector coverage (please read)

The method works for earnings calls from **any sector**. The comparison benchmark is currently **calibrated on Bank and Tech calls**, so results for those sectors are the most reliable. A call from another sector is scored the same way but compared with all benchmark calls, and its relative scores should be read with care. Expanding the benchmark to more sectors is the next step: add tickers to `sector_map.csv` and scored calls to `call_sentiment.csv`.

## Method notes and limitations

- **Dictionary adapted to calls.** Loughran-McDonald counts *question(s)* as negative because in annual reports it signals doubt. On a call it is neutral ("my question is..."), so it is removed.
- **Words, not meaning.** Dictionary methods miss context and sarcasm; only simple negation ("not strong") is handled.
- **Text only.** Voice, pauses and hesitation are not captured.
- **Small benchmark.** 22 calls (18 Tech, 4 Bank), so classifications are relative to this sample.
- **Not investment advice.** The project also tests whether tone relates to post-call stock returns; tone alone is not a trading signal.

## Data

The Bloomberg transcripts used to build the benchmark are licensed and are **not included** in this repository. Only derived scores are published (`call_sentiment.csv`, `segment_tone.csv`). To try the app, upload a transcript you have access to or paste the text of any earnings call.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Files

| File | Purpose |
|---|---|
| `app.py` | Streamlit app |
| `sentiment_core.py` | Transcript parsing and scoring (same logic as the project notebook) |
| `call_sentiment.csv` | Benchmark scores, one row per call |
| `segment_tone.csv` | Benchmark tone for each tenth of each call |
| `sector_map.csv` | Ticker to sector; add rows for new companies |
| `.streamlit/config.toml` | Colours |

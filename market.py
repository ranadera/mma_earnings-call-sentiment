"""Live market data (Yahoo Finance via yfinance) and the event-study calculations.

If a file data/prices.csv exists (dates in the first column, one adjusted-close column per ticker),
it is used instead of downloading, which makes the demo independent of a live connection.
"""
import os

import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats

MARKET = 'SPY'
SECTOR_ETF = {'Tech': 'XLK', 'Bank': 'KBE'}
WINDOWS = {'Day (0 to +1)': (0, 1), 'Week (0 to +5)': (0, 5), 'Month (0 to +21)': (0, 21)}
LOCAL_PRICES = os.path.join('data', 'prices.csv')


def _download(tickers, start, end):
    import yfinance as yf
    df = yf.download(list(tickers), start=start, end=end, auto_adjust=True, progress=False, threads=True)
    if df is None or df.empty:
        return None
    close = df['Close'] if 'Close' in df.columns.get_level_values(0) else df
    if isinstance(close, pd.Series):
        close = close.to_frame(tickers[0])
    close.index = pd.to_datetime(close.index).tz_localize(None)
    return close.dropna(how='all')


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def prices(tickers, start, end):
    """Adjusted closing prices. Returns (DataFrame or None, message)."""
    tickers = tuple(sorted(set(tickers)))
    if os.path.exists(LOCAL_PRICES):
        local = pd.read_csv(LOCAL_PRICES, index_col=0, parse_dates=True)
        if all(t in local.columns for t in tickers) and local.index.min() <= pd.Timestamp(start) + pd.Timedelta(days=10):
            return local[list(tickers)], 'saved price file'
    try:
        close = _download(tickers, start, end)
    except Exception as e:
        return None, f'Live price data is unavailable right now ({type(e).__name__}).'
    if close is None or close.empty:
        return None, 'Live price data is unavailable right now (no data returned).'
    return close, 'Yahoo Finance (live)'


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def company_info(ticker):
    try:
        import yfinance as yf
        return yf.Ticker(ticker).info or {}
    except Exception:
        return {}


def yahoo_sector(ticker):
    """Map Yahoo Finance's sector and industry to our sector groups (Bank, Tech) or return Yahoo's sector name."""
    info = company_info(ticker) if ticker else {}
    sector, industry = info.get('sector') or '', info.get('industry') or ''
    if 'bank' in industry.lower():
        return 'Bank'
    if sector == 'Technology' or industry.startswith('Internet') or 'software' in industry.lower() or 'semiconductor' in industry.lower():
        return 'Tech'
    return sector or None


def event_window(px, ticker, call_date, benchmark=MARKET, window=21):
    """Daily returns, abnormal returns and their running total from -window to +window trading days."""
    if px is None or ticker not in px.columns or benchmark not in px.columns:
        return None
    rets = px[[ticker, benchmark]].pct_change()
    days = rets.index
    t0 = days.searchsorted(pd.Timestamp(call_date))
    rows = []
    for k in range(-window, window + 1):
        i = t0 + k
        if 0 < i < len(days) and pd.notna(rets[ticker].iloc[i]) and pd.notna(rets[benchmark].iloc[i]):
            rows.append({'day': k, 'date': days[i], 'ret': rets[ticker].iloc[i], 'bench_ret': rets[benchmark].iloc[i]})
    if not rows:
        return None
    ev = pd.DataFrame(rows)
    ev['abn_ret'] = ev['ret'] - ev['bench_ret']
    pre = ev[ev['day'] < 0].copy()
    post = ev[ev['day'] >= 0].copy()
    pre['car'] = -(pre['abn_ret'][::-1].cumsum()[::-1] - pre['abn_ret'])
    post['car'] = post['abn_ret'].cumsum()
    return pd.concat([pre, post]).sort_values('day')


def car(ev, first, last):
    if ev is None:
        return np.nan
    w = ev[(ev['day'] >= first) & (ev['day'] <= last)]
    if w.empty or w['day'].max() < last:
        return np.nan
    return w['abn_ret'].sum()


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def benchmark_event_study(calls, benchmark=MARKET, window=21):
    """CARs for every benchmark call. calls: DataFrame with call_id, ticker, call_date."""
    tickers = list(calls['ticker'].unique()) + [benchmark]
    start = (calls['call_date'].min() - pd.Timedelta(days=60)).strftime('%Y-%m-%d')
    end = (calls['call_date'].max() + pd.Timedelta(days=60)).strftime('%Y-%m-%d')
    px, source = prices(tuple(tickers), start, end)
    if px is None:
        return None, None, source
    rows, paths = [], []
    for _, c in calls.iterrows():
        ev = event_window(px, c['ticker'], c['call_date'], benchmark, window)
        if ev is None:
            continue
        rows.append({'call_id': c['call_id'], 'car_pre': car(ev, -window, -1), 'car_day': car(ev, 0, 1),
                     'car_week': car(ev, 0, 5), 'car_month': car(ev, 0, window), 'hold_week': car(ev, 2, 5), 'car_drift': car(ev, 2, window)})
        paths.append(ev.assign(call_id=c['call_id']))
    if not rows:
        return None, None, 'No price data matched the benchmark calls.'
    return pd.DataFrame(rows), pd.concat(paths), source


def correlations(data, measures, windows):
    out = []
    for m in measures:
        for w in windows:
            d = data[[m, w]].dropna()
            if len(d) < 5:
                continue
            rho, p = stats.spearmanr(d[m], d[w])
            out.append({'measure': m, 'window': w, 'rho': rho, 'p': p, 'n': len(d)})
    return pd.DataFrame(out)


def long_short(data, signal_col, ret_col):
    d = data[[signal_col, ret_col]].dropna()
    long, short = d.loc[d[signal_col] == 'Positive', ret_col], d.loc[d[signal_col] == 'Negative', ret_col]
    if len(long) < 2 or len(short) < 2:
        return None
    t, p = stats.ttest_ind(long, short, equal_var=False)
    return {'n_long': len(long), 'n_short': len(short), 'long': long.mean(), 'short': short.mean(),
            'spread': long.mean() - short.mean(), 'hit_long': (long > 0).mean(), 'hit_short': (short < 0).mean(), 'p': p}


def stock_stats(px, ticker, benchmark=MARKET):
    p = px[ticker].dropna().iloc[-252:]
    m = px[benchmark].reindex(p.index)
    r, mr = p.pct_change().dropna(), m.pct_change().dropna()
    r, mr = r.align(mr, join='inner')
    return {'price': p.iloc[-1], 'as_of': p.index[-1], 'ret_1y': p.iloc[-1] / p.iloc[0] - 1, 'mkt_1y': m.iloc[-1] / m.iloc[0] - 1,
            'vol_1y': r.std() * np.sqrt(252), 'vol_30d': r.iloc[-21:].std() * np.sqrt(252),
            'max_dd': (p / p.cummax() - 1).min(), 'beta': r.cov(mr) / mr.var(), 'high': p.max(), 'low': p.min()}

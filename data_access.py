"""Cached access to the benchmark data shipped with the app."""
import os

import pandas as pd
import streamlit as st

import sentiment_core as sc

DATA = 'data'
SHORT_NAMES = {
    'AAPL': 'Apple', 'CMA': 'Comerica', 'SIVB': 'SVB Financial',
    'AMD': 'AMD', 'GOOGL': 'Alphabet', 'AMZN': 'Amazon', 'AVGO': 'Broadcom', 'C': 'Citigroup', 'CRWV': 'CoreWeave',
    'GS': 'Goldman Sachs', 'JPM': 'JPMorgan', 'KLAC': 'KLA', 'META': 'Meta', 'MSFT': 'Microsoft', 'MPWR': 'Monolithic Power',
    'ORCL': 'Oracle', 'PANW': 'Palo Alto', 'QCOM': 'Qualcomm', 'SNDK': 'Sandisk', 'WFC': 'Wells Fargo', 'WDC': 'Western Digital',
    'NVDA': 'NVIDIA', 'BAC': 'Bank of America', 'MS': 'Morgan Stanley', 'PNC': 'PNC', 'USB': 'U.S. Bancorp', 'TFC': 'Truist',
    'COF': 'Capital One', 'FITB': 'Fifth Third', 'RF': 'Regions', 'KEY': 'KeyCorp', 'CFG': 'Citizens', 'HBAN': 'Huntington',
    'ALLY': 'Ally', 'FLG': 'Flagstar', 'BANC': 'Banc of California', 'WAL': 'Western Alliance', 'ZION': 'Zions', 'MTB': 'M&T'}


@st.cache_resource
def lm():
    return sc.load_lm(os.path.join(DATA, 'LM_MasterDictionary.csv'))


@st.cache_data
def benchmark():
    b = pd.read_csv(os.path.join(DATA, 'call_sentiment.csv'))
    b = b[b['is_transcript'] == True].copy()
    b['call_date'] = pd.to_datetime(b['call_date'])
    b['name'] = b['ticker'].map(SHORT_NAMES).fillna(b['company'])
    b['label'] = b['name'] + ' (' + b['call_date'].dt.strftime('%b %Y') + ')'
    adj_path = os.path.join(DATA, 'benchmark_sector_tone.csv')
    if os.path.exists(adj_path):
        adj = pd.read_csv(adj_path)[['call_id', 'lm_tone_sector']]
        b = b.merge(adj, on='call_id', how='left')
    return b


@st.cache_data
def segments():
    path = os.path.join(DATA, 'segment_tone.csv')
    return pd.read_csv(path) if os.path.exists(path) else None


@st.cache_data
def sector_map():
    return sc.load_sector_map(os.path.join(DATA, 'sector_map.csv'))


@st.cache_data
def lexicon():
    return sc.load_sector_lexicon(os.path.join(DATA, 'sector_lexicon.csv'))


def calibrated_sectors(bench, min_calls=3):
    counts = bench['sector'].value_counts()
    return sorted(counts[counts >= min_calls].index), counts

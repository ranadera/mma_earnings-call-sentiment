"""Earnings Call Sentiment Analyzer (MMA 823, Part 5).

Run from this folder with:  streamlit run app.py
"""
import glob
import os
from collections import Counter

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import sentiment_core as sc

st.set_page_config(page_title='Earnings Call Sentiment Analyzer', layout='wide')

SMITH_BLUE, AZURE = '#071D49', '#0047BB'
SIGNAL_COLORS = {'Positive': '#578100', 'Neutral': '#858E9F', 'Negative': '#C8215D'}
MIN_PEERS = 3
PART_NAMES = {'presentation': 'Prepared presentation', 'qa_management': 'Management answers (Q&A)', 'qa_analyst': 'Analyst questions (Q&A)'}


@st.cache_resource
def load_lm():
    return sc.load_lm('LM_MasterDictionary.csv')


@st.cache_data
def load_benchmark():
    b = pd.read_csv('call_sentiment.csv')
    b = b[b['is_transcript'] == True].copy()
    b['label'] = b['ticker'] + ' ' + pd.to_datetime(b['call_date']).dt.strftime('%b %Y')
    return b


@st.cache_data
def load_sectors():
    return sc.load_sector_map('sector_map.csv')


@st.cache_data
def load_benchmark_segments():
    if not os.path.exists('segment_tone.csv'):
        return None
    return pd.read_csv('segment_tone.csv')


@st.cache_data(show_spinner='Reading and scoring the transcript...')
def analyse(name, data):
    raw = sc.read_text(name, data)
    meta = sc.get_meta(raw)
    fmt, turns = sc.parse(raw)
    scored = sc.score_turns(turns, load_lm())
    segs, qa_start = sc.segments(scored, load_lm())
    return meta, fmt, scored, segs, qa_start


bench = load_benchmark()
bench_segs = load_benchmark_segments()
sector_map = load_sectors()
counts = bench['sector'].value_counts()
calibrated = sorted(counts[counts >= MIN_PEERS].index)
covered = ' and '.join([', '.join(calibrated[:-1]), calibrated[-1]] if len(calibrated) > 1 else calibrated)
covered_detail = ', '.join(f'{counts[s]} {s.lower()}' for s in calibrated)

st.markdown(f"<h1 style='color:{SMITH_BLUE};margin-bottom:0'>Earnings Call Sentiment Analyzer</h1>", unsafe_allow_html=True)
st.caption(f'MMA 823 · Upload an earnings call transcript to measure management tone and compare it with {len(bench)} benchmark calls.')
st.markdown(
    f"<div style='border:1px solid #B9C9E8;border-left:6px solid {AZURE};background:#F3F6FA;padding:12px 16px;margin:6px 0 14px;color:{SMITH_BLUE}'>"
    f"<b>Works with earnings calls from any sector.</b> The benchmark is currently calibrated on <b>{covered}</b> calls "
    f"({covered_detail}), so comparisons for those sectors are the most reliable. Calls from other sectors are scored "
    f"the same way but compared with all {len(bench)} benchmark calls, and should be read with care until more sectors "
    f"are added to the benchmark. Next step: expand the benchmark to more sectors.</div>",
    unsafe_allow_html=True)

with st.sidebar:
    st.header('1. Transcript')
    samples = sorted(p for p in glob.glob('transcripts/*/*.pdf') if 'Summary' not in p)
    inputs = ['Upload a file', 'Paste text'] + (['Use a sample transcript'] if samples else [])
    source = st.radio('Input', inputs, label_visibility='collapsed')
    name, data = None, None
    if source == 'Upload a file':
        f = st.file_uploader('PDF or text file', type=['pdf', 'txt'])
        if f is not None:
            name, data = f.name, f.getvalue()
    elif source == 'Paste text':
        text = st.text_area('Paste the transcript', height=260,
                            help='If the text contains a heading such as "Questions And Answers", the app splits the presentation from the Q&A.')
        if text.strip():
            name, data = 'pasted.txt', text.encode('utf-8')
    else:
        pick = st.selectbox('Sample', samples, format_func=lambda p: os.path.basename(os.path.dirname(p)) + ' · ' + os.path.basename(p).split('_Earnings')[0].replace('_', ' '))
        if pick:
            name, data = pick, open(pick, 'rb').read()

    st.header('2. Compare with')
    sector_choice = st.selectbox('Benchmark group', ['Auto-detect'] + calibrated + ['All benchmark calls'],
                                 help='Each sector has its own vocabulary (banks say credit, losses and reserves, which the finance dictionary counts as negative), so a call is best compared with its own sector. Auto-detect uses sector_map.csv.')

    st.divider()
    st.caption('Tone uses the Loughran-McDonald finance dictionary. The overall score averages it with VADER and TextBlob, on the same scale as the benchmark calls in `call_sentiment.csv`.')

if data is None:
    st.info('Choose a transcript in the sidebar to begin: upload a Bloomberg or LSEG PDF, or paste the text of any earnings call.')
    c1, c2, c3 = st.columns(3)
    c1.markdown('**1. Read**  \nThe app extracts the text and splits it into the prepared presentation, analyst questions and management answers.')
    c2.markdown('**2. Score**  \nIt counts positive, negative and uncertain finance words and cross-checks with two general sentiment tools.')
    c3.markdown('**3. Compare**  \nIt places the call against the benchmark calls and flags it as Positive, Neutral or Negative.')
    st.stop()

meta, fmt, scored, segs, qa_start = analyse(name, data)
if scored.empty or scored['n_words'].sum() < 200:
    st.error('Not enough text could be read from this file. If it is a scanned PDF, it needs text recognition (OCR) first.')
    st.stop()

detected = sector_map.get(meta['ticker'].upper()) if meta['ticker'] else None
if sector_choice == 'Auto-detect':
    sector = detected if detected in calibrated else None
elif sector_choice == 'All benchmark calls':
    sector = None
else:
    sector = sector_choice
res = sc.score_call(scored, bench, sector)
peers = bench[bench['sector'] == sector] if sector else bench
peer_name = f'{sector} average' if sector else 'Benchmark average'
peer_short = f'{sector.lower()} average' if sector else 'benchmark average'

title = meta['company'] or os.path.basename(name)
sub = ' · '.join(x for x in [meta['ticker'], detected and f'{detected} sector', meta['call_date'], f'{fmt} format',
                              f'compared with {sector.lower()} calls' if sector else 'compared with all benchmark calls'] if x)
st.markdown(f"<h2 style='color:{SMITH_BLUE};margin-bottom:0'>{title}</h2>", unsafe_allow_html=True)
st.caption(sub)
if sector_choice == 'Auto-detect' and sector is None:
    if detected:
        st.info(f'{meta["ticker"]} is in the {detected} sector, which is not in the benchmark yet, so it is compared with all {len(bench)} benchmark calls. Read the relative scores with care.')
    else:
        st.info(f'The sector of this company was not recognised (add its ticker to sector_map.csv), so it is compared with all {len(bench)} benchmark calls.')
if fmt.startswith('Plain'):
    st.warning('Speakers could not be identified in this text, so analyst questions and management answers cannot be separated. The overall tone is still valid; Q&A measures are limited.')

pct = (bench['composite'] < res['composite']).mean()
color = SIGNAL_COLORS[res['signal']]
st.markdown(
    f"<div style='border-left:6px solid {color};background:#F3F6FA;padding:14px 18px;border-radius:0;margin:8px 0 18px'>"
    f"<span style='font-size:13px;color:#556075'>SENTIMENT SIGNAL</span><br>"
    f"<span style='font-size:28px;font-weight:800;color:{color}'>{res['signal']}</span>"
    f"<span style='font-size:16px;color:{SMITH_BLUE}'> &nbsp;· more positive than {pct:.0%} of the {len(bench)} benchmark calls</span></div>",
    unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
m1.metric('Tone', f"{res['lm_tone']:.2f}", f"{res['lm_tone'] - peers['lm_tone'].mean():+.2f} vs {peer_short}",
          help='Positive minus negative finance words per 100 words (Loughran-McDonald dictionary).')
m2.metric('Overall score', f"{res['composite']:+.2f}", f"{res['sector_score']:+.2f} vs {sector.lower()} peers" if sector and np.isfinite(res['sector_score']) else None,
          help='Average of three methods (finance dictionary, VADER, TextBlob), standardised against the benchmark calls. 0 = average call.')
m3.metric('Tone change into Q&A', f"{res['tone_shift']:+.2f}" if np.isfinite(res['tone_shift']) else 'n/a',
          help='Management tone in Q&A answers minus tone in the prepared presentation. Negative = the message softened under questioning.')
m4.metric('Management conviction', f"{res['conviction_score']:+.2f}" if np.isfinite(res['conviction_score']) else 'n/a',
          help='How well management held its message: answers more positive than the questions, little hedging, tone holding up in Q&A. 0 = average call.')

left, right = st.columns(2)

with left:
    st.subheader('Tone by part of the call')
    part_rows = []
    for p, label in PART_NAMES.items():
        g = scored[scored['part'] == p]
        if g['n_words'].sum() > 0:
            tone = (g['lm_pos'].sum() - g['lm_neg'].sum()) / g['n_words'].sum() * 100
            avg_col = {'presentation': 'pres_tone', 'qa_management': 'qa_mgmt_tone', 'qa_analyst': 'analyst_tone'}[p]
            part_rows.append({'part': label, 'This call': round(tone, 2), peer_name: round(peers[avg_col].mean(), 2)})
    parts_df = pd.DataFrame(part_rows)
    if not parts_df.empty:
        long = parts_df.melt('part', var_name='series', value_name='tone')
        bars = alt.Chart(long).mark_bar(cornerRadius=2).encode(
            y=alt.Y('part:N', title=None, sort=list(PART_NAMES.values()), axis=alt.Axis(labelLimit=220)),
            yOffset=alt.YOffset('series:N', sort=['This call', peer_name]),
            x=alt.X('tone:Q', title='Net positive words per 100'),
            color=alt.Color('series:N', scale=alt.Scale(domain=['This call', peer_name], range=[AZURE, '#B9C3D3']), legend=alt.Legend(orient='bottom', title=None)),
            tooltip=['part', 'series', alt.Tooltip('tone:Q', format='.2f')])
        st.altair_chart(bars.properties(height=240), width='stretch')

with right:
    st.subheader('How tone moves through the call')
    line_df = segs.assign(series='This call')
    if bench_segs is not None:
        seg_peers = bench_segs[bench_segs['sector'] == sector] if sector else bench_segs[bench_segs['call_id'].isin(bench['call_id'])]
        avg = seg_peers.groupby('segment')['lm_tone'].mean().reset_index().assign(series=peer_name)
        line_df = pd.concat([line_df, avg])
    lines = alt.Chart(line_df).mark_line(point=True, strokeWidth=2.5).encode(
        x=alt.X('segment:Q', title='Start of call → end of call (tenths)', scale=alt.Scale(domain=[1, 10])),
        y=alt.Y('lm_tone:Q', title='Tone'),
        color=alt.Color('series:N', scale=alt.Scale(range=[AZURE, '#B9C3D3'], domain=['This call', peer_name]), legend=alt.Legend(orient='bottom', title=None)),
        tooltip=['series', 'segment', alt.Tooltip('lm_tone:Q', format='.2f')])
    layers = [lines]
    if qa_start is not None:
        layers.append(alt.Chart(pd.DataFrame({'x': [qa_start + 0.5]})).mark_rule(strokeDash=[4, 4], color='#858E9F').encode(x='x:Q'))
    st.altair_chart(alt.layer(*layers).properties(height=240), width='stretch')
    if qa_start is not None:
        st.caption('Dashed line: start of the Q&A.')

st.subheader('Where this call sits among the benchmark calls')
strip = bench[['label', 'sector', 'composite', 'signal']].assign(kind='Benchmark call')
strip = pd.concat([strip, pd.DataFrame([{'label': 'This call', 'sector': detected or 'not recognised', 'composite': res['composite'], 'signal': res['signal'], 'kind': 'This call'}])])
q1, q2 = bench['composite'].quantile([1 / 3, 2 / 3])
dots = alt.Chart(strip).mark_point(filled=True, opacity=0.9).encode(
    x=alt.X('composite:Q', title='Overall score (0 = average benchmark call)'),
    y=alt.Y('kind:N', title=None, sort=['This call', 'Benchmark call']),
    color=alt.Color('kind:N', scale=alt.Scale(domain=['This call', 'Benchmark call'], range=[AZURE, '#9AA5B8']), legend=None),
    size=alt.Size('kind:N', scale=alt.Scale(domain=['This call', 'Benchmark call'], range=[400, 90]), legend=None),
    shape=alt.Shape('kind:N', scale=alt.Scale(domain=['This call', 'Benchmark call'], range=['diamond', 'circle']), legend=None),
    tooltip=['label', 'sector', 'signal', alt.Tooltip('composite:Q', format='+.2f')])
cuts = alt.Chart(pd.DataFrame({'x': [q1, q2]})).mark_rule(strokeDash=[4, 4], color='#C8CFDB').encode(x='x:Q')
st.altair_chart(alt.layer(cuts, dots).properties(height=150), width='stretch')
st.caption('Dashed lines split the benchmark into thirds: Negative (left), Neutral, Positive (right).')

with st.expander('Words driving the score'):
    pos = Counter(w for ws in scored['pos_words'] for w in ws).most_common(12)
    neg = Counter(w for ws in scored['neg_words'] for w in ws).most_common(12)
    c1, c2 = st.columns(2)
    c1.markdown('**Most frequent positive words**')
    c1.dataframe(pd.DataFrame(pos, columns=['word', 'count']), hide_index=True, width='stretch')
    c2.markdown('**Most frequent negative words**')
    c2.dataframe(pd.DataFrame(neg, columns=['word', 'count']), hide_index=True, width='stretch')

analysts = scored[(scored['part'] == 'qa_analyst') & (scored['n_words'] > 40)].copy()
if not analysts.empty:
    with st.expander('Toughest analyst questions'):
        analysts['tone'] = (analysts['lm_pos'] - analysts['lm_neg']) / analysts['n_words'] * 100
        for _, r in analysts.nsmallest(3, 'tone').iterrows():
            st.markdown(f"**{r['speaker']}** · tone {r['tone']:+.2f}")
            st.write(r['clean'][:600] + ('...' if len(r['clean']) > 600 else ''))

with st.expander('Speaker breakdown'):
    br = scored.groupby(['part', 'speaker'])['n_words'].sum().reset_index()
    br['part'] = br['part'].map(PART_NAMES)
    st.dataframe(br.rename(columns={'n_words': 'words'}), hide_index=True, width='stretch')

with st.expander('All scores'):
    out = pd.DataFrame([{'company': meta['company'], 'ticker': meta['ticker'], 'call_date': meta['call_date'], 'sector': detected or '', 'compared_with': sector or 'All benchmark calls',
                         **{k: (round(v, 4) if isinstance(v, (float, np.floating)) else v) for k, v in res.items()}}])
    st.dataframe(out.T.rename(columns={0: 'value'}).astype(str), width='stretch')
    st.download_button('Download scores (CSV)', out.to_csv(index=False), file_name=f"sentiment_{meta['ticker'] or 'transcript'}.csv", mime='text/csv')

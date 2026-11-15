import datetime as dt
import os
from collections import Counter

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import data_access as da
import market as mk
import sentiment_core as sc
import ui
from ui import esc, term

bench = da.benchmark()
calibrated, counts = da.calibrated_sectors(bench)
sector_map = da.sector_map()
lexicon = da.lexicon()
PART_NAMES = {'presentation': 'Prepared presentation', 'qa_management': 'Management answers (Q&A)', 'qa_analyst': 'Analyst questions (Q&A)'}


@st.cache_data(show_spinner='Reading and scoring the transcript...')
def analyse(name, data, sector_for_lexicon):
    raw = sc.read_text(name, data)
    meta = sc.get_meta(raw)
    fmt, turns = sc.parse(raw)
    scored = sc.score_turns(turns, da.lm(), sc.neutral_terms(lexicon, sector_for_lexicon))
    segs, qa_start = sc.segments(scored, da.lm())
    return meta, fmt, scored, segs, qa_start


def detect_meta(name, data):
    return sc.get_meta(sc.read_text(name, data))


ui.hero('Analyze a call', 'Score any earnings call in seconds',
        'Upload a transcript (Bloomberg or LSEG PDF) or paste the text of any earnings call. The app splits it into the scripted '
        'presentation and the live Q&amp;A, measures the tone of each part, compares it with its sector, and shows how the stock moved around the call.')

with st.sidebar:
    st.markdown('<div class="qm-side-brand">QUANTA-MENTALS<span>Call analyzer</span></div>', unsafe_allow_html=True)
    st.markdown('<p class="qm-side-h">1 · Transcript</p>', unsafe_allow_html=True)
    source = st.radio('Input', ['Upload a file', 'Paste text'], horizontal=True, label_visibility='collapsed')
    name, data = None, None
    if source == 'Upload a file':
        f = st.file_uploader('PDF or text file', type=['pdf', 'txt'], help='Bloomberg and LSEG PDFs are read automatically, including the ticker and date.')
        if f is not None:
            name, data = f.name, f.getvalue()
    else:
        text = st.text_area('Paste the transcript', height=220,
                            help='If the text contains a heading such as "Questions And Answers", the app splits the presentation from the Q&A.')
        if text.strip():
            name, data = 'pasted.txt', text.encode('utf-8')

    st.markdown('<p class="qm-side-h">2 · Company</p>', unsafe_allow_html=True)
    auto = detect_meta(name, data) if data else {'ticker': '', 'call_date': '', 'company': ''}
    ticker = st.text_input('Ticker', value=auto['ticker'], placeholder='e.g. JPM',
                           help='Read from the transcript when possible. Needed for the sector and the price reaction.').strip().upper()
    default_date = pd.to_datetime(auto['call_date']).date() if auto['call_date'] else None
    call_date = st.date_input('Call date', value=default_date, max_value=dt.date.today(), format='YYYY-MM-DD')

    st.markdown('<p class="qm-side-h">3 · Compare with</p>', unsafe_allow_html=True)
    detected, how = (sector_map.get(ticker), 'our sector map') if ticker in sector_map else (None, None)
    if ticker and not detected:
        detected, how = mk.yahoo_sector(ticker), 'Yahoo Finance'
    options = ['Auto-detect'] + calibrated + ['All benchmark calls']
    sector_choice = st.selectbox('Benchmark group', options, label_visibility='collapsed',
                                 help='Each sector has its own vocabulary (banks say credit, losses and reserves, which the finance dictionary counts as negative), '
                                      'so a call is best compared with its own sector.')
    if sector_choice == 'Auto-detect':
        st.caption(f'Detected: **{detected}** (from {how})' if detected else 'Enter a ticker to detect the sector.')
    st.markdown('<div class="qm-side-foot">Tone uses the Loughran-McDonald finance dictionary, cross-checked with VADER and TextBlob, '
                'on the same scale as the benchmark calls.</div>', unsafe_allow_html=True)

if data is None:
    ui.coverage_banner(bench, calibrated, counts)
    st.markdown("""<div class="qm-empty">""" + ui.icon("upload_file") + """
<h3>Start with a transcript</h3><p>Use the panel on the left to upload a Bloomberg or LSEG PDF, or paste the text of any earnings call.</p></div>""",
                unsafe_allow_html=True)
    st.markdown(f"""<div class="qm-steps">
<div class="qm-step"><span class="n">1 · READ</span><h5>Split the call</h5><p>{term("Prepared presentation", "Prepared presentation")}, analyst questions and management answers.</p></div>
<div class="qm-step"><span class="n">2 · SCORE</span><h5>Measure tone</h5><p>Upbeat, downbeat and uncertain finance words, cross-checked by two general tools.</p></div>
<div class="qm-step"><span class="n">3 · COMPARE</span><h5>Against its sector</h5><p>Placed against bank or tech {term("Benchmark", "benchmark")} calls and given a {term("Signal", "signal")}.</p></div>
<div class="qm-step"><span class="n">4 · REACT</span><h5>Check the stock</h5><p>Live {term("Abnormal return", "abnormal return")} over the day, week and month after the call.</p></div>
</div>""", unsafe_allow_html=True)
    ui.footer()
    st.stop()

if sector_choice == 'Auto-detect':
    sector = detected if detected in calibrated else None
elif sector_choice == 'All benchmark calls':
    sector = None
else:
    sector = sector_choice
lex_sector = sector or detected

meta, fmt, scored, segs, qa_start = analyse(name, data, lex_sector)
if scored.empty or scored['n_words'].sum() < 200:
    ui.warn('Not enough text could be read from this file. If it is a scanned PDF, it needs text recognition (OCR) first.')
    st.stop()

res = sc.score_call(scored, bench, sector)
peers = bench[bench['sector'] == sector] if sector else bench
peer_word = f'{sector.lower()} calls' if sector else 'all benchmark calls'
company = meta['company'] or (da.SHORT_NAMES.get(ticker) or ticker or os.path.splitext(name)[0])

st.markdown(f'<div class="qm-company"><h3>{esc(company)}</h3><div class="meta">'
            + ' · '.join(esc(x) for x in [ticker, detected and f'{detected} sector', call_date and call_date.isoformat(), f'{fmt} format', f'compared with {peer_word}'] if x)
            + '</div></div>', unsafe_allow_html=True)
if sector_choice == 'Auto-detect' and sector is None:
    if detected:
        ui.warn(f'<b>{esc(ticker)}</b> is in the <b>{esc(detected)}</b> sector (from {how}). The benchmark covers {" and ".join(calibrated)} only so far, '
                f'so this call is compared with all {len(bench)} benchmark calls. Read the relative scores with care.')
    elif ticker:
        ui.warn(f'The sector of <b>{esc(ticker)}</b> could not be looked up, so this call is compared with all {len(bench)} benchmark calls. '
                f'Pick <b>Bank</b> or <b>Tech</b> under "Compare with" in the left panel if one fits.')
    else:
        ui.warn(f'No ticker was found in this text, so the sector is unknown and the call is compared with all {len(bench)} benchmark calls. '
                f'Enter the ticker in the left panel to compare it with its own sector and to see the price reaction.')
if fmt.startswith('Plain'):
    ui.warn('Speakers could not be identified in this text, so analyst questions and management answers cannot be separated. The overall tone is still valid; the Q&A measures are limited.')

pct = (peers['composite'] < res['composite']).mean()
color = ui.SIGNAL_COLORS[res['signal']]
reading = {'Positive': 'Management sounds clearly more upbeat than most calls.',
           'Neutral': 'Management sounds about as upbeat as a typical call.',
           'Negative': 'Management sounds more cautious than most calls.'}[res['signal']]
st.markdown(f'<div class="qm-signal"><div class="pill" style="background:{color}">{esc(res["signal"])}</div>'
            f'<div class="txt"><b>{term("Signal", "Sentiment signal")}.</b> {reading} This call is more positive than '
            f'<b>{pct:.0%}</b> of {esc(peer_word)}.</div></div>', unsafe_allow_html=True)


def vs(value, avg, unit=''):
    if not np.isfinite(value) or not np.isfinite(avg):
        return ''
    diff = value - avg
    word = 'above' if diff >= 0 else 'below'
    return f'<b>{abs(diff):.2f}{unit} {word}</b> the {esc(sector.lower() if sector else "benchmark")} average ({avg:.2f})'


k = st.columns(5)
with k[0]:
    ui.kpi(term('Tone'), f"{res['lm_tone']:.2f}", vs(res['lm_tone'], peers['lm_tone'].mean()))
with k[1]:
    adj_avg = peers['lm_tone_sector'].mean() if 'lm_tone_sector' in peers else np.nan
    ui.kpi(term('Sector-adjusted tone'), f"{res['lm_tone_sector']:.2f}" if np.isfinite(res['lm_tone_sector']) else 'n/a',
           vs(res['lm_tone_sector'], adj_avg) or 'Ignores routine sector jargon.', color=ui.SKY)
with k[2]:
    ui.kpi(term('Overall score'), f"{res['composite']:+.2f}", '0 = average benchmark call; ±1 = one standard deviation.', color=color)
with k[3]:
    shift = res['tone_shift']
    ui.kpi(term('Tone change into Q&A'), f'{shift:+.2f}' if np.isfinite(shift) else 'n/a',
           ('Message <b>softened</b> under questioning.' if shift < 0 else 'Message <b>held or improved</b> in the Q&A.') if np.isfinite(shift) else 'Needs speaker labels.',
           color=ui.ROSE if np.isfinite(shift) and shift < 0 else ui.OLIVE)
with k[4]:
    conv = res['conviction_score']
    ui.kpi(term('Management conviction'), f'{conv:+.2f}' if np.isfinite(conv) else 'n/a',
           ('Held its message <b>better</b> than the average call.' if conv >= 0 else 'Held its message <b>less well</b> than the average call.') if np.isfinite(conv) else 'Needs speaker labels.',
           color=ui.OLIVE if np.isfinite(conv) and conv >= 0 else ui.ROSE)

ui.section('A · INSIDE THE CALL', 'Scripted remarks vs. live answers',
           f'Tone of each part of the call compared with the average of {esc(peer_word)}, and how tone moves from the first minute to the last.')
left, right = st.columns(2)
peer_name = f'{sector} average' if sector else 'Benchmark average'
with left:
    rows = []
    for p, label in PART_NAMES.items():
        g = scored[scored['part'] == p]
        if g['n_words'].sum() > 0:
            tone = (g['lm_pos'].sum() - g['lm_neg'].sum()) / g['n_words'].sum() * 100
            col = {'presentation': 'pres_tone', 'qa_management': 'qa_mgmt_tone', 'qa_analyst': 'analyst_tone'}[p]
            rows += [{'part': label, 'series': 'This call', 'tone': tone}, {'part': label, 'series': peer_name, 'tone': peers[col].mean()}]
    if rows:
        df = pd.DataFrame(rows)
        chart = alt.Chart(df).mark_bar(cornerRadiusEnd=3).encode(
            y=alt.Y('part:N', title=None, sort=list(PART_NAMES.values()), axis=alt.Axis(labelLimit=220),
                    scale=alt.Scale(paddingInner=0.35, paddingOuter=0.2)),
            yOffset=alt.YOffset('series:N', sort=['This call', peer_name]),
            x=alt.X('tone:Q', title='Tone (net positive words per 100)'),
            color=alt.Color('series:N', scale=alt.Scale(domain=['This call', peer_name], range=[ui.AZURE, '#B9C3D3'])),
            tooltip=['part', 'series', alt.Tooltip('tone:Q', format='.2f')])
        zero = alt.Chart(pd.DataFrame({'x': [0]})).mark_rule(color=ui.MUTED).encode(x='x:Q')
        labels = alt.Chart(df).mark_text(align='left', dx=4, fontSize=11, color=ui.INK).encode(
            y=alt.Y('part:N', sort=list(PART_NAMES.values())), yOffset=alt.YOffset('series:N', sort=['This call', peer_name]),
            x=alt.X('pos:Q'), text=alt.Text('tone:Q', format='.2f')).transform_calculate(pos='max(datum.tone, 0)')
        st.altair_chart((chart + zero + labels).properties(height=250, title='Tone by part of the call'), width='stretch')
with right:
    line_df = segs.assign(series='This call')
    seg_all = da.segments()
    if seg_all is not None:
        sp = seg_all[seg_all['sector'] == sector] if sector else seg_all[seg_all['call_id'].isin(bench['call_id'])]
        line_df = pd.concat([line_df, sp.groupby('segment')['lm_tone'].mean().reset_index().assign(series=peer_name)])
    lines = alt.Chart(line_df).mark_line(point=alt.OverlayMarkDef(size=45), strokeWidth=2.5).encode(
        x=alt.X('segment:Q', title='Start of call → end of call (tenths)', scale=alt.Scale(domain=[1, 10])),
        y=alt.Y('lm_tone:Q', title='Tone'),
        color=alt.Color('series:N', scale=alt.Scale(domain=['This call', peer_name], range=[ui.AZURE, '#B9C3D3'])),
        tooltip=['series', 'segment', alt.Tooltip('lm_tone:Q', format='.2f')])
    layers = [lines]
    if qa_start is not None:
        layers.append(alt.Chart(pd.DataFrame({'x': [qa_start + 0.5], 't': ['Q&A starts']})).mark_rule(strokeDash=[4, 4], color=ui.MUTED).encode(x='x:Q', tooltip='t'))
    st.altair_chart(alt.layer(*layers).properties(height=250, title='How tone moves through the call'), width='stretch')
    st.caption('The dashed line marks where the Q&A starts.')

ui.section('B · IN CONTEXT', 'Where this call sits among the benchmark',
           f'Every grey dot is a benchmark call; the blue diamond is this call. Dashed lines split the benchmark into Negative, Neutral and Positive thirds.')
strip = pd.concat([bench[['label', 'sector', 'composite', 'signal']].assign(kind='Benchmark calls'),
                   pd.DataFrame([{'label': 'This call', 'sector': detected or 'unknown', 'composite': res['composite'], 'signal': res['signal'], 'kind': 'This call'}])])
q1, q2 = bench['composite'].quantile([1 / 3, 2 / 3])
dots = alt.Chart(strip).mark_point(filled=True, opacity=0.9).encode(
    x=alt.X('composite:Q', title='Overall score (0 = average benchmark call)'),
    y=alt.Y('kind:N', title=None, sort=['This call', 'Benchmark calls']),
    color=alt.Color('kind:N', scale=alt.Scale(domain=['This call', 'Benchmark calls'], range=[ui.AZURE, '#9AA5B8']), legend=None),
    size=alt.Size('kind:N', scale=alt.Scale(domain=['This call', 'Benchmark calls'], range=[420, 90]), legend=None),
    shape=alt.Shape('kind:N', scale=alt.Scale(domain=['This call', 'Benchmark calls'], range=['diamond', 'circle']), legend=None),
    tooltip=['label', 'sector', 'signal', alt.Tooltip('composite:Q', format='+.2f')])
cuts = alt.Chart(pd.DataFrame({'x': [q1, q2]})).mark_rule(strokeDash=[4, 4], color='#C8CFDB').encode(x='x:Q')
st.altair_chart(alt.layer(cuts, dots).properties(height=140), width='stretch')

ui.section('C · MARKET REACTION', 'How the stock moved around this call',
           f'The line shows the stock\'s {term("Cumulative abnormal return (CAR)", "cumulative abnormal return")}: how much it beat or lagged the market, '
           'starting from the close the day before the call. Prices are fetched live from Yahoo Finance.')
if not ticker or not call_date:
    ui.note('Enter the <b>ticker</b> and <b>call date</b> above to see the price reaction.')
else:
    bench_etf = mk.SECTOR_ETF.get(detected)
    start = (pd.Timestamp(call_date) - pd.Timedelta(days=50)).strftime('%Y-%m-%d')
    end = min(pd.Timestamp(call_date) + pd.Timedelta(days=50), pd.Timestamp.today()).strftime('%Y-%m-%d')
    with st.spinner('Fetching prices...'):
        px, source = mk.prices(tuple([ticker, mk.MARKET] + ([bench_etf] if bench_etf else [])), start, end)
    ev = mk.event_window(px, ticker, call_date, mk.MARKET) if px is not None else None
    if ev is None:
        ui.warn(f'Price data for <b>{esc(ticker)}</b> could not be loaded. {esc(source or "")} The sentiment results above are unaffected.')
    else:
        ev_sec = mk.event_window(px, ticker, call_date, bench_etf) if bench_etf else None
        m1, m2, m3 = st.columns(3)
        for col, (label, (a, b)) in zip([m1, m2, m3], mk.WINDOWS.items()):
            v = mk.car(ev, a, b)
            with col:
                ui.kpi(f'{label} vs. S&amp;P 500', f'{v:+.1%}' if np.isfinite(v) else 'n/a',
                       ('Beat the market' if v >= 0 else 'Lagged the market') if np.isfinite(v) else 'Not enough trading days yet',
                       color=ui.OLIVE if np.isfinite(v) and v >= 0 else ui.ROSE)
        plot = ev.assign(benchmark='vs. S&P 500 (SPY)')
        if ev_sec is not None:
            plot = pd.concat([plot, ev_sec.assign(benchmark=f'vs. {detected} ETF ({bench_etf})')])
        line = alt.Chart(plot).mark_line(strokeWidth=2.5).encode(
            x=alt.X('day:Q', title='Trading days from the call (0 = call day)'),
            y=alt.Y('car:Q', title='Cumulative abnormal return', axis=alt.Axis(format='%')),
            color=alt.Color('benchmark:N', scale=alt.Scale(range=[ui.AZURE, ui.PUMPKIN])),
            tooltip=['benchmark', 'day', alt.Tooltip('date:T', format='%d %b %Y'), alt.Tooltip('car:Q', format='+.2%', title='CAR')])
        zero = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(color=ui.LINE).encode(y='y:Q')
        day0 = alt.Chart(pd.DataFrame({'x': [0]})).mark_rule(strokeDash=[4, 4], color=ui.MUTED).encode(x='x:Q')
        st.altair_chart(alt.layer(zero, day0, line).properties(height=280), width='stretch')
        agree = {('Positive', True): 'The tone and the price reaction point the same way.',
                 ('Negative', False): 'The tone and the price reaction point the same way.',
                 ('Positive', False): 'The market reacted against the upbeat tone: other news (the numbers, guidance) likely dominated.',
                 ('Negative', True): 'The market shrugged off the cautious tone: other news (the numbers, guidance) likely dominated.'}
        day = mk.car(ev, 0, 1)
        if res['signal'] != 'Neutral' and np.isfinite(day):
            ui.note(f'<b>Reading.</b> {agree[(res["signal"], day >= 0)]} One call is anecdote, not evidence; the Market reaction page tests the pattern across all benchmark calls.')
        st.caption(f'Source: {source}. Abnormal return = stock return minus benchmark return each day.')

ui.section('D · UNDER THE HOOD', 'What drove the score')
c1, c2, c3 = st.columns(3)
pos = Counter(w for ws in scored['pos_words'] for w in ws).most_common(10)
neg = Counter(w for ws in scored['neg_words'] for w in ws).most_common(10)
with c1:
    st.markdown('**Most frequent positive words**')
    st.dataframe(pd.DataFrame(pos, columns=['word', 'count']), hide_index=True, width='stretch')
with c2:
    st.markdown('**Most frequent negative words**')
    st.dataframe(pd.DataFrame(neg, columns=['word', 'count']), hide_index=True, width='stretch')
with c3:
    st.markdown('**Sector jargon set aside**')
    nt = sc.neutral_terms(lexicon, lex_sector)
    jargon = Counter()
    for t in scored['clean']:
        toks = t.lower().split()
        for i, w in enumerate(toks):
            w = w.strip('.,;:()"\'')
            if w in nt['words'] or (i > 0 and (toks[i - 1].strip('.,;:()"\''), w) in nt['pairs']):
                jargon[w if w in nt['words'] else toks[i - 1].strip('.,;:()"\'') + ' ' + w] += 1
    if jargon:
        st.dataframe(pd.DataFrame(jargon.most_common(10), columns=['term', 'count']), hide_index=True, width='stretch')
    else:
        st.caption('None found for this sector.')
    st.caption('These words are routine jargon in the sector and are ignored in the sector-adjusted tone.')

analysts = scored[(scored['part'] == 'qa_analyst') & (scored['n_words'] > 40)].copy()
if not analysts.empty:
    with st.expander('Toughest analyst questions'):
        analysts['tone'] = (analysts['lm_pos'] - analysts['lm_neg']) / analysts['n_words'] * 100
        for _, r in analysts.nsmallest(3, 'tone').iterrows():
            st.markdown(f"**{r['speaker']}** · tone {r['tone']:+.2f}")
            st.write(r['clean'][:600] + ('...' if len(r['clean']) > 600 else ''))

with st.expander('Download the scores'):
    out = pd.DataFrame([{'company': company, 'ticker': ticker, 'call_date': call_date, 'sector': detected or '',
                         'compared_with': sector or 'All benchmark calls',
                         **{k: (round(v, 4) if isinstance(v, (float, np.floating)) else v) for k, v in res.items()}}])
    st.dataframe(out.T.rename(columns={0: 'value'}).astype(str), width='stretch')
    st.download_button('Download as CSV', out.to_csv(index=False), file_name=f"sentiment_{ticker or 'transcript'}.csv", mime='text/csv')

ui.footer()

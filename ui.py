"""Quanta-Mentals design system: colours, CSS, reusable components, glossary and chart theme."""
import html

import altair as alt
import streamlit as st

SMITH_BLUE, AZURE, SKY, OCEAN, MINT = '#071D49', '#0047BB', '#0B76A6', '#00C1FF', '#5ECFBF'
ROSE, OLIVE, PUMPKIN, INK, MUTED, LINE, TINT = '#C8215D', '#578100', '#BD5A00', '#1F2A3D', '#556075', '#DDE3EC', '#F3F6FA'
SIGNAL_COLORS = {'Positive': OLIVE, 'Neutral': '#858E9F', 'Negative': ROSE}
SECTOR_PALETTE = [AZURE, PUMPKIN, '#6B4FBB', '#0E8A7E', '#A0522D', '#5A6B8C']

GLOSSARY = {
    'Earnings call': 'A quarterly conference call where a company presents its results, followed by questions from analysts who cover the stock.',
    'Transcript': 'The written record of an earnings call, split by speaker.',
    'Sentiment': 'Whether the language used is upbeat or downbeat. Here it is measured from the words management uses.',
    'Tone': 'Positive minus negative finance words for every 100 words spoken. Above 0 means more upbeat than downbeat language.',
    'Sector-adjusted tone': 'Tone after ignoring words that are routine jargon in the sector (e.g. "stress test" for banks, "mission-critical" for tech).',
    'Loughran-McDonald dictionary': 'A word list built by academics from thousands of company filings. Unlike everyday sentiment tools it knows that words like "liability" or "tax" are not bad news in finance.',
    'VADER': 'A rule-based sentiment tool built for everyday text such as social media. Used as a second opinion.',
    'TextBlob': 'A simple general-purpose sentiment tool based mostly on adjectives. Used as a third opinion.',
    'FinBERT': 'An AI language model trained on financial news that reads whole sentences in context. Available in the research notebook; left out of this demo to keep the app small and fast.',
    'Overall score': 'The average of the three methods after putting them on the same scale. 0 is the average benchmark call; +1 is one standard deviation more positive.',
    'Signal': 'Calls are ranked on the overall score and split into thirds: Positive (top third), Neutral, Negative (bottom third).',
    'Prepared presentation': 'The scripted opening part of the call, read by management.',
    'Q&A': 'The live part of the call where analysts ask questions and management answers unscripted.',
    'Tone change into Q&A': 'Management tone in its live answers minus its tone in the prepared presentation. Negative means the message softened under questioning.',
    'Analyst pushback': 'Negative finance words per 100 words in analysts\' questions: a measure of how critical the questions were.',
    'Hedging': 'Use of uncertain words such as "may", "approximately" or "depends". More hedging suggests less confidence.',
    'Management conviction': 'How well management held its message: answers more positive than the questions, little hedging, and tone holding up in the Q&A. 0 = average call.',
    'Benchmark': 'The set of past earnings calls each new call is compared against.',
    'Calibrated': 'The sectors with enough benchmark calls for a fair comparison. Nothing is trained; scores are compared against these calls.',
    'Abnormal return': 'A stock\'s return minus the market\'s return on the same day. It strips out market-wide moves so what is left is the company-specific reaction.',
    'Cumulative abnormal return (CAR)': 'Abnormal returns added up over a window, e.g. the day of the call and the day after.',
    'Event study': 'A standard finance method that measures how a stock moved around an event (here, the earnings call) compared with the market.',
    'Long-short strategy': 'Buy the stocks with a positive signal and short-sell those with a negative one. It makes money if positive calls beat negative ones, whatever the market does.',
    'Correlation': 'How closely two measures move together, from -1 to +1. Spearman correlation uses ranks, so a single extreme stock move cannot dominate.',
    'p-value': 'The chance of seeing a result this strong by luck if there were no real relationship. Below 0.05 is the usual bar for "statistically significant".',
    'Volatility': 'How much a stock\'s price swings, measured as the annualised standard deviation of daily returns.',
    'Maximum drawdown': 'The largest fall from a previous high over the period.',
    'Beta': 'How much the stock tends to move for a 1% move in the S&P 500. Above 1 means more volatile than the market.',
    'P/E ratio': 'Price per share divided by earnings per share: how many dollars investors pay for $1 of annual profit.',
    'Forward P/E': 'Price divided by the earnings analysts expect over the next 12 months.',
    'P/B ratio': 'Price divided by book value (assets minus liabilities) per share. The key valuation ratio for banks.',
    'EV/EBITDA': 'Enterprise value (market value plus net debt) divided by operating earnings before depreciation. Not meaningful for banks, whose debt is part of the business.',
    'Dividend yield': 'Annual dividends per share divided by the share price.',
    'ROE': 'Return on equity: annual profit as a percentage of shareholders\' equity. A core profitability measure for banks.',
    'Market cap': 'Share price times the number of shares: the stock market value of the company.',
}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lato:wght@400;700;900&display=swap');
html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], .stMarkdown, button, input, textarea, select {{
  font-family: 'Lato', 'Helvetica Neue', Arial, sans-serif !important; }}
[data-testid="stAppViewContainer"] {{ background: #F7F9FC; }}
[data-testid="stToolbar"], #MainMenu, footer {{ visibility: hidden; }}
.block-container {{ padding-top: 4.2rem; max-width: 1180px; }}
h1, h2, h3 {{ color: {SMITH_BLUE}; font-weight: 900 !important; letter-spacing: -0.01em; }}
.qm-hero {{ background: {SMITH_BLUE}; color: #fff; border-radius: 14px; padding: 34px 36px 30px; margin-bottom: 18px; position: relative; overflow: hidden; }}
.qm-hero::after {{ content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 6px;
  background: linear-gradient(90deg, {AZURE} 0 40%, {OCEAN} 40% 70%, {MINT} 70% 100%); }}
.qm-kicker {{ color: {OCEAN}; font-size: 12.5px; letter-spacing: .1em; text-transform: uppercase; font-weight: 700; margin: 0 0 8px; }}
.qm-hero h1 {{ color: #fff !important; font-size: clamp(28px, 3.6vw, 42px); line-height: 1.1; margin: 0 0 10px; padding: 0; }}
.qm-hero p.qm-sub {{ color: #DCE5F5; font-size: 17px; margin: 0; max-width: 52em; line-height: 1.5; }}
.qm-hero b {{ color: #fff; }}
.qm-banner {{ border: 1px solid #B9C9E8; border-left: 6px solid {AZURE}; background: #fff; padding: 12px 16px; margin: 4px 0 18px;
  color: {INK}; border-radius: 0 10px 10px 0; font-size: 14.5px; line-height: 1.5; }}
.qm-banner b {{ color: {SMITH_BLUE}; }}
.qm-section {{ margin: 34px 0 10px; }}
.qm-section .qm-num {{ color: {AZURE}; font-weight: 900; font-size: 13px; letter-spacing: .09em; }}
.qm-section h2 {{ margin: 2px 0 6px; font-size: 26px; padding: 0; }}
.qm-section p {{ color: {MUTED}; font-size: 15.5px; margin: 0; max-width: 56em; line-height: 1.55; }}
.qm-card {{ background: #fff; border: 1px solid {LINE}; border-radius: 12px; padding: 18px 20px; height: 100%; }}
.qm-card h4 {{ margin: 0 0 6px; color: {SMITH_BLUE}; font-size: 16.5px; font-weight: 900; }}
.qm-card p {{ margin: 0; color: {MUTED}; font-size: 14.5px; line-height: 1.5; }}
.qm-card .qm-tag {{ display: inline-block; font-size: 11.5px; font-weight: 700; letter-spacing: .06em; color: {AZURE}; text-transform: uppercase; margin-bottom: 6px; }}
.qm-kpi {{ background: #fff; border: 1px solid {LINE}; border-top: 4px solid {AZURE}; border-radius: 10px; padding: 14px 16px 12px; height: 100%; }}
.qm-kpi .lbl {{ color: {MUTED}; font-size: 13px; }}
.qm-kpi .val {{ color: {SMITH_BLUE}; font-size: 30px; font-weight: 900; line-height: 1.15; margin: 4px 0 2px; font-variant-numeric: tabular-nums; }}
.qm-kpi .note {{ color: {MUTED}; font-size: 12.5px; line-height: 1.4; }}
.qm-kpi .note b {{ color: {INK}; }}
.qm-signal {{ display: flex; align-items: center; gap: 22px; background: #fff; border: 1px solid {LINE}; border-radius: 12px; padding: 18px 22px; margin: 8px 0 16px; }}
.qm-signal .pill {{ font-size: 26px; font-weight: 900; color: #fff; border-radius: 10px; padding: 10px 20px; white-space: nowrap; }}
.qm-signal .txt {{ color: {INK}; font-size: 15.5px; line-height: 1.5; }}
.qm-term {{ border-bottom: 1.5px dotted {AZURE}; cursor: help; position: relative; white-space: nowrap; }}
.qm-term:hover::after, .qm-term:focus::after {{ content: attr(data-tip); position: absolute; left: 0; top: 135%; z-index: 50; width: 280px; white-space: normal;
  background: {SMITH_BLUE}; color: #fff; font-size: 13px; font-weight: 400; line-height: 1.45; padding: 10px 12px; border-radius: 8px;
  box-shadow: 0 8px 24px rgba(7,29,73,.25); text-transform: none; letter-spacing: 0; }}
.qm-note {{ background: {TINT}; border-radius: 10px; padding: 12px 16px; color: {INK}; font-size: 14px; line-height: 1.55; margin: 8px 0; }}
.qm-note b {{ color: {SMITH_BLUE}; }}
.qm-warn {{ background: #FFF6EC; border-left: 4px solid {PUMPKIN}; border-radius: 0 10px 10px 0; padding: 11px 15px; color: {INK}; font-size: 14px; margin: 8px 0; }}
.qm-steps {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; }}
.qm-step {{ background: #fff; border: 1px solid {LINE}; border-top: 4px solid {AZURE}; border-radius: 10px; padding: 14px 16px; }}
.qm-step .n {{ color: {AZURE}; font-weight: 900; font-size: 12px; letter-spacing: .08em; }}
.qm-step h5 {{ margin: 4px 0 4px; color: {SMITH_BLUE}; font-size: 15px; font-weight: 900; }}
.qm-step p {{ margin: 0; color: {MUTED}; font-size: 13.5px; line-height: 1.45; }}
.qm-chip {{ display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 12.5px; font-weight: 700; margin: 2px 4px 2px 0; }}
.qm-pos {{ background: #EAF3DC; color: #3F5F00; }} .qm-neg {{ background: #FBE4EC; color: #9E1A4A; }} .qm-neu {{ background: #ECEFF4; color: #4A5468; }}
.qm-company {{ background: #fff; border: 1px solid {LINE}; border-radius: 12px; padding: 16px 20px; margin: 12px 0 4px; }}
.qm-company h3 {{ margin: 0; font-size: 24px; padding: 0; }}
.qm-company .meta {{ color: {MUTED}; font-size: 13.5px; margin-top: 4px; }}
.qm-foot {{ color: {MUTED}; font-size: 12.5px; border-top: 1px solid {LINE}; margin-top: 40px; padding-top: 12px; }}
div[data-testid="stExpander"] details {{ background: #fff; border-radius: 10px; border: 1px solid {LINE}; }}
div[data-testid="stExpander"] summary p {{ font-weight: 700; color: {SMITH_BLUE}; }}
[data-testid="stMetricValue"] {{ color: {SMITH_BLUE}; }}
</style>
"""


def setup():
    st.markdown(CSS, unsafe_allow_html=True)


def esc(text):
    return html.escape(str(text))


def term(word, label=None):
    tip = GLOSSARY.get(word, '')
    return f'<span class="qm-term" tabindex="0" data-tip="{esc(tip)}">{esc(label or word)}</span>'


def hero(kicker, title, subtitle_html):
    st.markdown(f'<div class="qm-hero"><p class="qm-kicker">{esc(kicker)}</p><h1>{esc(title)}</h1>'
                f'<p class="qm-sub">{subtitle_html}</p></div>', unsafe_allow_html=True)


def section(num, title, intro_html=''):
    st.markdown(f'<div class="qm-section"><span class="qm-num">{esc(num)}</span><h2>{esc(title)}</h2>'
                f'<p>{intro_html}</p></div>', unsafe_allow_html=True)


def card(title, body_html, tag=None):
    tag_html = f'<span class="qm-tag">{esc(tag)}</span><br>' if tag else ''
    st.markdown(f'<div class="qm-card">{tag_html}<h4>{esc(title)}</h4><p>{body_html}</p></div>', unsafe_allow_html=True)


def kpi(label_html, value, note_html='', color=AZURE):
    st.markdown(f'<div class="qm-kpi" style="border-top-color:{color}"><div class="lbl">{label_html}</div>'
                f'<div class="val">{esc(value)}</div><div class="note">{note_html}</div></div>', unsafe_allow_html=True)


def note(body_html):
    st.markdown(f'<div class="qm-note">{body_html}</div>', unsafe_allow_html=True)


def warn(body_html):
    st.markdown(f'<div class="qm-warn">{body_html}</div>', unsafe_allow_html=True)


def coverage_banner(bench, calibrated, counts):
    covered = ' and '.join(calibrated) if len(calibrated) <= 2 else ', '.join(calibrated[:-1]) + ' and ' + calibrated[-1]
    detail = ', '.join(f'{counts[s]} {s.lower()}' for s in calibrated)
    st.markdown(
        f'<div class="qm-banner"><b>Works with earnings calls from any sector.</b> The {term("Benchmark", "benchmark")} is currently '
        f'{term("Calibrated", "calibrated")} on <b>{esc(covered)}</b> calls ({esc(detail)}), so comparisons for those sectors are the most '
        f'reliable. Calls from other sectors are scored the same way but compared with all {len(bench)} benchmark calls, and should be read '
        f'with care. <b>Next step:</b> extend the benchmark and the sector dictionaries to more sectors.</div>', unsafe_allow_html=True)


def footer():
    st.markdown('<div class="qm-foot">Quanta-Mentals · MMA 823 Analytics for Financial Markets · Smith School of Business, Queen\'s University. '
                'Research prototype, not investment advice. Transcripts are not stored or published; only derived scores are used.</div>',
                unsafe_allow_html=True)


def signal_chip(signal):
    cls = {'Positive': 'qm-pos', 'Negative': 'qm-neg'}.get(signal, 'qm-neu')
    return f'<span class="qm-chip {cls}">{esc(signal)}</span>'


@alt.theme.register('quanta', enable=True)
def quanta_theme():
    font = 'Lato, Helvetica Neue, Arial, sans-serif'
    return alt.theme.ThemeConfig({
        'config': {
            'background': 'white',
            'font': font,
            'view': {'stroke': None},
            'axis': {'labelColor': MUTED, 'titleColor': MUTED, 'gridColor': '#E9EDF3', 'domainColor': LINE, 'tickColor': LINE,
                     'labelFontSize': 12, 'titleFontSize': 12.5, 'titleFontWeight': 'normal'},
            'legend': {'labelColor': INK, 'titleColor': MUTED, 'labelFontSize': 12.5, 'orient': 'bottom', 'title': None},
            'title': {'color': SMITH_BLUE, 'fontSize': 15, 'anchor': 'start', 'fontWeight': 'bold'},
            'range': {'category': SECTOR_PALETTE},
        }
    })

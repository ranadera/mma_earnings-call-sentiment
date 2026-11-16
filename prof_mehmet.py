"""Optional, light-hearted bonus section: "Prof. Mehmet's take" on the Analyze page.

A student-written, imagined take inspired by themes from the MMA 823 lectures.
To switch it off, set SHOW_PROF_MEHMET = False in features.py.
To remove it completely, delete this file, features.py and the marked block at the end of views/analyze.py.
"""
import numpy as np
import streamlit as st

import ui
from ui import esc

CSS = """<style>
.pm-head { display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin:34px 0 4px; }
.pm-head .k { color:#5B6475; font-weight:900; font-size:11.5px; letter-spacing:.12em; }
.pm-sub { display:inline-block; background:#B90E31; color:#fff; font-weight:900; font-size:10.5px; letter-spacing:.12em;
  padding:3px 8px; border-radius:3px; }
.pm-card { background:#002452; border-radius:10px; padding:18px 20px; border-bottom:4px solid #FABD0F; color:#E8EDF6; }
.pm-top { display:flex; align-items:center; gap:14px; margin-bottom:12px; }
.pm-av { width:52px; height:52px; border-radius:50%; background:#FABD0F; color:#002452; font-weight:900; font-size:18px;
  display:flex; align-items:center; justify-content:center; flex:none; }
.pm-top h4 { margin:0; color:#fff; font-size:19px; font-weight:900; padding:0; }
.pm-top .s { color:#AFC0DA; font-size:12.5px; }
.pm-verdict { background:rgba(255,255,255,.07); border-left:4px solid #FABD0F; border-radius:0 6px 6px 0; padding:10px 14px;
  font-size:16px; line-height:1.5; color:#fff; margin-bottom:12px; }
.pm-card ul { margin:0 0 10px 18px; padding:0; }
.pm-card li { font-size:14.3px; line-height:1.55; margin-bottom:6px; color:#E8EDF6; }
.pm-card b { color:#FABD0F; }
.pm-meter { margin:8px 0 12px; }
.pm-meter .lbl { font-size:11.5px; font-weight:900; letter-spacing:.1em; color:#AFC0DA; margin-bottom:4px; }
.pm-bar { position:relative; height:12px; border-radius:6px; background:linear-gradient(90deg,#3B7CC4 0%,#FABD0F 60%,#B90E31 100%); }
.pm-pin { position:absolute; top:-5px; width:4px; height:22px; background:#fff; border-radius:2px; box-shadow:0 0 0 2px #002452; }
.pm-scale { display:flex; justify-content:space-between; font-size:11.5px; color:#AFC0DA; margin-top:4px; }
.pm-hw { background:rgba(250,189,15,.12); border-radius:6px; padding:9px 12px; font-size:13.8px; color:#fff; }
.pm-disc { color:#5B6475; font-size:12px; margin-top:8px; line-height:1.45; }
</style>"""

SECTOR_CONTEXT = {
    'Bank': 'For a bank, check the <b>yield curve and credit spreads</b> that week before blaming the CEO\'s adjectives. Rates move bank stocks more than vocabulary does.',
    'Tech': 'For tech, the story this year is the <b>AI build-out</b>: is the market starting to charge a higher risk premium for all that capital spending? That can swamp anything said on one call.',
}


def _benchmark_evidence():
    """Correlation of the overall score with the day 0 to +1 reaction across the benchmark, if the saved event study exists."""
    try:
        import pandas as pd
        from scipy.stats import spearmanr
        import data_access as da
        r = pd.read_csv('data/event_returns.csv')
        d = da.benchmark().merge(r[r['benchmark'] == 'SPY'], on='call_id').dropna(subset=['composite', 'car_day'])
        if len(d) < 8:
            return None
        rho, p = spearmanr(d['composite'], d['car_day'])
        return len(d), rho, p
    except Exception:
        return None


def render(res, peer_word, sector, reaction):
    """res: scored call; reaction: dict from the market section (or None if no prices)."""
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<div class="pm-head"><span class="k">F · BONUS</span><span class="pm-sub">SUBSCRIBERS ONLY</span></div>',
                unsafe_allow_html=True)
    with st.expander("Prof. Mehmet's take on how the market moved", expanded=False, icon=':material/school:'):
        signal = res.get('signal', 'Neutral')
        bullets = []

        if not reaction or not np.isfinite(reaction.get('day', np.nan)):
            verdict = ('No prices, no story. And even with prices, remember we only ever observe <b>one history</b>: '
                       'we cannot rewind the tape and replay this call with different words.')
            size = np.nan
        else:
            day, size, up = reaction['day'], reaction['size'], reaction['day'] >= 0
            match = (signal == 'Positive' and up) or (signal == 'Negative' and not up)
            clash = (signal == 'Positive' and not up) or (signal == 'Negative' and up)
            if not np.isfinite(size) or size < 1:
                verdict = (f'The market more or less shrugged ({day:+.1%} vs. the S&amp;P 500). "Nothing unusual happened" is a perfectly '
                           'respectable research finding. Write it down; do not torture the data until it confesses.')
            elif match:
                verdict = (f'Tone and price agreed ({day:+.1%} vs. the market). Before celebrating, ask the uncomfortable question: '
                           '<b>how many calls and how many measures did we try before finding one that lines up?</b>')
            elif clash:
                verdict = (f'The words said one thing, the price ({day:+.1%}) said another. The market did not read our dictionary; '
                           'it read the numbers, the guidance and the headlines of that week.')
            else:
                verdict = (f'A sizeable move ({day:+.1%}) after a call with a neutral tone. The language did not tell this story, '
                           'so the explanation is in the context: results, guidance, rates, sector news.')
            pre, week = reaction.get('pre', np.nan), reaction.get('week', np.nan)
            if np.isfinite(pre) and abs(pre) > 0.03:
                bullets.append(f'The stock had already moved <b>{pre:+.1%}</b> against the market in the month before the call. '
                               'Was the market reading the transcript, or had it already priced in the news?')
            if np.isfinite(week) and np.sign(week) != np.sign(day):
                bullets.append('The first-day move <b>reversed within a week</b>. Prices are people: on the day there were more sellers '
                               '(or buyers) than the other side, and a week later the crowd changed its mind.')

        bullets.append('Where does this result sit between a <b>roulette wheel</b> (pure chance, no memory) and <b>Halley\'s Comet</b> '
                       '(predictable to the day)? One call is a single spin; finance usually lives somewhere in between.')
        if np.isfinite(res.get('tone_shift', np.nan)) and res['tone_shift'] < 0:
            bullets.append('Management sounded better in the script than live. Naturally: the script was rehearsed. '
                           'The Q&amp;A is where you hear <b>the sound in the room</b>.')
        if sector in SECTOR_CONTEXT:
            bullets.append(SECTOR_CONTEXT[sector])
        ev = _benchmark_evidence()
        if ev:
            n, rho, p = ev
            bullets.append(f'Across our {n} benchmark calls the overall score and the next-day reaction have a correlation of '
                           f'<b>{rho:+.2f}</b> (p-value {p:.2f}). With a sample this small, the honest answer is "we do not know yet", '
                           'and that is a respectable answer.')
        bullets.append('If you test enough sentiment measures, one of them will always "explain" the move. That is '
                       '<b>seeing faces in the clouds</b>: count your trials and discount the result accordingly.')

        pin = 5 if not np.isfinite(size) else float(np.clip(size / 3 * 100, 2, 98))
        noise_txt = ('no prices to judge' if not np.isfinite(size) else 'mostly noise' if size < 1 else
                     'some signal, plenty of noise' if size < 2 else 'signal... or a very loud coincidence')
        st.markdown(f"""<div class="pm-card">
<div class="pm-top"><div class="pm-av">PM</div><div><h4>Prof. Mehmet's office hours</h4>
<div class="s">An imagined take on {esc(peer_word.removeprefix('all '))}, written by Group 9 in the spirit of the MMA 823 lectures</div></div></div>
<div class="pm-verdict">{verdict}</div>
<div class="pm-meter"><div class="lbl">NOISE-O-METER (REACTION VS. A NORMAL DAY): {esc(noise_txt.upper())}</div>
<div class="pm-bar"><div class="pm-pin" style="left:{pin:.0f}%"></div></div>
<div class="pm-scale"><span>0× · normal noise</span><span>1×</span><span>2× · unusual</span><span>3×+ · front-page news</span></div></div>
<p style="margin:6px 0 6px;font-weight:900;color:#fff;font-size:14px">Questions he would probably ask in class</p>
<ul>{''.join(f'<li>{b}</li>' for b in bullets)}</ul>
<div class="pm-hw"><b>Homework:</b> read the financial headlines from the week of this call, then decide whether the transcript or the macro
moved the stock. Running the model is not the skill; spotting the fluke is.</div></div>
<div class="pm-disc">Light-hearted bonus written by the students of Group 9, inspired by themes from the MMA 823 lectures. It is not written,
reviewed or endorsed by the professor and does not quote him. Not financial advice.</div>""", unsafe_allow_html=True)

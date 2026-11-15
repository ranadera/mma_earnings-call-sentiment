"""Quanta-Mentals Earnings Call Sentiment platform (MMA 823).

Run with:  streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title='Quanta-Mentals · Earnings Call Sentiment', page_icon=':material/insights:', layout='wide')

import ui

ui.setup()

pages = [
    st.Page('views/home.py', title='Home', icon=':material/home:', default=True),
    st.Page('views/analyze.py', title='Analyze a call', icon=':material/upload_file:'),
    st.Page('views/explorer.py', title='Benchmark explorer', icon=':material/leaderboard:'),
    st.Page('views/market_reaction.py', title='Market reaction', icon=':material/candlestick_chart:'),
    st.Page('views/stocks.py', title='Stock reports', icon=':material/description:'),
    st.Page('views/method.py', title='Method & decisions', icon=':material/menu_book:'),
]
st.navigation(pages, position='top').run()

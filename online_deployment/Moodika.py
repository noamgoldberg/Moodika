
import streamlit as st
st.set_page_config(page_title="Moodika",
                   page_icon=":notes:")
# st.write("""
# # Simple Stock Price App
# Shown are the stock closing price and volume of Google!
# """)
#
# # https://towardsdatascience.com/how-to-get-stock-data-using-python-c0de1df17e75
# #define the ticker symbol
# tickerSymbol = 'GOOGL'
# #get data on this ticker
# tickerData = yf.Ticker(tickerSymbol)
# #get the historical prices for this ticker
# tickerDf = tickerData.history(period='1d', start='2010-5-31', end='2020-5-31')
# # Open	High	Low	Close	Volume	Dividends	Stock Splits
#
# st.line_chart(tickerDf.Close)
# st.line_chart(tickerDf.Volume)

import predict_page
from predict_page import show_predict_page
from explore_page import show_explore_page





page = st.sidebar.selectbox("Welcome to Moodika", ("Moodika", "More about Us"))

if page == "Moodika":
    show_predict_page()
else:
    show_explore_page()
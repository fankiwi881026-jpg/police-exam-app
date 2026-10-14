import re
import streamlit as st
import yfinance as yf

@st.cache_data(ttl=86400,show_spinner=False)
def resolve(code, market):
    code=code.strip().upper()
    if not re.fullmatch(r"[A-Z0-9.\-^=]{1,24}",code):raise ValueError("請輸入有效股票代號")
    if code.endswith(('.TW','.TWO')):return code
    if market=='美股':return code
    if market=='台股':
        if not re.fullmatch(r'\d{4,6}',code):raise ValueError('台股請輸入數字代號')
        for suffix in ('.TW','.TWO'):
            try:
                df=yf.Ticker(code+suffix).history(period='5d',interval='1d')
                if not df.empty:return code+suffix
            except Exception:pass
        raise ValueError('找不到此上市／上櫃代號；可能是新上市、下市或行情暫時無法取得')
    if re.fullmatch(r'\d{4,6}',code):return resolve(code,'台股')
    return code

@st.cache_data(ttl=3600,show_spinner=False)
def long_history(symbol):
    df=yf.Ticker(symbol).history(period='max',interval='1d',auto_adjust=False)
    if df.empty:raise ValueError('查無可用歷史資料')
    df=df[['Open','High','Low','Close','Volume']].dropna().copy()
    df.index=df.index.tz_localize(None)
    return df.sort_index()

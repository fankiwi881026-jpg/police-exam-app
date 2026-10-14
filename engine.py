import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st

@st.cache_data(ttl=300, show_spinner=False)
def history(symbol: str, period='2y'):
    symbol = symbol.strip().upper()
    if not symbol or len(symbol) > 24 or not all(c.isalnum() or c in '.-^=' for c in symbol):
        raise ValueError('股票代號格式錯誤')
    df = yf.Ticker(symbol).history(period=period, interval='1d', auto_adjust=True)
    if df.empty:
        raise ValueError('無行情資料，台股請試 2330.TW 或 6488.TWO')
    df = df[['Open','High','Low','Close','Volume']].dropna().copy()
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    return df[~df.index.duplicated(keep='last')].sort_index()

def indicators(df):
    d = df.copy()
    for n in (20,60,120): d[f'MA{n}'] = d.Close.rolling(n, min_periods=n).mean()
    for n in (5,20): d[f'VMA{n}'] = d.Volume.rolling(n, min_periods=n).mean()
    sd = d.Close.rolling(20, min_periods=20).std(ddof=0)
    d['BB_UP'] = d.MA20 + 2*sd
    d['BB_LOW'] = d.MA20 - 2*sd
    d['VOL_RATIO'] = d.Volume / d.VMA20.replace(0,np.nan)
    return d

def levels(d, window=120, pivot=3, tolerance=.012):
    """Confirmed swing pivots; recent levels grouped into price zones."""
    x=d.tail(window+2*pivot).copy()
    if len(x)<2*pivot+1: return [],[]
    lows=[]; highs=[]
    for i in range(pivot,len(x)-pivot):
        segment=x.iloc[i-pivot:i+pivot+1]
        if x.Low.iloc[i] == segment.Low.min(): lows.append(float(x.Low.iloc[i]))
        if x.High.iloc[i] == segment.High.max(): highs.append(float(x.High.iloc[i]))
    price=float(d.Close.iloc[-1])
    def cluster(vals):
        groups=[]
        for v in sorted(vals):
            found=next((g for g in groups if abs(v-np.mean(g))/max(np.mean(g),1e-9)<=tolerance),None)
            if found is None: groups.append([v])
            else: found.append(v)
        return [(float(np.mean(g)),len(g)) for g in groups]
    supports=sorted([x for x in cluster(lows) if x[0]<price],key=lambda z:z[0],reverse=True)[:3]
    resistances=sorted([x for x in cluster(highs) if x[0]>price],key=lambda z:z[0])[:3]
    return supports,resistances

def score(d):
    if len(d)<120: return None,[]
    r=d.iloc[-1]; p=d.iloc[-2]
    pts=0; notes=[]
    for n,weight in ((20,15),(60,15),(120,15)):
        if r.Close>r[f'MA{n}']: pts+=weight;notes.append(f'站上 MA{n} +{weight}')
    if r.MA20>r.MA60>r.MA120: pts+=20;notes.append('均線多頭排列 +20')
    if r.Close>p.Close and r.VOL_RATIO>=1.5: pts+=15;notes.append('上漲放量 +15')
    if r.Close>=r.MA20 and r.Close<=r.BB_UP: pts+=10;notes.append('布林中上軌 +10')
    if r.Close>r.MA20 and r.MA20>p.MA20: pts+=10;notes.append('MA20 上彎 +10')
    return min(100,pts),notes

def backtest(d, fee_bps=15, initial=100000):
    """Long only: prior-close signal, execute next day's open; open-to-open returns."""
    x=d.dropna(subset=['MA20','MA60','MA120']).copy()
    if len(x)<4: return None
    signal=((x.Close>x.MA20)&(x.MA20>x.MA60)&(x.MA60>x.MA120)).astype(int)
    # Signal at close t, order executed at open t+1. Holding open(t+1)->open(t+2).
    pos=signal.shift(1).fillna(0)
    ret=x.Open.shift(-1)/x.Open-1
    turnover=pos.diff().abs().fillna(pos.abs())
    strat=(pos*ret-turnover*fee_bps/10000).iloc[:-1].fillna(0)
    bench=ret.iloc[:-1].fillna(0)
    equity=initial*(1+strat).cumprod()
    benchmark=initial*(1+bench).cumprod()
    years=max(len(strat)/252,1/252)
    dd=equity/equity.cummax()-1
    return {'equity':equity,'benchmark':benchmark,'return':float(equity.iloc[-1]/initial-1),
            'cagr':float((equity.iloc[-1]/initial)**(1/years)-1),
            'drawdown':float(dd.min()),'trades':int((turnover.iloc[:-1]>0).sum()),
            'note':'收盤訊號於次日開盤執行；採用開盤至次日開盤報酬；單邊成本以 bps 扣除，未計滑價、稅務及股息再投入。'}


import html
import re
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import yfinance as yf
from symbols import resolve,long_history
from storage import categories,create_category,add_watch_category,watches_by_category,remove_watch
from indicators import OVERLAYS,SUBS,ALL,calc

st.set_page_config(page_title="StockVision｜專業看盤",page_icon="📈",layout="wide",initial_sidebar_state="expanded")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;600;700;800&display=swap');
html,body,.stApp{font-family:'Noto Sans TC',sans-serif}
.stApp{background:#081827;color:#e7f2fb}
[data-testid="stHeader"]{background:#0c2438!important;min-height:2.3rem}
[data-testid="stToolbar"]{transform:scale(.72);transform-origin:top right}
[data-testid="stSidebar"]{background:#0c2234;border-right:1px solid #274458;min-width:240px;max-width:290px}
[data-testid="stSidebar"] .block-container{padding-top:.7rem}
.block-container{max-width:1900px;padding:2.1rem .9rem 1rem}
h1,h2,h3{color:#f2f8fd!important;letter-spacing:0}
.stButton button{background:#15334c;color:#e5f2ff;border:1px solid #315672;border-radius:7px;font-size:13px}
.stButton button:hover{border-color:#40aaf6;color:#fff}
[data-testid="stMetric"]{background:#112c41;border:1px solid #25465c;padding:10px;border-radius:9px}
[data-testid="stMetricLabel"] p{color:#a9c5d8!important;font-size:12px!important}
[data-testid="stMetricValue"]{color:#f4f9fd!important;font-size:clamp(17px,2vw,27px)!important}
[data-testid="stCaptionContainer"] p{color:#a3bfd3!important}
[data-testid="stTabs"]{overflow-x:auto}
[data-testid="stTabs"] button{font-size:12px;color:#b9d0df;font-weight:700;padding:7px 11px}
[data-testid="stTabs"] button[aria-selected="true"]{color:#63dcf5}
[data-testid="stPlotlyChart"]{border:1px solid #29475c;border-radius:6px;overflow:hidden}
[data-testid="stMain"] [data-testid="stImage"] img{width:100%;height:74px;object-fit:cover;object-position:center 45%;border-radius:4px}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.45rem}
[data-testid="stSidebar"] p{font-size:13px}
.stSelectbox label,.stTextInput label{font-size:12px!important}
.stock-header{display:flex;flex-wrap:wrap;gap:15px;align-items:center;padding:12px 15px;background:linear-gradient(110deg,#102a41,#15334b);border:1px solid #2b4a60;border-radius:7px;margin:6px 0 9px}
.stock-name{font-size:clamp(18px,2.1vw,26px);font-weight:800;color:#f3f9ff}
.stock-name small{font-size:12px;color:#aac4d6;margin-left:8px}
.stock-label{color:#7da8c5;font-size:11px}
.quote-price{font-size:clamp(27px,3vw,44px);font-weight:800;color:#ff527e;line-height:1.1}
.quote-price.down{color:#32edc6}
.quote-time{color:#9bbacf;font-size:11px}
.market-strip{display:flex;flex-wrap:wrap;gap:8px 22px;padding:7px 12px;border:1px solid #244459;background:#10283c;border-radius:6px;margin-bottom:8px;font-size:12px;color:#a7c4d7}
.market-strip b{color:#eaf7ff;margin-left:4px}
.section-title{font-size:14px;font-weight:800;color:#d6eafa;border-left:3px solid #21aaff;padding-left:9px;margin:12px 0 6px}
[data-testid="stHorizontalBlock"]{gap:.6rem}
@media(max-width:850px){
.block-container{padding:1.5rem .4rem .8rem}
[data-testid="stMain"] [data-testid="stImage"] img{height:54px}
.stock-header{gap:9px;padding:9px}
.quote-price{font-size:26px}
[data-testid="stToolbar"]{transform:scale(.65)}
}
</style>""",unsafe_allow_html=True)

@st.cache_data(ttl=90,show_spinner=False)
def minute_data(s,interval='1m'):
    period='1d' if interval=='1m' else '5d'
    d=yf.Ticker(s).history(period=period,interval=interval,auto_adjust=False)
    return d[['Open','High','Low','Close','Volume']].dropna() if not d.empty else d
@st.cache_data(ttl=1800,show_spinner=False)
def metadata(s):
    try:return yf.Ticker(s).info or {}
    except Exception:return {}
@st.cache_data(ttl=1800,show_spinner=False)
def dividend_data(s):
    try:return yf.Ticker(s).dividends
    except Exception:return pd.Series(dtype=float)
@st.cache_data(ttl=1800,show_spinner=False)
def split_data(s):
    try:return yf.Ticker(s).splits
    except Exception:return pd.Series(dtype=float)
@st.cache_data(ttl=900,show_spinner=False)
def news_data(s):
    try:return yf.Ticker(s).news or []
    except Exception:return []
@st.cache_data(ttl=3600,show_spinner=False)
def statement(s,kind):
    try:
        t=yf.Ticker(s)
        return t.income_stmt if kind=='損益表' else (t.balance_sheet if kind=='資產負債表' else t.cashflow)
    except Exception:return pd.DataFrame()
@st.cache_data(ttl=300,show_spinner=False)
def quote(s):
    try:
        d=minute_data(s)
        if not d.empty:return float(d.Close.iloc[-1]),str(d.index[-1]),'Yahoo 分鐘行情（可能延遲）'
    except Exception:pass
    try:
        d=long_history(s)
        if not d.empty:return float(d.Close.iloc[-1]),str(d.index[-1]),'歷史日收盤（非即時）'
    except Exception:pass
    return None,None,'目前無報價'


def draw(d,overlays,subindicators):
    """Interactive constrained-range professional K chart; indicator panes directly below price."""
    # Compute indicators on all original bars; no downsampling that would distort periods.
    rising='#ff477c';falling='#20e7be'
    nrows=2+len(subindicators)
    weights=[.60,.15]+[.25/max(1,len(subindicators))]*len(subindicators)
    fig=make_subplots(rows=nrows,cols=1,shared_xaxes=True,vertical_spacing=.015,
                      row_heights=weights)
    fig.add_trace(go.Candlestick(x=d.index,open=d.Open,high=d.High,low=d.Low,close=d.Close,
        name='K 線',increasing_line_color=rising,increasing_fillcolor=rising,
        decreasing_line_color=falling,decreasing_fillcolor=falling,whiskerwidth=.4),row=1,col=1)
    palette=['#ffbb44','#69ccff','#bd7cff','#2de7c1','#ff6eab','#f7d579']
    for ind in overlays:
        for j,(name,series) in enumerate(calc(d,ind).items()):
            fig.add_trace(go.Scatter(x=d.index,y=series,name=f'{ind} {name}',
                line=dict(color=palette[j%len(palette)],width=1.35),connectgaps=False),row=1,col=1)
    fig.add_trace(go.Bar(x=d.index,y=d.Volume,name='成交量',
        marker_color=[rising if c>=o else falling for o,c in zip(d.Open,d.Close)],opacity=.85),row=2,col=1)
    for i,ind in enumerate(subindicators):
        row=3+i
        data=calc(d,ind)
        for j,(name,series) in enumerate(data.items()):
            if name in ('柱狀體','成交量'):
                fig.add_trace(go.Bar(x=d.index,y=series,name=f'{ind} {name}',
                    marker_color=[rising if x>=0 else falling for x in series.fillna(0)],opacity=.75),row=row,col=1)
            else:
                fig.add_trace(go.Scatter(x=d.index,y=series,name=f'{ind} {name}',
                    line=dict(color=palette[j%len(palette)],width=1.6)),row=row,col=1)
        fig.update_yaxes(title_text=ind.split(' ')[0],row=row,col=1,title_font_size=10)
    # minallowed/maxallowed prevent panning/zooming beyond available timestamps
    xmin=d.index.min();xmax=d.index.max()
    if len(d)>1:
        initial_left=d.index[max(0,len(d)-100)]
    else:initial_left=xmin
    fig.update_layout(height=min(1050,530+135*len(subindicators)),template='plotly_dark',
        paper_bgcolor='#081c2c',plot_bgcolor='#081c2c',
        margin=dict(l=4,r=6,t=20,b=7),font=dict(family='Noto Sans TC, sans-serif',size=10,color='#c5dced'),
        xaxis_rangeslider_visible=False,hovermode='x unified',dragmode='pan',
        legend=dict(orientation='h',y=1.035,x=0,font=dict(size=9)),uirevision='stockvision-11',
        bargap=.12)
    fig.update_xaxes(gridcolor='#20394a',showspikes=True,spikemode='across',
        spikethickness=1,spikecolor='#9bc0d5',
        range=[initial_left,xmax],minallowed=xmin,maxallowed=xmax)
    fig.update_yaxes(gridcolor='#20394a',showspikes=True,spikemode='across',spikethickness=1,spikecolor='#9bc0d5')
    return fig

def select_stock(s):
    st.session_state['symbol_input']=s.replace('.TW','').replace('.TWO','')
    st.session_state['market_choice']='自動判斷'

with st.sidebar:
    st.markdown('## 📊 StockVision')
    st.caption('專業看盤 · 台美股')
    st.text_input('搜尋代號／股票',key='symbol_input',value='2330',placeholder='2330、AAPL、NVDA')
    st.selectbox('市場',options=['自動判斷','台股','美股'],key='market_choice')
    if st.button('↻ 重新整理行情',use_container_width=True):
        quote.clear();minute_data.clear();st.rerun()
    st.divider()
    st.markdown('### ☆ 自選股分類')
    groups=categories()
    group=st.selectbox('分類書籤',groups)
    stocks=watches_by_category(group)
    for item in stocks:
        if st.button('▸ '+item.replace('.TW','').replace('.TWO',''),key='pick_'+item,use_container_width=True):
            select_stock(item);st.rerun()
    if not stocks:st.caption('目前沒有股票')
    with st.expander('＋ 管理自選股與分類'):
        new=st.text_input('新增分類名稱')
        if st.button('建立分類') and new.strip():create_category(new.strip());st.rerun()
        if st.button('加入目前股票',use_container_width=True):
            try:
                add_watch_category(resolve(st.session_state['symbol_input'].strip().upper(),st.session_state['market_choice']),group)
                st.rerun()
            except Exception as e:st.error(str(e))
        if stocks:
            rem=st.selectbox('選擇移除',stocks)
            if st.button('移除股票'):remove_watch(rem);st.rerun()
    st.divider()
    st.caption('資料模式：Yahoo Finance（可能延遲）')
    st.caption('元大 SPARK API 尚未開通、尚未串接。')
    st.caption('自選股存在本機 SQLite；雲端重啟可能遺失。')

raw=st.session_state['symbol_input'].strip().upper()
try:symbol=resolve(raw,st.session_state['market_choice'])
except ValueError as e:st.error(str(e));st.stop()
st.image('header.png',use_container_width=True)
info=metadata(symbol)
name=info.get('shortName') or info.get('longName') or symbol
try:hist=long_history(symbol)
except Exception:hist=pd.DataFrame()
if hist is None:hist=pd.DataFrame()
last=hist.iloc[-1] if not hist.empty else None
prev=hist.iloc[-2] if len(hist)>1 else None
st.markdown('<div class="stock-header"><div><div class="stock-label">個股行情 · '+html.escape(symbol)+'</div><div class="stock-name">'+html.escape(raw)+'　'+html.escape(str(name))+'<small>'+html.escape(info.get('exchange',''))+'</small></div></div></div>',unsafe_allow_html=True)
@st.fragment(run_every='5s')
def price_strip():
    price,t,source=quote(symbol)
    if price is None:st.warning('目前無法取得報價。');return
    delta=price-float(prev.Close) if prev is not None else None
    pct=delta/float(prev.Close)*100 if delta is not None and prev.Close else None
    color='down' if delta is not None and delta<0 else ''
    arrow='▼' if delta is not None and delta<0 else '▲'
    c1,c2,c3=st.columns([1.6,1.2,1.8])
    with c1:
        st.markdown(f'<div class="quote-price {color}">{price:,.2f} <span style="font-size:15px">{arrow if delta is not None else ""}</span></div>',unsafe_allow_html=True)
        if delta is not None:st.markdown(f'**{delta:+,.2f}（{pct:+.2f}%）**')
    with c2:
        st.markdown('<div class="stock-label">最新可取得資料時間</div>',unsafe_allow_html=True)
        st.write(str(t)[:25])
    with c3:
        st.markdown('<div class="stock-label">資料來源</div>',unsafe_allow_html=True)
        st.write(source)
    st.caption('每 5 秒檢查畫面，行情來源快取及供應商延遲可能造成價格不變。非元大即時行情。')
price_strip()
if last is not None:
    v=last
    strip=[('開盤',f'{v.Open:,.2f}'),('最高',f'{v.High:,.2f}'),('最低',f'{v.Low:,.2f}'),
           ('日收盤',f'{v.Close:,.2f}'),('日成交量',f'{int(v.Volume):,}')]
    st.markdown('<div class="market-strip">'+''.join(f'<span>{k}<b>{val}</b></span>' for k,val in strip)+'</div>',unsafe_allow_html=True)

st.markdown('<div class="section-title">技術分析｜K 線與副圖</div>',unsafe_allow_html=True)
a,b,c=st.columns([2.7,1.4,1.1])
with a:kind=st.segmented_control('週期',['日 K','週 K','月 K'],default='日 K',label_visibility='collapsed')
with b:period=st.selectbox('期間',['3 個月','6 個月','1 年','2 年','3 年','5 年','10 年','全部'],index=3,label_visibility='collapsed')
with c:
    if st.button('↺ 重設圖表',use_container_width=True):
        st.session_state['chart_reset']=st.session_state.get('chart_reset',0)+1
        st.rerun()
st.caption('選擇主圖與副圖技術指標；圖表只允許縮放及平移至所選歷史期間的起訖位置。')
with st.expander('📊 技術指標庫（31 種）',expanded=True):
    l,r=st.columns([1,1])
    with l:
        overlays=st.multiselect('主圖疊加（10 種）',OVERLAYS,default=[],max_selections=3)
    with r:
        subindicators=st.multiselect('K 線下方副圖（21 種）',SUBS,default=['MACD'],max_selections=3)
    st.caption('共 31 種可計算指標。最多 3 種主圖及 3 種副圖同時顯示，避免手機版過度擁擠。')
try:
    d=hist.copy()
    if kind=='週 K':d=d.resample('W-FRI').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
    if kind=='月 K':d=d.resample('ME').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
    n={'3 個月':93,'6 個月':184,'1 年':366,'2 年':731,'3 年':1097,'5 年':1827,'10 年':3653}.get(period)
    if n and not d.empty:d=d.loc[d.index>=d.index.max()-pd.Timedelta(days=n)]
    if d.empty:st.warning('這檔股票目前沒有可用的 K 線資料。')
    else:
        figure=draw(d,overlays,subindicators)
        figure.update_layout(uirevision='stockvision-'+str(st.session_state.get('chart_reset',0))+'-'+symbol+'-'+period+'-'+kind)
        st.plotly_chart(figure,use_container_width=True,
            config={'scrollZoom':True,'displaylogo':False,'responsive':True,
                    'modeBarButtonsToRemove':['select2d','lasso2d','autoScale2d']})
        st.caption(f'資料邊界：{d.index[0]:%Y-%m-%d} ～ {d.index[-1]:%Y-%m-%d}。滾輪縮放、拖曳平移，雙擊重設。')
except Exception as exc:st.error(f'圖表繪製失敗：{exc}')
with st.expander('📉 分時走勢（5 分鐘資料）'):
    try:
        intraday=minute_data(symbol,'5m')
        if intraday.empty:st.info('目前沒有分時資料。')
        else:
            st.line_chart(intraday.Close,color='#6bc9ff',height=190)
            st.caption('分時資料可能延遲，並非元大逐筆即時行情。')
    except Exception:st.info('分時資料暫時無法取得。')
# Only render tabs for actually available information. No invented order book, trades, shareholder or institutional data.
dv=dividend_data(symbol)
spl=split_data(symbol)
news=news_data(symbol)
basic={k:info.get(k) for k in ['sector','industry','marketCap','trailingPE','priceToBook','dividendYield','currency','exchange','website','longBusinessSummary'] if info.get(k) is not None}
tabnames=[]
if basic:tabnames.append('基本資料')
if not dv.empty or not spl.empty:tabnames.append('除權息')
if news:tabnames.append('個股新聞')
tabnames.extend(['財務報表','自選股'])
tabs=st.tabs(tabnames)
for label,tab in zip(tabnames,tabs):
    with tab:
        if label=='基本資料':
            labels={'sector':'產業部門','industry':'產業','marketCap':'市值','trailingPE':'本益比','priceToBook':'股價淨值比','dividendYield':'殖利率',
                    'currency':'幣別','exchange':'交易所','website':'公司網站','longBusinessSummary':'公司簡介'}
            st.dataframe(pd.DataFrame([{'項目':labels[k],'內容':str(v)} for k,v in basic.items()]),hide_index=True,use_container_width=True)
        elif label=='除權息':
            if not dv.empty:st.dataframe(dv.rename('每股現金股利').reset_index(),hide_index=True,use_container_width=True)
            if not spl.empty:st.dataframe(spl.rename('股票分割比例').reset_index(),hide_index=True,use_container_width=True)
        elif label=='個股新聞':
            for item in news[:12]:
                x=item.get('content',item)
                title=x.get('title') or '新聞'
                url=x.get('canonicalUrl') or x.get('clickThroughUrl') or item.get('link')
                if isinstance(url,dict):url=url.get('url')
                if isinstance(url,str) and re.match(r'^https://',url):
                    st.markdown(f'[{html.escape(title)}]({url})')
                else:st.write(title)
        elif label=='財務報表':
            ftype=st.selectbox('財報類型',['損益表','資產負債表','現金流量表'])
            df=statement(symbol,ftype)
            if df.empty:st.info('這檔股票目前沒有可取得的此類財報。')
            else:st.dataframe(df,use_container_width=True)
        elif label=='自選股':
            target=st.selectbox('加入分類',categories(),key='bottom_group')
            if st.button('⭐ 加入自選股',key='bottom_add'):
                add_watch_category(symbol,target);st.success('已加入')
st.caption('StockVision V11｜31 指標專業看盤版，非元大官方系統。尚未串接元大 SPARK API，未提供即時五檔、逐筆成交或下單。價格及資料可能延遲。')

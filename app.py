
import html
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import yfinance as yf
from engine import history
from symbols import resolve,long_history
from storage import categories,create_category,add_watch_category,watches_by_category,remove_watch
st.set_page_config(page_title="StockVision｜即時看盤工作台",page_icon="📈",layout="wide",initial_sidebar_state="collapsed")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;600;700&display=swap');
html,body,.stApp{font-family:'Noto Sans TC',sans-serif}
.stApp{background:#15293e;color:#f1f7ff}
[data-testid="stHeader"]{background:#233e59!important;min-height:2.5rem}
[data-testid="stToolbar"]{transform:scale(.77);transform-origin:top right}
[data-testid="stSidebar"]{background:#1d354d}
.block-container{max-width:1550px;padding:2.5rem 1rem 1rem}
h1,h2,h3{letter-spacing:.01em}
[data-testid="stMetric"]{background:#244159;border:1px solid #426079;border-radius:15px;padding:10px}
[data-testid="stMetricLabel"] p{color:#bed2e7!important}
[data-testid="stMetricValue"]{color:#f1f8ff!important}
[data-testid="stCaptionContainer"] p{color:#bcd2e6!important}
.stButton button{border-radius:12px}
[data-testid="stTabs"] button{font-size:clamp(12px,1.4vw,15px);font-weight:600;color:#c9def2;min-width:0;padding:.45rem .75rem}
[data-testid="stTabs"] button[aria-selected="true"]{color:#74f6dd}
[data-testid="stImage"] img{border-radius:15px}
[data-testid="stPlotlyChart"]{border:1px solid #3a5672;border-radius:14px;overflow:hidden}
.hero{background:linear-gradient(100deg,#22435e,#254d68);padding:12px 18px;border-radius:15px;margin:8px 0}
.hero strong{font-size:clamp(17px,2.2vw,25px)}
.hero span{color:#c4dcec;font-size:12px}
@media(max-width:700px){
.block-container{padding:.65rem .45rem 1rem}
[data-testid="stHeader"]{min-height:2rem}
[data-testid="stToolbar"]{transform:scale(.65)}
[data-testid="stTabs"] button{font-size:12px;padding:.3rem .5rem}
[data-testid="stMetric"]{padding:7px}
[data-testid="stMetricValue"]{font-size:1.15rem}
[data-testid="stImage"] img{max-height:95px;object-fit:cover}
}
</style>""",unsafe_allow_html=True)
st.image('header.png',use_container_width=True)
@st.cache_data(ttl=45,show_spinner=False)
def intraday(s):
    d=yf.Ticker(s).history(period='5d',interval='5m',auto_adjust=False)
    return d[['Open','High','Low','Close','Volume']].dropna() if not d.empty else d
@st.cache_data(ttl=300,show_spinner=False)
def latest(s):
    # 1m series is an indicative delayed vendor feed, not licensed real-time
    d=yf.Ticker(s).history(period='1d',interval='1m',auto_adjust=False)
    if not d.empty:
        return float(d.Close.iloc[-1]),str(d.index[-1]),'Yahoo 1 分鐘資料（可能延遲）'
    d=history(s)
    return float(d.Close.iloc[-1]),str(d.index[-1]),'歷史日收盤（非即時）'
@st.cache_data(ttl=1800,show_spinner=False)
def fundamentals(s):
    try:return yf.Ticker(s).info or {}
    except Exception:return {}
@st.cache_data(ttl=1800,show_spinner=False)
def payouts(s):
    try:return yf.Ticker(s).dividends
    except Exception:return pd.Series(dtype=float)
@st.cache_data(ttl=1800,show_spinner=False)
def actions(s):
    try:return yf.Ticker(s).splits
    except Exception:return pd.Series(dtype=float)
@st.cache_data(ttl=900,show_spinner=False)
def articles(s):
    try:return yf.Ticker(s).news or []
    except Exception:return []
@st.cache_data(ttl=3600,show_spinner=False)
def financials(s):
    try:return yf.Ticker(s).income_stmt
    except Exception:return pd.DataFrame()
def plot(d,line=False):
    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=.04,row_heights=[.77,.23])
    up='#ff4fa5';down='#39f5d0'
    if line:
        fig.add_trace(go.Scatter(x=d.index,y=d.Close,name='價格',line=dict(color='#79d6ff',width=2.5),fill='tozeroy',fillcolor='rgba(105,211,255,.12)'),row=1,col=1)
    else:
        fig.add_trace(go.Candlestick(x=d.index,open=d.Open,high=d.High,low=d.Low,close=d.Close,name='K 線',
            increasing_line_color=up,increasing_fillcolor=up,decreasing_line_color=down,decreasing_fillcolor=down),row=1,col=1)
    fig.add_trace(go.Bar(x=d.index,y=d.Volume,name='成交量',marker_color=[up if c>=o else down for o,c in zip(d.Open,d.Close)]),row=2,col=1)
    fig.update_layout(template='plotly_dark',paper_bgcolor='#20394f',plot_bgcolor='#20394f',
        height=480,font=dict(color='#e9f5ff',family='Noto Sans TC, sans-serif',size=11),
        margin=dict(l=5,r=5,t=12,b=6),showlegend=False,hovermode='x unified',dragmode='pan',
        xaxis_rangeslider_visible=False,uirevision='stockvision-v7')
    fig.update_xaxes(gridcolor='#35536b',showspikes=True)
    fig.update_yaxes(gridcolor='#35536b')
    return fig
with st.container():
    c1,c2,c3=st.columns([2.5,1.2,1.1],vertical_alignment='bottom')
    with c1:
        raw=st.text_input('搜尋股票代號',value=st.session_state.get('raw_symbol','2330'),placeholder='2330、6488、AAPL',label_visibility='collapsed')
    with c2:market=st.selectbox('市場',['自動判斷','台股','美股'],label_visibility='collapsed')
    with c3:
        if st.button('↻ 更新資料',use_container_width=True):
            latest.clear();intraday.clear();history.clear();st.rerun()
try:symbol=resolve(raw.strip().upper(),market)
except ValueError as e:st.error(str(e));st.stop()
info=fundamentals(symbol)
name=info.get('shortName') or info.get('longName') or symbol
st.markdown('<div class="hero"><strong>'+html.escape(name)+' · '+html.escape(raw.upper())+'</strong><div><span>'+html.escape(symbol)+'｜台美股行情與歷史資料</span></div></div>',unsafe_allow_html=True)
@st.fragment(run_every="5s")
def price_panel():
    try:
        p,t,source=latest(symbol)
        c1,c2,c3=st.columns([1.1,1.4,1.7])
        c1.metric('最新可取得價格',f'{p:,.2f}')
        c2.metric('行情資料時間',t.split('+')[0].replace('T',' ')[:19])
        c3.metric('資料來源',source)
        st.caption('畫面每 5 秒檢查一次；報價快取最多 5 分鐘。非交易所授權即時行情，價格可能不跳動。')
    except Exception as e:st.warning('報價暫時無法取得，請稍後更新。')
price_panel()
c1,c2=st.columns([3,1],vertical_alignment='bottom')
with c1:
    choice=st.segmented_control('圖表類型',['分時圖','日 K','週 K','月 K'],default='日 K',label_visibility='collapsed')
with c2:
    period=st.selectbox('時間範圍',['3 個月','1 年','5 年','10 年','全部'],index=1,label_visibility='collapsed')
try:
    if choice=='分時圖':
        d=intraday(symbol)
    else:
        d=long_history(symbol)
        if choice=='週 K':d=d.resample('W-FRI').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
        if choice=='月 K':d=d.resample('ME').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
        days={'3 個月':93,'1 年':366,'5 年':1827,'10 年':3653}.get(period)
        if days:d=d.loc[d.index>=d.index.max()-pd.Timedelta(days=days)]
    if d.empty:st.warning('這檔股票目前沒有可用的圖表資料。')
    else:
        st.plotly_chart(plot(d,line=choice=='分時圖'),use_container_width=True,
            config={'scrollZoom':True,'displaylogo':False,'responsive':True,'modeBarButtonsToRemove':['select2d','lasso2d','autoScale2d']})
        st.caption(f'資料範圍：{d.index[0]:%Y-%m-%d} 至 {d.index[-1]:%Y-%m-%d}｜滑鼠滾輪縮放，拖曳平移，雙擊重設')
except Exception:st.warning('圖表資料暫時無法取得，請稍後再試。')
# Only show information tabs that actually have source data
dv=payouts(symbol)
sp=actions(symbol)
fin=financials(symbol)
news=articles(symbol)
details={k:info.get(k) for k in ['sector','industry','marketCap','trailingPE','priceToBook','dividendYield','website','currency','exchange','longBusinessSummary'] if info.get(k) is not None}
available=[]
if not dv.empty or not sp.empty:available.append('除權息')
if details:available.append('基本資料')
if isinstance(fin,pd.DataFrame) and not fin.empty:available.append('財務報表')
if news:available.append('新聞')
available.append('自選股書籤')
tabs=st.tabs(available)
for label,tab in zip(available,tabs):
    with tab:
        if label=='除權息':
            if not dv.empty:
                st.write('**歷史現金股利**')
                st.dataframe(dv.rename('每股配息').reset_index(),hide_index=True,use_container_width=True)
            if not sp.empty:
                st.write('**歷史股票分割**')
                st.dataframe(sp.rename('分割比例').reset_index(),hide_index=True,use_container_width=True)
        elif label=='基本資料':
            names={'sector':'產業部門','industry':'產業類別','marketCap':'市值','trailingPE':'本益比','priceToBook':'股價淨值比',
                'dividendYield':'股息殖利率','website':'公司網站','currency':'幣別','exchange':'交易所','longBusinessSummary':'公司介紹'}
            st.dataframe(pd.DataFrame([{'項目':names[k],'資料':str(v)} for k,v in details.items()]),hide_index=True,use_container_width=True)
        elif label=='財務報表':
            st.dataframe(fin,use_container_width=True)
        elif label=='新聞':
            for item in news[:12]:
                x=item.get('content',item)
                title=x.get('title') or '新聞'
                link=x.get('canonicalUrl') or x.get('clickThroughUrl') or item.get('link')
                if isinstance(link,dict):link=link.get('url')
                if isinstance(link,str) and link.startswith('https://'):st.markdown(f'[{html.escape(title)}]({link})')
                else:st.write(title)
        elif label=='自選股書籤':
            a,b=st.columns(2)
            with a:
                group=st.selectbox('書籤分類',categories())
                if st.button('⭐ 加入這個分類'):add_watch_category(symbol,group);st.success('已加入')
            with b:
                new=st.text_input('新增分類名稱')
                if st.button('建立分類') and new.strip():create_category(new.strip());st.rerun()
            stocks=watches_by_category(group)
            st.write('、'.join(stocks) if stocks else '這個分類目前沒有股票')
            if stocks:
                chosen=st.selectbox('移除股票',stocks)
                if st.button('移除所選'):remove_watch(chosen);st.rerun()
st.caption('StockVision V7｜僅顯示可取得資料的分頁。資料來自第三方，可能延遲、缺漏；不構成投資建議。')

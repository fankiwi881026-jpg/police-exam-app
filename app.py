import re
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import streamlit as st
import yfinance as yf
from engine import history
from storage import watches, add_watch, remove_watch

st.set_page_config(page_title="StockVision｜智慧看盤",page_icon="📊",layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;600;700;800&display=swap');
html,body,[class*="st-"]{font-family:'Noto Sans TC',sans-serif}
.stApp{background:linear-gradient(135deg,#15273d 0%,#101d30 55%,#162b42 100%);color:#eaf4ff}
[data-testid="stSidebar"]{background:#1b3048;border-right:1px solid #37506a}
.block-container{max-width:1540px;padding-top:1.2rem}
[data-testid="stMetric"]{background:#20374f;border:1px solid #385571;padding:15px;border-radius:17px}
[data-testid="stMetricLabel"] p{color:#b7d0e8!important}
[data-testid="stMetricValue"]{color:#f5fbff!important}
[data-testid="stCaptionContainer"] p{color:#b5cce0!important}
h1,h2,h3{color:#f5fbff!important;letter-spacing:.01em}
[data-testid="stTabs"] button{font-weight:700!important;color:#d3e6f8!important;font-size:15px!important}
[data-testid="stTabs"] button[aria-selected="true"]{color:#65e3ca!important}
.stButton button{border-radius:12px}
div[data-testid="stDataFrame"]{border-radius:14px;overflow:hidden}
.hero{border-radius:20px;padding:22px 25px;margin-bottom:14px;background:linear-gradient(110deg,#244965,#20344e);border:1px solid #41617b}
.hero .overline{color:#72e6ce;font-size:12px;letter-spacing:2px;font-weight:800}
.hero h1{font-size:2.1rem;margin:5px 0}
.hero p{margin:0;color:#c5daeb}
@media(max-width:700px){.block-container{padding:1rem .65rem}.hero{padding:15px}.hero h1{font-size:1.55rem}}
</style>""",unsafe_allow_html=True)
st.markdown('<div class="hero"><div class="overline">STOCKVISION · MARKET STUDIO</div><h1>看懂市場，從這裡開始。</h1><p>分時・價量・K 線・公司資訊｜繁體中文看盤工作台</p></div>',unsafe_allow_html=True)

@st.cache_data(ttl=5,show_spinner=False)
def tw_quote(s):
    m=re.fullmatch(r'(\d{4,6})\.(TW|TWO)',s)
    if not m:return None
    exchange='tse' if m.group(2)=='TW' else 'otc'
    r=requests.get('https://mis.twse.com.tw/stock/api/getStockInfo.jsp',
        params={'ex_ch':f'{exchange}_{m.group(1)}.tw','json':'1','delay':'0'},
        headers={'User-Agent':'Mozilla/5.0','Referer':'https://mis.twse.com.tw/'},timeout=6)
    r.raise_for_status()
    a=r.json().get('msgArray') or []
    if not a:return None
    v=a[0]
    try:price=float(v['z'].split('_')[0].replace(',',''))
    except (KeyError,ValueError,AttributeError):return None
    if price<=0:return None
    return {'價格':price,'日期':v.get('d','—'),'時間':v.get('t','—'),'來源':'證交所 MIS 公開查詢（可能延遲）'}
@st.cache_data(ttl=60,show_spinner=False)
def intraday(s):
    d=yf.Ticker(s).history(period='5d',interval='5m',auto_adjust=True)
    if d.empty:return d
    return d[['Open','High','Low','Close','Volume']].dropna()
@st.cache_data(ttl=1800,show_spinner=False)
def profile(s):
    try:return yf.Ticker(s).info or {}
    except Exception:return {}
@st.cache_data(ttl=1800,show_spinner=False)
def dividends(s):
    try:return yf.Ticker(s).dividends.tail(15)
    except Exception:return pd.Series(dtype=float)
@st.cache_data(ttl=900,show_spinner=False)
def news(s):
    try:return yf.Ticker(s).news or []
    except Exception:return []
def quote(s):
    if s.endswith(('.TW','.TWO')):
        try:
            q=tw_quote(s)
            if q:return q
        except Exception:pass
    try:
        d=history(s)
        return {'價格':float(d.Close.iloc[-1]),'日期':d.index[-1].strftime('%Y-%m-%d'),'時間':'日收盤','來源':'Yahoo Finance 歷史資料'}
    except Exception:return None

def chart(d,mode='k',indicator=False):
    d=d.tail(180 if mode=='k' else 350)
    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=.035,row_heights=[.78,.22])
    up='#ff7f91';down='#48d9ba'
    if mode=='line':
        fig.add_trace(go.Scatter(x=d.index,y=d.Close,mode='lines',name='成交價格',line=dict(color='#73b9ff',width=2.8),fill='tozeroy',fillcolor='rgba(86,164,255,.08)'),row=1,col=1)
    else:
        fig.add_trace(go.Candlestick(x=d.index,open=d.Open,high=d.High,low=d.Low,close=d.Close,name='K 線',
           increasing_line_color=up,increasing_fillcolor=up,decreasing_line_color=down,decreasing_fillcolor=down,
           whiskerwidth=.35),row=1,col=1)
    if indicator and len(d)>=20:
        ma=d.Close.rolling(20).mean()
        fig.add_trace(go.Scatter(x=d.index,y=ma,mode='lines',name='20 期均線',line=dict(color='#ffcc78',width=1.7)),row=1,col=1)
    fig.add_trace(go.Bar(x=d.index,y=d.Volume,name='成交量',
        marker_color=[up if c>=o else down for o,c in zip(d.Open,d.Close)],opacity=.75),row=2,col=1)
    fig.update_layout(template='plotly_dark',height=590,paper_bgcolor='#1c3047',plot_bgcolor='#1c3047',
        font=dict(family='Noto Sans TC, sans-serif',color='#e8f2ff',size=12),margin=dict(l=8,r=8,t=18,b=10),
        showlegend=indicator,legend=dict(orientation='h',y=1.05),hovermode='x unified',dragmode='pan',
        xaxis_rangeslider_visible=False,uirevision='market-chart')
    fig.update_xaxes(gridcolor='#30485f',showspikes=True,spikecolor='#a8c6dc')
    fig.update_yaxes(gridcolor='#30485f',showspikes=True,spikecolor='#a8c6dc')
    return fig
with st.sidebar:
    st.markdown('### 🧭 看盤導覽')
    symbol=st.text_input('股票代號',value='2330.TW',help='台股 2330.TW、上櫃 6488.TWO、美股 AAPL').strip().upper()
    if st.button('🔄 更新行情',use_container_width=True):
        history.clear();intraday.clear();tw_quote.clear();st.rerun()
    st.divider()
    new=st.text_input('加入自選股',placeholder='例如 AAPL')
    if st.button('⭐ 新增',use_container_width=True) and new.strip():
        add_watch(new.strip().upper());st.rerun()
    w=watches()
    if w:
        remove=st.selectbox('移除自選股',w)
        if st.button('移除',use_container_width=True):remove_watch(remove);st.rerun()
    st.caption('台股證交所公開行情、美股 Yahoo Finance。並非交易所授權的逐筆即時報價。')

tabs=st.tabs(['分時圖','價量','K 線','指標','成分股','除權息','折溢價','法人','籌碼','主力','資券','權證','新聞','大戶','基本資料'])
try: daily=history(symbol)
except Exception as e:daily=None;st.error(f'無法取得日 K：{e}')
with tabs[0]:
    st.subheader('📈 分時走勢')
    st.caption('免費來源提供 5 分鐘 K 資料，通常有延遲；不是每 5 秒成交價。')
    d=intraday(symbol)
    if d.empty:st.warning('目前沒有可用的分時資料，請確認代號或稍後再試。')
    else:
        st.plotly_chart(chart(d,mode='line'),use_container_width=True,config={'scrollZoom':True,'displaylogo':False,'locale':'zh-TW'})
        st.caption(f'最後一筆分時資料：{d.index[-1]}')
with tabs[1]:
    st.subheader('📊 價量資訊')
    if daily is not None:
        r=daily.iloc[-1];p=daily.iloc[-2] if len(daily)>1 else r
        cols=st.columns(4)
        for col,title,value in zip(cols,['最新日收盤','日漲跌幅','日成交量','資料日期'],
                                   [f'{r.Close:,.2f}',f'{(r.Close/p.Close-1):+.2%}',f'{int(r.Volume):,}',f'{daily.index[-1]:%Y-%m-%d}']):
            col.metric(title,value)
        st.plotly_chart(chart(daily),use_container_width=True,config={'scrollZoom':True,'displaylogo':False})
    st.caption('日 K 資料與盤中快照來源不同，價格可能不一致。')
with tabs[2]:
    st.subheader('🕯️ K 線圖')
    period=st.radio('顯示範圍',['近 1 個月','近 3 個月','近 6 個月','近 1 年'],index=2,horizontal=True)
    if daily is not None:
        n={'近 1 個月':23,'近 3 個月':66,'近 6 個月':130,'近 1 年':252}[period]
        st.plotly_chart(chart(daily.tail(n)),use_container_width=True,config={'scrollZoom':True,'displaylogo':False})
        st.caption('滑鼠滾輪縮放、拖曳平移、雙擊重設。紅漲綠跌。')
with tabs[3]:
    st.subheader('🧭 指標')
    st.info('依照你的前次要求，預設不顯示任何均線、支撐線、壓力線或布林帶。')
    show=st.checkbox('顯示 20 期均線（選用）',value=False)
    if daily is not None:st.plotly_chart(chart(daily,indicator=show),use_container_width=True,config={'scrollZoom':True,'displaylogo':False})
with tabs[4]:
    st.subheader('🧩 成分股')
    st.info('此功能適用於指數及 ETF，需另串接官方指數成分股資料。目前尚未接入，避免顯示錯誤名單。')
with tabs[5]:
    st.subheader('💰 除權息')
    dv=dividends(symbol)
    if dv.empty:st.info('資料來源目前未提供可顯示的歷史配息。')
    else:
        t=dv.rename('每股配息').reset_index()
        st.dataframe(t,use_container_width=True,hide_index=True)
    st.caption('僅供參考，正式公告以交易所及發行公司為準。')
with tabs[6]:
    st.subheader('⚖️ 折溢價')
    st.info('僅適用有淨值資料的 ETF 等商品；需同步取得最新市價及淨值，目前未接入。')
with tabs[7]:
    st.subheader('🏛️ 三大法人')
    st.info('外資、投信、自營商買賣超需串接交易所官方法人資料；尚未接入。')
with tabs[8]:
    st.subheader('🧮 籌碼')
    st.info('籌碼集中度、持股分布等需專用資料來源；尚未接入。')
with tabs[9]:
    st.subheader('🎯 主力')
    st.info('主力買賣超需合法券商分點及相關資料來源；尚未接入。')
with tabs[10]:
    st.subheader('🏦 資券')
    st.info('融資融券餘額與變化需交易所官方資料；尚未接入。')
with tabs[11]:
    st.subheader('🎟️ 權證')
    st.info('權證篩選、履約價、到期日等需權證商品資料庫；尚未接入。')
with tabs[12]:
    st.subheader('📰 個股新聞')
    entries=news(symbol)
    if not entries:st.info('目前沒有取得新聞資料。')
    for item in entries[:12]:
        x=item.get('content',item)
        title=x.get('title') or item.get('title') or '新聞'
        link=x.get('canonicalUrl') or x.get('clickThroughUrl') or item.get('link')
        if isinstance(link,dict):link=link.get('url')
        if isinstance(link,str) and link.startswith('https://'):
            st.markdown(f'**[{title}]({link})**')
        else:st.write('• '+title)
    st.caption('新聞由第三方資料來源提供，可能延遲或缺漏。')
with tabs[13]:
    st.subheader('🐋 大戶')
    st.info('大戶持股分級、集保戶數等需臺灣集保結算所資料；尚未接入。')
with tabs[14]:
    st.subheader('🏢 基本資料')
    p=profile(symbol)
    fields={'longName':'公司名稱','sector':'產業部門','industry':'產業分類','marketCap':'市值',
            'trailingPE':'本益比','priceToBook':'股價淨值比','website':'官方網站','currency':'幣別'}
    values=[{'項目':v,'內容':str(p[k])} for k,v in fields.items() if k in p and p[k] is not None]
    if values:st.dataframe(pd.DataFrame(values),hide_index=True,use_container_width=True)
    else:st.info('目前無法取得公司基本資料。')
st.divider()
st.subheader('⭐ 自選股速覽')
@st.fragment(run_every='5s')
def watch_panel():
    symbols=list(dict.fromkeys(([symbol] if symbol else [])+watches()))[:12]
    rows=[]
    for s in symbols:
        q=quote(s)
        rows.append({'股票':s,'最新可取得價格':q['價格'] if q else None,
                     '行情日期':q['日期'] if q else '—','行情時間':q['時間'] if q else '—',
                     '資料來源':q['來源'] if q else '無法取得'})
    st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
    st.caption('每 5 秒檢查一次公開行情（僅網頁開啟時）。查詢時間：'+datetime.now(ZoneInfo('Asia/Taipei')).strftime('%H:%M:%S')+'；不保證每次有新報價。')
watch_panel()

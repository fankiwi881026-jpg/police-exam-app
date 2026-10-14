import re
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from engine import history
from storage import watches, add_watch, remove_watch

st.set_page_config(page_title='StockVision｜中文看盤',page_icon='📈',layout='wide')
st.markdown('''<style>
.stApp {background:#14243a;color:#f5f8ff}
[data-testid="stSidebar"] {background:#1c304a}
[data-testid="stMetric"] {background:#213953;border:1px solid #425a74;border-radius:15px;padding:14px}
[data-testid="stMetricLabel"] p {color:#c7d7ec!important}
[data-testid="stMetricValue"] {color:#fff!important}
[data-testid="stCaptionContainer"] p {color:#cbd9ea!important}
.block-container {padding-top:1.2rem;max-width:1500px}
h1,h2,h3,p,label {color:#f4f8ff}
@media(max-width:650px){.block-container{padding:.9rem .65rem}}
</style>''',unsafe_allow_html=True)

@st.cache_data(ttl=4,show_spinner=False)
def twse_quote(symbol):
    # 公開 MIS 查詢介面，可能限流、停用或變更；不可視為授權即時行情服務。
    m=re.fullmatch(r'(\d{4,6})\.(TW|TWO)',symbol.upper())
    if not m:return None
    market='tse' if m.group(2)=='TW' else 'otc'
    response=requests.get('https://mis.twse.com.tw/stock/api/getStockInfo.jsp',params={'ex_ch':f'{market}_{m.group(1)}.tw','json':'1','delay':'0'},headers={'User-Agent':'Mozilla/5.0','Referer':'https://mis.twse.com.tw/'},timeout=7)
    response.raise_for_status()
    data=response.json().get('msgArray') or []
    if not data:return None
    r=data[0]
    def num(k):
        try:return float(r[k].split('_')[0].replace(',',''))
        except (KeyError,ValueError,AttributeError):return None
    price=num('z')
    if price is None or price<=0:return None
    return {'price':price,'name':r.get('n') or symbol,'date':r.get('d',''),'time':r.get('t',''), 'source':'證交所公開 MIS 查詢介面（非授權即時行情保證）'}

def quote(symbol):
    if symbol.endswith(('.TW','.TWO')):
        try:
            r=twse_quote(symbol)
            if r:return r
        except Exception:pass
    try:
        d=history(symbol)
        return {'price':float(d.Close.iloc[-1]),'name':symbol,'date':d.index[-1].strftime('%Y%m%d'),'time':'收盤','source':'Yahoo Finance 歷史日 K（可能延遲）'}
    except Exception:return None

def candle_chart(df):
    d=df.tail(240)
    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=.04,row_heights=[.78,.22])
    fig.add_trace(go.Candlestick(x=d.index,open=d.Open,high=d.High,low=d.Low,close=d.Close,name='K 線',increasing_line_color='#ff696f',decreasing_line_color='#42d6a4',increasing_fillcolor='#ff696f',decreasing_fillcolor='#42d6a4'),row=1,col=1)
    fig.add_trace(go.Bar(x=d.index,y=d.Volume,name='成交量',marker_color=['#ff696f' if c>=o else '#42d6a4' for o,c in zip(d.Open,d.Close)]),row=2,col=1)
    fig.update_layout(template='plotly_dark',paper_bgcolor='#1c304a',plot_bgcolor='#1c304a',font=dict(color='#f3f7ff'),height=630,margin=dict(l=5,r=8,t=20,b=10),showlegend=False,xaxis_rangeslider_visible=False,dragmode='pan',hovermode='x unified',uirevision='保留縮放')
    fig.update_xaxes(gridcolor='#304b67',showspikes=True)
    fig.update_yaxes(gridcolor='#304b67',showspikes=True)
    return fig

st.title('📈 StockVision｜中文看盤')
st.caption('純 K 線與成交量 · 無均線、無支撐壓力、無布林帶 · 台股公開行情查詢可能延遲、限流或暫時不可用')
with st.sidebar:
    st.header('看盤設定')
    symbol=st.text_input('股票代號',value='2330.TW',help='台灣上市 2330.TW｜上櫃 6488.TWO｜美股 AAPL').strip().upper()
    refresh=st.toggle('每 5 秒檢查一次報價',value=True)
    st.caption('僅在網頁保持開啟時檢查；非背景通知。')
    if st.button('立即重新取得日 K'):
        history.clear();st.rerun()
    st.divider()
    st.subheader('自選股管理')
    new=st.text_input('新增代號',placeholder='例如 2330.TW')
    if st.button('加入自選股') and new.strip():
        add_watch(new.strip().upper());st.rerun()
    current=watches()
    if current:
        delete=st.selectbox('選擇要刪除的股票',current)
        if st.button('刪除自選股'):
            remove_watch(delete);st.rerun()

@st.fragment(run_every='5s')
def live_panel():
    st.subheader('📡 行情快照')
    if not refresh:
        st.info('自動檢查已暫停。')
    items=list(dict.fromkeys(([symbol] if symbol else [])+watches()))[:15]
    rows=[]
    for s in items:
        r=quote(s)
        if r:
            rows.append({'股票':s,'名稱':r['name'],'最新可取得價格':r['price'],'行情日期':r['date'],'行情時間':r['time'],'資料來源':r['source']})
        else:rows.append({'股票':s,'名稱':'—','最新可取得價格':None,'行情日期':'—','行情時間':'—','資料來源':'無法取得；可能休市、限流或來源異常'})
    if rows:
        st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
    st.caption('本頁查詢時間（台北）：'+datetime.now(ZoneInfo('Asia/Taipei')).strftime('%Y-%m-%d %H:%M:%S')+'｜查詢時間不等於交易所報價時間。')
    if len(items)>5:st.warning('追蹤股票較多時，每 5 秒查詢可能被行情來源限流；建議降低更新頻率。')

live_panel()
st.subheader(f'🕯️ {symbol}｜日 K 線與成交量')
st.caption('滑鼠滾輪縮放圖表、按住左鍵拖曳平移；雙擊圖表恢復原始視角。手機可用雙指縮放。')
try:
    df=history(symbol)
    st.plotly_chart(candle_chart(df),use_container_width=True,config={'scrollZoom':True,'displaylogo':False,'locale':'zh-TW','displayModeBar':True})
    st.caption(f'日 K 最後交易日期：{df.index[-1]:%Y-%m-%d}｜日 K 使用 Yahoo Finance 歷史資料，不會每 5 秒產生新 K 棒。')
except Exception as e:
    st.error(f'無法取得 {symbol} 日 K：{e}')
st.info('提醒：這是行情檢視原型，不是證交所授權的即時報價終端。若要穩定 5 秒更新或盤中逐筆資料，須串接合法授權的報價供應商。')

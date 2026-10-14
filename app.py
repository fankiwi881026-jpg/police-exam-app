import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from engine import history,indicators,levels,score,backtest
from storage import watches,add_watch,remove_watch,add_alert,alerts,delete_alert,mark_fired

st.set_page_config(page_title='StockVision 股票技術分析',page_icon='📈',layout='wide',initial_sidebar_state='expanded')
st.markdown('<div class="hero"><div class="eyebrow">STOCKVISION · MARKET INTELLIGENCE</div><h1>📈 StockVision</h1><p>台股 × 美股｜讓趨勢、支撐與量價訊號一眼看懂</p></div>', unsafe_allow_html=True)
st.caption('每日歷史行情研究工具｜免費資料可能延遲，並非逐筆即時行情或交易建議。')
with st.sidebar:
    st.markdown('### ◉ STOCKVISION')
    st.caption('深色金融儀表板 · v2')
    auto_refresh = False
    st.caption('🟢 網頁在線 ≠ 交易所即時報價')

with st.sidebar:
    page=st.radio('功能', ['技術分析','自選股','價格警示','條件選股','策略回測'])
    symbol=st.text_input('股票代號',value='2330.TW').strip().upper()
    st.caption('上市：2330.TW｜上櫃：6488.TWO｜美股：AAPL')
    if st.button('🔄 重新抓取行情'):
        history.clear();st.rerun()


st.markdown('''<style>
html, body, .stApp, .stMarkdown, label {color:#edf4ff}
[data-testid='stWidgetLabel'] p,[data-testid='stCaptionContainer'] p {color:#b6c8df!important}
[data-testid='stDataFrame'],[data-testid='stTable'] {background:#15253b}
[data-baseweb='input'] input,[data-baseweb='select'] div,textarea {color:#f4f8ff!important;background:#182c45!important}
[data-testid='stSidebar'] * {color:#edf4ff!important}

:root {color-scheme:dark}
.stApp, [data-testid="stAppViewContainer"] {background: radial-gradient(circle at 85% 0%,#182943 0%,#15253c 50%,#101c30 100%);color:#e7edf8}
[data-testid="stSidebar"] {background:#17283f;border-right:1px solid #233249}
[data-testid="stHeader"] {background:transparent}
.block-container {padding-top:1.4rem;max-width:1500px}
.hero {padding:28px 30px;border:1px solid #2b3c56;border-radius:22px;background:linear-gradient(120deg,#182945,#0d1728);margin-bottom:14px;box-shadow:0 16px 38px #0004}
.hero h1 {font-size:clamp(2rem,4vw,3rem);margin:2px 0 5px;letter-spacing:-.035em;color:#f2f7ff}
.hero p {color:#aebed5;margin:0}
.eyebrow {font-size:11px;font-weight:750;letter-spacing:.17em;color:#5ce3c3}
[data-testid="stMetric"] {background:#203650;padding:18px;border:1px solid #2b3c56;border-radius:16px}
[data-testid="stMetricLabel"] {color:#a8bad2}
[data-testid="stMetricValue"] {color:#f3f7ff}
.stButton button[kind="primary"],.stButton button {border-radius:12px;border:1px solid #344762;background:#1b2c46;color:#e9f2ff}
.stButton button:hover {border-color:#55d4b8;color:#7af5d6}
[data-testid="stPlotlyChart"] {border:1px solid #2b3c56;border-radius:18px;overflow:hidden;background:#182c45}
@media(max-width:650px){.block-container{padding:1rem .75rem}.hero{padding:18px}.hero h1{font-size:1.9rem}[data-testid="stMetric"]{padding:10px}}
</style>''',unsafe_allow_html=True)

def load(s):
    try: return indicators(history(s))
    except Exception as e:
        st.error(f'{s} 取得資料失敗：{e}')
        return None

def plot(d,show_levels=True):
    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=.045,row_heights=[.76,.24])
    fig.add_trace(go.Candlestick(x=d.index,open=d.Open,high=d.High,low=d.Low,close=d.Close,name='K線',increasing_line_color='#d84b54',decreasing_line_color='#1baf80'),row=1,col=1)
    for name,color in [('MA20','#f2a93b'),('MA60','#4e98e5'),('MA120','#a57be2')]:
        fig.add_trace(go.Scatter(x=d.index,y=d[name],name=name,line=dict(color=color,width=1.6)),row=1,col=1)
    for name in ('BB_UP','BB_LOW'):
        fig.add_trace(go.Scatter(x=d.index,y=d[name],name=name,line=dict(color='#28a99b',width=1,dash='dot')),row=1,col=1)
    if show_levels:
        su,re=levels(d)
        for val,count in su:fig.add_hline(y=val,line_color='#20a47b',line_dash='dash',annotation_text=f'支撐 {val:.2f} ({count})',row=1,col=1)
        for val,count in re:fig.add_hline(y=val,line_color='#e05a62',line_dash='dash',annotation_text=f'壓力 {val:.2f} ({count})',row=1,col=1)
    colors=['#d84b54' if c>=o else '#1baf80' for o,c in zip(d.Open,d.Close)]
    fig.add_trace(go.Bar(x=d.index,y=d.Volume,marker_color=colors,name='成交量'),row=2,col=1)
    for name,color in [('VMA5','#f2a93b'),('VMA20','#4e98e5')]:
        fig.add_trace(go.Scatter(x=d.index,y=d[name],name=name,line=dict(color=color,width=1.4)),row=2,col=1)
    fig.update_layout(template='plotly_dark',paper_bgcolor='#182c45',plot_bgcolor='#182c45',font=dict(color='#d9e4f5'),height=620,margin=dict(l=8,r=8,t=28,b=12),xaxis_rangeslider_visible=False,legend=dict(orientation='h',y=1.10),hovermode='x unified')
    fig.update_xaxes(gridcolor='#26354d',zeroline=False)
    fig.update_yaxes(gridcolor='#26354d',zeroline=False)
    fig.update_xaxes(rangebreaks=[dict(bounds=['sat','mon'])])
    return fig

if page=='技術分析':
    d=load(symbol)
    if d is not None:
        r=d.iloc[-1];s,notes=score(d)
        previous=float(d.Close.iloc[-2]) if len(d)>1 else float(r.Close)
        delta=float(r.Close)-previous
        date=d.index[-1].strftime('%Y-%m-%d')
        st.subheader(f'📌 {symbol}｜最新可取得日 K')
        st.caption(f'資料日期：{date}｜收盤價，不是即時成交價｜來源 Yahoo Finance')
        a,b,c,dcol=st.columns(4)
        a.metric('最新收盤價',f'{r.Close:,.2f}',f'{delta:+,.2f} ({delta/previous:+.2%})' if previous else None)
        b.metric('20 日均線',f'{r.MA20:,.2f}' if pd.notna(r.MA20) else '—')
        c.metric('量比 / 20日均量',f'{r.VOL_RATIO:.2f}' if pd.notna(r.VOL_RATIO) else '—')
        dcol.metric('技術評分',f'{s}/100' if s is not None else '資料不足')
        st.plotly_chart(plot(d),use_container_width=True)
        su,re=levels(d)
        st.write('**支撐**：',', '.join(f'{v:.2f}（{n}次）' for v,n in su) or '無已確認支撐')
        st.write('**壓力**：',', '.join(f'{v:.2f}（{n}次）' for v,n in re) or '無已確認壓力')
        with st.expander('查看評分依據'):
            st.write('；'.join(notes) if notes else '尚未符合加分條件')
        if st.button('⭐ 加入自選股'):
            add_watch(symbol);st.success('已加入自選股，請到左側「自選股」查看')
elif page=='自選股':
    st.subheader('⭐ 我的自選股')
    st.caption('顯示最新可取得的每日收盤資料；不是即時盤中價格。日期會顯示在每一列。')
    x,y=st.columns([3,1])
    with x:
        entry=st.text_input('新增股票代號',value=symbol,key='watch_add',help='台股例如 2330.TW；美股例如 AAPL')
    with y:
        st.write(' ')
        if st.button('＋ 新增',use_container_width=True):
            if entry.strip():add_watch(entry.strip().upper());st.rerun()
    if st.button('🔄 更新全部自選股行情'):
        history.clear();st.rerun()
    symbols=watches()
    if not symbols:
        st.info('目前沒有自選股，請先輸入股票代號並按「新增」。')
    else:
        rows=[]
        for s in symbols:
            try:
                d=indicators(history(s))
                if len(d)<2: raise ValueError('資料不足')
                r=d.iloc[-1];prev=float(d.Close.iloc[-2]);price=float(r.Close)
                sc,_=score(d)
                rows.append({'股票代號':s,'最新收盤價':round(price,2),'漲跌':round(price-prev,2),
                             '漲跌幅':f'{(price/prev-1):+.2%}' if prev else '—',
                             '資料日期':d.index[-1].strftime('%Y-%m-%d'),
                             'MA20':round(float(r.MA20),2) if pd.notna(r.MA20) else None,
                             '技術評分':sc if sc is not None else '—','資料狀態':'正常'})
            except Exception:
                rows.append({'股票代號':s,'最新收盤價':None,'漲跌':None,'漲跌幅':'—',
                             '資料日期':'—','MA20':None,'技術評分':'—','資料狀態':'無法取得行情'})
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
        st.caption('若價格沒有變動，可能是休市、行情來源延遲，或當日資料尚未發布。')
        remove=st.selectbox('移除自選股',symbols)
        if st.button('移除所選股票'):
            remove_watch(remove);st.rerun()
elif page=='價格警示':
    with st.form('alert'):
        direction=st.selectbox('觸發條件',['突破','跌破'])
        target=st.number_input('目標價格',min_value=.0001,value=100.0)
        if st.form_submit_button('新增警示'):add_alert(symbol,direction,target);st.success('已儲存')
    st.caption('警示僅在此頁開啟或重新整理時檢查；依最新可取得收盤價，不會背景發送通知。')
    for i,s,direction,target,fired in alerts():
        if not fired:
            data=load(s)
            if data is not None:
                price=float(data.Close.iloc[-1]);hit=(price>=target if direction=='突破' else price<=target)
                if hit:mark_fired(i);fired=1
        a,b=st.columns([5,1]);a.write(f'{s}｜{direction} {target:g}｜{"🔔 已觸發" if fired else "等待中"}')
        if b.button('刪除',key='del'+str(i)):delete_alert(i);st.rerun()
elif page=='條件選股':
    universe=st.text_area('股票清單（逗號或換行分隔；建議每次最多 20 檔）',value='2330.TW,2317.TW,2454.TW,AAPL,MSFT,NVDA')
    strategy=st.selectbox('篩選條件',['均線多頭排列','收盤站上三均線','放量上漲','技術評分 ≥ 70'])
    if st.button('開始掃描'):
        syms=list(dict.fromkeys(x.strip().upper() for x in universe.replace('\n',',').split(',') if x.strip()))[:20]
        results=[]
        bar=st.progress(0)
        for j,s in enumerate(syms):
            d=load(s)
            if d is not None and len(d)>=120:
                r=d.iloc[-1];prev=d.iloc[-2];v,_=score(d)
                match={'均線多頭排列':r.MA20>r.MA60>r.MA120,'收盤站上三均線':all(r.Close>r[f'MA{n}'] for n in (20,60,120)),'放量上漲':r.Close>prev.Close and r.VOL_RATIO>=1.5,'技術評分 ≥ 70':v>=70}[strategy]
                if match:results.append({'代號':s,'收盤':round(r.Close,2),'量比':round(r.VOL_RATIO,2),'評分':v})
            bar.progress((j+1)/max(len(syms),1))
        st.dataframe(pd.DataFrame(results),use_container_width=True)
        st.caption('僅掃描輸入清單，不代表掃描整個交易所。')
else:
    d=load(symbol)
    if d is not None:
        cost=st.slider('單次換倉成本（基點，1 bps = 0.01%）',0,100,15)
        result=backtest(d,cost)
        if result:
            a,b,c,e=st.columns(4)
            a.metric('累積報酬',f'{result["return"]:.1%}')
            b.metric('年化報酬',f'{result["cagr"]:.1%}')
            c.metric('最大回撤',f'{result["drawdown"]:.1%}')
            e.metric('持倉狀態變更次數',result['trades'])
            st.line_chart(pd.DataFrame({'策略':result['equity'],'買入持有':result['benchmark']}))
            st.caption(result['note'])
            st.warning('示範回測未考慮真實成交限制、滑價、稅費差異及除權息現金流；不可視為實盤預期績效。')
        else:st.info('歷史資料不足，無法回測。')



"""31 independently calculated technical indicators; educational analytics, not investment advice."""
import numpy as np
import pandas as pd

OVERLAYS=["MA 均線","EMA 指數均線","WMA 加權均線","布林通道 BOLL","一目均衡表 Ichimoku","VWAP 成交量加權價","SAR 拋物線","唐奇安通道 Donchian","肯特納通道 Keltner","超級趨勢 Supertrend"]
SUBS=["MACD","RSI","KD 隨機指標","Stoch RSI","CCI","DMI / ADX","ATR","ROC","MOM 動能","Williams %R","MFI 資金流量","OBV","ADL 累積派發","CMF","成交量 Volume","成交量均線 VMA","TRIX","PPO","PVO","Aroon","Ultimate Oscillator"]
ALL=OVERLAYS+SUBS
assert len(ALL)==31

def ema(s,n):return s.ewm(span=n,adjust=False,min_periods=n).mean()
def atr(d,n=14):
    prev=d.Close.shift()
    tr=pd.concat([d.High-d.Low,(d.High-prev).abs(),(d.Low-prev).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/n,adjust=False,min_periods=n).mean()
def psar(d,step=.02,maximum=.2):
    h=d.High.to_numpy();l=d.Low.to_numpy();n=len(d)
    out=np.full(n,np.nan)
    if n<2:return pd.Series(out,index=d.index)
    rising=h[1]>=h[0];ep=h[1] if rising else l[1];sar=l[0] if rising else h[0];af=step
    for i in range(2,n):
        candidate=sar+af*(ep-sar)
        if rising:
            candidate=min(candidate,l[i-1],l[i-2])
            if l[i]<candidate:
                rising=False;candidate=ep;ep=l[i];af=step
            elif h[i]>ep:ep=h[i];af=min(maximum,af+step)
        else:
            candidate=max(candidate,h[i-1],h[i-2])
            if h[i]>candidate:
                rising=True;candidate=ep;ep=h[i];af=step
            elif l[i]<ep:ep=l[i];af=min(maximum,af+step)
        sar=candidate;out[i]=sar
    return pd.Series(out,index=d.index)
def supertrend(d,n=10,mult=3):
    mid=(d.High+d.Low)/2;band=mult*atr(d,n);upper=mid+band;lower=mid-band
    trend=np.full(len(d),np.nan);direction=np.ones(len(d))
    for i in range(1,len(d)):
        if pd.isna(upper.iloc[i]) or pd.isna(lower.iloc[i]):continue
        up=upper.iloc[i];lo=lower.iloc[i]
        if not pd.isna(upper.iloc[i-1]) and d.Close.iloc[i-1]<=upper.iloc[i-1]:up=min(up,upper.iloc[i-1])
        if not pd.isna(lower.iloc[i-1]) and d.Close.iloc[i-1]>=lower.iloc[i-1]:lo=max(lo,lower.iloc[i-1])
        upper.iloc[i]=up;lower.iloc[i]=lo
        direction[i]=1 if d.Close.iloc[i]>upper.iloc[i-1] else -1 if d.Close.iloc[i]<lower.iloc[i-1] else direction[i-1]
        trend[i]=lo if direction[i]==1 else up
    return pd.Series(trend,index=d.index)
def calc(d,name):
    c=d.Close.astype(float);h=d.High.astype(float);l=d.Low.astype(float);v=d.Volume.astype(float)
    typical=(h+l+c)/3
    change=c.diff()
    gain=change.clip(lower=0).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    loss=(-change.clip(upper=0)).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    rsi=100-100/(1+gain/loss.replace(0,np.nan))
    true_range=atr(d)
    if name=="MA 均線":return {"MA5":c.rolling(5).mean(),"MA10":c.rolling(10).mean(),"MA20":c.rolling(20).mean(),"MA60":c.rolling(60).mean(),"MA120":c.rolling(120).mean()}
    if name=="EMA 指數均線":return {"EMA12":ema(c,12),"EMA26":ema(c,26)}
    if name=="WMA 加權均線":
        w=np.arange(1,21)
        return {"WMA20":c.rolling(20).apply(lambda x:np.dot(x,w)/w.sum(),raw=True)}
    if name=="布林通道 BOLL":
        m=c.rolling(20).mean();sd=c.rolling(20).std()
        return {"上軌":m+2*sd,"中軌":m,"下軌":m-2*sd}
    if name=="一目均衡表 Ichimoku":
        mid=lambda n:(h.rolling(n).max()+l.rolling(n).min())/2
        ten=mid(9);kij=mid(26)
        return {"轉換線":ten,"基準線":kij,"先行A":((ten+kij)/2).shift(26),"先行B":mid(52).shift(26)}
    if name=="VWAP 成交量加權價":
        # Reset cumulative VWAP each trading day; daily historical bars => 1 bar/day, so use rolling 20-day VWAP.
        return {"20期VWAP":(typical*v).rolling(20).sum()/v.rolling(20).sum().replace(0,np.nan)}
    if name=="SAR 拋物線":return {"SAR":psar(d)}
    if name=="唐奇安通道 Donchian":return {"上軌":h.rolling(20).max(),"下軌":l.rolling(20).min()}
    if name=="肯特納通道 Keltner":
        m=ema(c,20);a=atr(d,10)
        return {"上軌":m+2*a,"中軌":m,"下軌":m-2*a}
    if name=="超級趨勢 Supertrend":return {"Supertrend":supertrend(d)}
    if name=="MACD":
        dif=ema(c,12)-ema(c,26);sig=ema(dif,9)
        return {"DIF":dif,"訊號線":sig,"柱狀體":dif-sig}
    if name=="RSI":return {"RSI14":rsi}
    if name=="KD 隨機指標":
        low=l.rolling(9).min();high=h.rolling(9).max()
        k=(100*(c-low)/(high-low).replace(0,np.nan)).ewm(alpha=1/3,adjust=False).mean()
        return {"K":k,"D":k.ewm(alpha=1/3,adjust=False).mean()}
    if name=="Stoch RSI":
        low=rsi.rolling(14).min();high=rsi.rolling(14).max()
        k=(100*(rsi-low)/(high-low).replace(0,np.nan)).rolling(3).mean()
        return {"K":k,"D":k.rolling(3).mean()}
    if name=="CCI":
        dev=typical.rolling(20).apply(lambda x:np.mean(np.abs(x-np.mean(x))),raw=True)
        return {"CCI20":(typical-typical.rolling(20).mean())/(.015*dev.replace(0,np.nan))}
    if name=="DMI / ADX":
        up=h.diff();down=-l.diff()
        plus=pd.Series(np.where((up>down)&(up>0),up,0),index=d.index)
        minus=pd.Series(np.where((down>up)&(down>0),down,0),index=d.index)
        smooth=lambda s:s.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
        di_plus=100*smooth(plus)/true_range.replace(0,np.nan)
        di_minus=100*smooth(minus)/true_range.replace(0,np.nan)
        dx=100*(di_plus-di_minus).abs()/(di_plus+di_minus).replace(0,np.nan)
        return {"+DI":di_plus,"-DI":di_minus,"ADX":smooth(dx)}
    if name=="ATR":return {"ATR14":true_range}
    if name=="ROC":return {"ROC12":c.pct_change(12)*100}
    if name=="MOM 動能":return {"MOM10":c-c.shift(10)}
    if name=="Williams %R":return {"%R14":-100*(h.rolling(14).max()-c)/(h.rolling(14).max()-l.rolling(14).min()).replace(0,np.nan)}
    if name=="MFI 資金流量":
        money=typical*v
        pos=money.where(typical>typical.shift(),0).rolling(14).sum()
        neg=money.where(typical<typical.shift(),0).rolling(14).sum()
        return {"MFI14":100-100/(1+pos/neg.replace(0,np.nan))}
    if name=="OBV":return {"OBV":(np.sign(c.diff()).fillna(0)*v).cumsum()}
    if name=="ADL 累積派發":
        m=((c-l)-(h-c))/(h-l).replace(0,np.nan)
        return {"ADL":(m.fillna(0)*v).cumsum()}
    if name=="CMF":
        m=((c-l)-(h-c))/(h-l).replace(0,np.nan)
        return {"CMF20":(m.fillna(0)*v).rolling(20).sum()/v.rolling(20).sum().replace(0,np.nan)}
    if name=="成交量 Volume":return {"成交量":v}
    if name=="成交量均線 VMA":return {"VMA5":v.rolling(5).mean(),"VMA20":v.rolling(20).mean()}
    if name=="TRIX":
        e=ema(ema(ema(c,15),15),15)
        return {"TRIX":e.pct_change()*100}
    if name=="PPO":
        fast=ema(c,12);slow=ema(c,26);ppo=100*(fast-slow)/slow.replace(0,np.nan)
        return {"PPO":ppo,"訊號線":ema(ppo,9)}
    if name=="PVO":
        fast=ema(v,12);slow=ema(v,26);pvo=100*(fast-slow)/slow.replace(0,np.nan)
        return {"PVO":pvo,"訊號線":ema(pvo,9)}
    if name=="Aroon":
        period=25
        up=h.rolling(period+1).apply(lambda x:100*(period-(period-np.argmax(x)))/period,raw=True)
        down=l.rolling(period+1).apply(lambda x:100*(period-(period-np.argmin(x)))/period,raw=True)
        return {"Aroon Up":up,"Aroon Down":down}
    if name=="Ultimate Oscillator":
        prev=c.shift()
        bp=c-pd.concat([l,prev],axis=1).min(axis=1)
        tr=pd.concat([h,prev],axis=1).max(axis=1)-pd.concat([l,prev],axis=1).min(axis=1)
        av=lambda n:bp.rolling(n).sum()/tr.rolling(n).sum().replace(0,np.nan)
        return {"UO":100*(4*av(7)+2*av(14)+av(28))/7}
    raise ValueError("Unknown indicator")

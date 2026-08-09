#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,subprocess,urllib.parse
from pathlib import Path

COORDS={
'gwanggyo-brothers':(37.3227,127.0340),'gwanggyo-sirubong':(37.3449,127.0225),'baragwanggyo':(37.3636,127.0035),'chilbo-ridge':(37.2577,126.9396),'surisan-loop':(37.3675,126.9027),'cheonggye-maebong':(37.4278,127.0435),'gwanak-sadang':(37.4450,126.9640),'samseong-hoam':(37.4347,126.9282),'namhansanseong':(37.4782,127.1810),'bulgok-yeongjang':(37.3699,127.1467),'seokseong-halmi':(37.2746,127.1777),'wangsong-obong':(37.3162,126.9496)}
FIELDS=['temperature_2m','apparent_temperature','precipitation_probability','precipitation','weather_code','wind_speed_10m','wind_gusts_10m','relative_humidity_2m']

def risk(row):
    code=int(row.get('weatherCode') or 0);pop=float(row.get('precipitationProbabilityPct') or 0);gust=float(row.get('gustKph') or 0);feel=float(row.get('apparentTempC') or 0)
    flags=[];level=0
    if code>=95: flags.append('뇌우');level=max(level,3)
    if pop>=70: flags.append('강수 가능성 높음');level=max(level,2)
    elif pop>=40: flags.append('비 가능성');level=max(level,1)
    if gust>=55: flags.append('강풍');level=max(level,3)
    elif gust>=40: flags.append('돌풍');level=max(level,1)
    if feel>=35: flags.append('체감 폭염');level=max(level,2)
    elif feel>=31: flags.append('더위');level=max(level,1)
    return {'levelCode':level,'level':['양호','주의','경계','위험'][level],'flags':flags or ['예보상 큰 위험요소 없음']}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--file',default='suwon-trail/weekly.json');args=ap.parse_args();path=Path(args.file);root=json.loads(path.read_text(encoding='utf-8'));routes=root.get('recommendations') or []
    ordered=[r for r in routes if r.get('id') in COORDS]
    if not ordered:return
    lats=','.join(str(COORDS[r['id']][0]) for r in ordered);lons=','.join(str(COORDS[r['id']][1]) for r in ordered)
    params={'latitude':lats,'longitude':lons,'hourly':','.join(FIELDS),'timezone':'Asia/Seoul','forecast_days':'16'}
    url='https://api.open-meteo.com/v1/forecast?'+urllib.parse.urlencode(params,safe=',')
    raw=subprocess.check_output(['curl','--fail','--silent','--show-error','--location','--retry','4','--retry-all-errors','--connect-timeout','15','--max-time','90',url],text=True)
    data=json.loads(raw);blocks=data if isinstance(data,list) else [data]
    weekend={root.get('weekend',{}).get('saturday'),root.get('weekend',{}).get('sunday')}
    for route,block in zip(ordered,blocks):
        h=block.get('hourly') or {};times=h.get('time') or [];rows=[]
        for i,t in enumerate(times):
            day=str(t)[:10];hour=int(str(t)[11:13] or 0)
            if day not in weekend or hour<5 or hour>20:continue
            def val(k):
                a=h.get(k) or [];return a[i] if i<len(a) else None
            row={'time':t,'tempC':val('temperature_2m'),'apparentTempC':val('apparent_temperature'),'precipitationProbabilityPct':val('precipitation_probability'),'precipitationMm':val('precipitation'),'weatherCode':val('weather_code'),'windKph':val('wind_speed_10m'),'gustKph':val('wind_gusts_10m'),'humidityPct':val('relative_humidity_2m')}
            row['risk']=risk(row);rows.append(row)
        route['hourly']=rows
    root['schemaVersion']=max(3,int(root.get('schemaVersion') or 1));root['hourlyNote']='주말 05~20시 시간대별 예보. 개인 예상 이동시간과의 결합은 앱 기기 내부에서 계산합니다.'
    path.write_text(json.dumps(root,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()

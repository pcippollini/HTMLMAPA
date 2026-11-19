#!/usr/bin/env python3
"""Rota geográfica determinística para testes, NÃO otimização pela malha viária."""
import argparse,hashlib,json,math,pathlib,datetime

def distance(a,b):
 lat1,lon1=a;lat2,lon2=b
 p1,p2=math.radians(lat1),math.radians(lat2)
 dp=p2-p1;dl=math.radians(lon2-lon1)
 h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
 return 6371*2*math.asin(min(1,math.sqrt(h)))
def key(p):
 v=''.join(c for c in str(p.get('CNPJ','')) if c.isdigit())
 return v.zfill(14) if v and len(v)<=14 else ''
def solve(features):
 by={};invalid=[]
 for f in features:
  props=f.get('properties') or {};c=key(props);g=f.get('geometry') or {}
  coords=g.get('coordinates') or []
  if g.get('type')!='Point' or len(coords)<2 or not c:invalid.append(c or 'SEM_CNPJ');continue
  lon,lat=map(float,coords[:2]);
  if not(-90<=lat<=90 and -180<=lon<=180):invalid.append(c);continue
  if c in by:invalid.append('DUPLICADO_'+c);continue
  by[c]=(lat,lon,props)
 if not by:raise ValueError('Nenhum ponto válido no GeoJSON')
 keys=sorted(by);start=min(keys,key=lambda k:(-by[k][0],by[k][1],k));route=[start];unused=set(keys);unused.remove(start)
 while unused:
  here=route[-1];nearest=min(unused,key=lambda k:(distance(by[here][:2],by[k][:2]),k));route.append(nearest);unused.remove(nearest)
 # 2-opt first improvement; start point stays fixed
 for _ in range(15):
  improvement=False
  for i in range(1,len(route)-1):
   for j in range(i+1,len(route)):
    a=route[i-1];b=route[i];c=route[j]
    old=distance(by[a][:2],by[b][:2]);new=distance(by[a][:2],by[c][:2])
    if j<len(route)-1:
     d=route[j+1];old+=distance(by[c][:2],by[d][:2]);new+=distance(by[b][:2],by[d][:2])
    if new+1e-8<old:
     route[i:j+1]=reversed(route[i:j+1]);improvement=True
  if not improvement:break
 return route,by,invalid

def main():
 parser=argparse.ArgumentParser();parser.add_argument('source');parser.add_argument('destination');args=parser.parse_args()
 path=pathlib.Path(args.source);raw=path.read_bytes();obj=json.loads(raw)
 if obj.get('type')!='FeatureCollection':raise ValueError('Esperado FeatureCollection')
 route,by,invalid=solve(obj.get('features') or [])
 km=sum(distance(by[a][:2],by[b][:2]) for a,b in zip(route,route[1:]))
 result={'route_version':'PRIORIDADES_V2_TESTE','method':'geographic_nearest_neighbor_2opt_NOT_ROAD_NETWORK','source_geojson':path.name,'source_sha256':hashlib.sha256(raw).hexdigest(),'source_version':hashlib.sha256(raw).hexdigest()[:16],'keys':route,'km_direct':round(km,2),'invalid_or_duplicate':invalid}
 output=pathlib.Path(args.destination);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Pontos:',len(route),'Distância geográfica (km):',round(km,2),'Ignorados:',len(invalid),'Saída:',output)
if __name__=='__main__':main()

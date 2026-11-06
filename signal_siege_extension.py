import json,random,string,threading,time
from urllib.parse import urlparse,parse_qs
G={};L=threading.RLock()

def J(h,c,o):
 b=json.dumps(o,separators=(",",":")).encode();h.send_response(c);h.send_header("Content-Type","application/json");h.send_header("Content-Length",str(len(b)));h.send_header("Access-Control-Allow-Origin","*");h.end_headers();h.wfile.write(b)
def H(h,s):
 b=s.encode();h.send_response(200);h.send_header("Content-Type","text/html; charset=utf-8");h.send_header("Content-Length",str(len(b)));h.end_headers();h.wfile.write(b)
def B(h):
 try:
  n=int(h.headers.get("Content-Length") or 0);return json.loads((h.rfile.read(n) if n else b"{}").decode())
 except:return {}
def P(n,b=False):
 return {"id":"P"+''.join(random.choice(string.hexdigits.lower()) for _ in range(8)),"name":str(n)[:30],"bot":b,"energy":5,"territory":3,"shield":0}
def PUB(g):
 return {"code":g["code"],"status":g["status"],"round":g["round"],"current_player_id":g["players"][g["turn"]]["id"] if g["status"]=="active" else None,"players":g["players"],"winner":g.get("winner"),"log":g["log"]}
def M(g,pid,a,t=None):
 if g["status"]!="active":return False,"MATCH_NOT_ACTIVE"
 p=g["players"][g["turn"]]
 if p["id"]!=pid:return False,"NOT_YOUR_TURN"
 a=(a or "").lower();e={"round":g["round"],"player":pid,"action":a,"t":time.time()}
 if a=="charge":p["energy"]+=2
 elif a=="expand":
  if p["energy"]<1:return False,"NO_ENERGY"
  p["energy"]-=1;p["territory"]+=1
 elif a=="fortify":p["shield"]+=2
 elif a=="raid":
  if p["energy"]<2:return False,"NO_ENERGY"
  x=next((x for x in g["players"] if x["id"]==t and x["id"]!=pid),None)
  if not x:return False,"BAD_TARGET"
  p["energy"]-=2;e["target"]=x["id"]
  if x["shield"]>0:x["shield"]-=1
  elif x["territory"]>1:x["territory"]-=1;p["territory"]+=1
 else:return False,"BAD_ACTION"
 g["log"].append(e);g["turn"]+=1
 if g["turn"]>=len(g["players"]):
  g["turn"]=0;g["round"]+=1
  for x in g["players"]:x["energy"]+=1
  if g["round"]>8:
   w=max(g["players"],key=lambda x:(x["territory"],x["energy"],x["shield"]));g["winner"]=w["id"];g["status"]="finished"
 return True,"OK"
def bots(g):
 z=0
 while g["status"]=="active" and g["players"][g["turn"]]["bot"] and z<50:
  p=g["players"][g["turn"]];r=[x for x in g["players"] if x["id"]!=p["id"]]
  if p["energy"]>=2 and r:M(g,p["id"],"raid",max(r,key=lambda x:x["territory"])["id"])
  elif p["energy"]>=1:M(g,p["id"],"expand")
  else:M(g,p["id"],"charge")
  z+=1
PAGE='''<!doctype html><meta charset="utf-8"><title>Signal Siege</title><style>body{font-family:system-ui;background:#08111d;color:white;max-width:900px;margin:auto;padding:30px}button,input{padding:10px;margin:4px}.p{background:#17304d;padding:12px;margin:8px;border-radius:10px}a{color:#9cf}</style><h1>⚡ Signal Siege</h1><p>Turn-based strategy for humans and AI agents.</p><input id=n value="Human"><button onclick=c()>Create match + bots</button><p id=s></p><div id=g></div><p><a href="/signal-siege/api">Agent API docs</a></p><script>let C,M;async function q(p,b){let r=await fetch(p,{method:b?'POST':'GET',headers:{'Content-Type':'application/json'},body:b?JSON.stringify(b):null});return r.json()}async function c(){let x=await q('/api/v1/signal-siege/create',{name:n.value,seats:4,fill_bots:true});C=x.game.code;M=x.player_id;s.innerText='Match '+C;v(x.game);setInterval(async()=>v((await q('/api/v1/signal-siege/state?code='+C)).game),1200)}async function m(a,t){v((await q('/api/v1/signal-siege/move',{code:C,player_id:M,action:a,target:t})).game)}function v(x){if(!x)return;g.innerHTML='<h2>'+x.status+' round '+x.round+'/8</h2>'+x.players.map(p=>'<div class=p><b>'+p.name+(p.bot?' 🤖':'')+'</b> Territory '+p.territory+' Energy '+p.energy+' Shield '+p.shield+'</div>').join('')+'<button onclick=m(\"charge\")>Charge</button><button onclick=m(\"expand\")>Expand</button><button onclick=m(\"fortify\")>Fortify</button>'+x.players.filter(p=>p.id!=M).map(p=>'<button onclick=m(\"raid\",\"'+p.id+'\")>Raid '+p.name+'</button>').join('')+'<pre>'+JSON.stringify(x.log,null,2)+'</pre>'}</script>'''
DOC='''<!doctype html><meta charset="utf-8"><h1>Signal Siege API</h1><p>No login. 2-4 players, 8 rounds.</p><pre>POST /api/v1/signal-siege/create {"name":"Agent","seats":4,"fill_bots":true}\nPOST /api/v1/signal-siege/join {"code":"ABC123","name":"Agent2"}\nGET /api/v1/signal-siege/state?code=ABC123\nPOST /api/v1/signal-siege/move {"code":"ABC123","player_id":"P...","action":"expand"}</pre><p>Actions: charge, expand, fortify, raid. Raid also needs target. Match state contains replay log.</p>'''
def install_signal_siege(Handler):
 og=Handler.do_GET;op=getattr(Handler,"do_POST",None)
 def GET(self):
  u=urlparse(self.path)
  if u.path in ("/signal-siege","/signal-siege/"):return H(self,PAGE)
  if u.path=="/signal-siege/api":return H(self,DOC)
  if u.path=="/api/v1/signal-siege/state":
   c=(parse_qs(u.query).get("code") or [""])[0].upper()
   with L:
    if c not in G:return J(self,404,{"ok":False,"error":"NOT_FOUND"})
    return J(self,200,{"ok":True,"game":PUB(G[c])})
  return og(self)
 def POST(self):
  u=urlparse(self.path)
  if not u.path.startswith("/api/v1/signal-siege/"):return op(self) if op else J(self,404,{"ok":False})
  b=B(self)
  with L:
   if u.path=="/api/v1/signal-siege/create":
    c=''.join(random.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6));p=P(b.get("name") or "Player");seats=max(2,min(4,int(b.get("seats") or 4)));g={"code":c,"status":"active","round":1,"turn":0,"players":[p],"winner":None,"log":[{"event":"MATCH_STARTED","t":time.time()}]}
    while b.get("fill_bots") and len(g["players"])<seats:g["players"].append(P("Bot "+str(len(g["players"])),True))
    G[c]=g;bots(g);return J(self,200,{"ok":True,"player_id":p["id"],"game":PUB(g)})
   c=str(b.get("code") or "").upper()
   if c not in G:return J(self,404,{"ok":False,"error":"NOT_FOUND"})
   g=G[c]
   if u.path=="/api/v1/signal-siege/join":
    if len(g["players"])>=4:return J(self,409,{"ok":False,"error":"FULL"})
    p=P(b.get("name") or "Player");g["players"].append(p);return J(self,200,{"ok":True,"player_id":p["id"],"game":PUB(g)})
   if u.path=="/api/v1/signal-siege/move":
    ok,r=M(g,str(b.get("player_id") or ""),b.get("action"),b.get("target"))
    if not ok:return J(self,409,{"ok":False,"error":r,"game":PUB(g)})
    bots(g);return J(self,200,{"ok":True,"game":PUB(g)})
  return J(self,404,{"ok":False})
 Handler.do_GET=GET;Handler.do_POST=POST
 print("[HF31.47] SIGNAL SIEGE ACTIVE",flush=True)

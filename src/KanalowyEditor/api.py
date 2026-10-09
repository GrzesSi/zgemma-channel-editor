import base64
import ipaddress
import json
import secrets
import threading
import time
from urllib.parse import urlsplit
from .core import EditorError, unpack

class WebApp:
    def __init__(self, core, demo=False):
        self.core = core
        self.demo = demo
        self.lock = threading.RLock()
        self.sessions = {}

    def client_allowed(self, address):
        try:
            address = ipaddress.ip_address(address)
            if getattr(address,'ipv4_mapped',None): address=address.ipv4_mapped
            return address.is_loopback or any(address in ipaddress.ip_network(n) for n in
                (['10.0.0.0/8','172.16.0.0/12','192.168.0.0/16','169.254.0.0/16'] if address.version==4 else ['fc00::/7','fe80::/10']))
        except ValueError:
            return False

    def handle(self, method, rawpath, headers, body, client='127.0.0.1'):
        with self.lock:
            return self._handle(method,rawpath,headers,body,client)

    def _handle(self, method, rawpath, headers, body, client):
        path=urlsplit(rawpath).path
        headers={k.lower():v for k,v in headers.items()}
        response={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'}
        def result(status,value):
            if isinstance(value,dict) and 'catalog' in value: value['demo']=self.demo
            if isinstance(value,dict) and isinstance(value.get('state'),dict): value['state']['demo']=self.demo
            return status,response,json.dumps(value,ensure_ascii=False).encode('utf-8')
        if not self.client_allowed(client):
            return result(403,{'error':'Edytor jest dostępny tylko w sieci lokalnej.'})
        if len(body)>30*1024*1024:
            return result(413,{'error':'Plik jest za duży.'})
        if method not in ('GET','POST'):
            return result(405,{'error':'Nieobsługiwana operacja.'})
        payload={}
        if method=='POST':
            origin=headers.get('origin'); host=headers.get('host')
            if headers.get('x-kanaly-editor')!='1' or (origin and urlsplit(origin).netloc!=host):
                return result(403,{'error':'Żądanie musi pochodzić ze strony edytora.'})
            if not headers.get('content-type','').lower().startswith('application/json'):
                return result(415,{'error':'Nieprawidłowy format danych.'})
            try:
                payload=json.loads(body.decode('utf-8'))
                if not isinstance(payload,dict): raise ValueError()
            except (ValueError,UnicodeError):
                return result(400,{'error':'Nieprawidłowe dane.'})
        routes={'/api/state':'GET','/api/backups':'GET','/api/import':'POST','/api/save':'POST','/api/export':'POST','/api/restore':'POST'}
        if path not in routes:
            return result(404,{'error':'Nie znaleziono tej operacji.'})
        if method!=routes[path]:
            return result(405,{'error':'Nieobsługiwana operacja.'})
        # Browser identity isolates editing drafts; it never requires a login or code.
        now=time.time()
        self.sessions={s:v for s,v in self.sessions.items() if now-v<8*3600}
        cookie=headers.get('cookie',''); token=''
        for part in cookie.split(';'):
            if part.strip().startswith('ke_browser='): token=part.strip().split('=',1)[1]
        if token not in self.sessions:
            if len(self.sessions)>=256: self.sessions.pop(next(iter(self.sessions)))
            token=secrets.token_urlsafe(32)
            response['Set-Cookie']='ke_browser='+token+'; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800'
        self.sessions[token]=now
        try:
            if path=='/api/state' and method=='GET':
                return result(200,self.core.state(owner=token))
            if path=='/api/backups' and method=='GET':
                return result(200,{'backups':self.core.list_backups()})
            if path=='/api/import' and method=='POST':
                try:
                    data=base64.b64decode(payload.get('data',''),validate=True)
                except (ValueError,TypeError):
                    raise EditorError('Nieprawidłowy plik.')
                return result(200,self.core.state(unpack(data),owner=token))
            if path=='/api/save' and method=='POST':
                return result(200,self.core.save(payload.get('draft'),payload.get('groups'),owner=token))
            if path=='/api/export' and method=='POST':
                return result(200,self.core.export(payload.get('draft'),payload.get('groups'),owner=token))
            if path=='/api/restore' and method=='POST':
                return result(200,self.core.restore(payload.get('name'),owner=token))
            return result(404,{'error':'Nie znaleziono tej operacji.'})
        except EditorError as e:
            return result(400,{'error':str(e)})
        except Exception:
            return result(500,{'error':'Nie udało się wykonać operacji. Sprawdź dostępne miejsce i listę kanałów.'})

SECURITY_HEADERS={
 'X-Content-Type-Options':'nosniff',
 'X-Frame-Options':'DENY',
 'Referrer-Policy':'same-origin',
 'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
}
STATIC={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','application/javascript; charset=utf-8'),'/style.css':('style.css','text/css; charset=utf-8')}


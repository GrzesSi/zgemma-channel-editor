from pathlib import Path
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from .core import EditorCore
from .api import WebApp, SECURITY_HEADERS, STATIC

_listener=None
_application=None
_start_error=None

def _reload():
    from enigma import eDVBDB
    database=eDVBDB.getInstance()
    database.reloadServicelist()
    database.reloadBouquets()
    try:
        from Screens.InfoBar import InfoBar
        if InfoBar.instance is not None:
            servicelist=InfoBar.instance.servicelist
            current=servicelist.getCurrentSelection()
            root=servicelist.getRoot()
            servicelist.setRoot(root)
            if current is not None: servicelist.setCurrentSelection(current)
    except Exception:
        pass

def sessionstart(reason,session=None,**kwargs):
    global _listener,_application,_start_error
    if reason!=0 or session is None or _listener is not None:
        return
    try:
        from twisted.internet import reactor
        from twisted.web.resource import Resource
        from twisted.web.server import Site
        _application=WebApp(EditorCore('/etc/enigma2',reload_callback=_reload))
        application=_application
        web=Path(__file__).parent/'web'
        class EditorResource(Resource):
            isLeaf=True
            def render(self,request):
                path=request.uri.decode('utf-8',errors='replace')
                method=request.method.decode('ascii')
                client=request.getClientAddress().host
                decode=lambda x: x.decode('latin1') if isinstance(x,bytes) else x
                headers={decode(k):decode(v[0]) for k,v in request.requestHeaders.getAllRawHeaders()}
                if not application.client_allowed(client):
                    status,extra,body=403,{'Content-Type':'text/plain; charset=utf-8'},b'Siec lokalna wymagana.'
                elif path.split('?',1)[0] in STATIC and method=='GET':
                    filename,mime=STATIC[path.split('?',1)[0]]
                    status,extra,body=200,{'Content-Type':mime,'Cache-Control':'no-cache'},(web/filename).read_bytes()
                else:
                    body=request.content.read(30*1024*1024+1)
                    status,extra,body=application.handle(method,path,headers,body,client)
                request.setResponseCode(status)
                for k,v in dict(SECURITY_HEADERS,**extra).items():
                    request.setHeader(k.encode('ascii'),v.encode('utf-8'))
                return body
        _listener=reactor.listenTCP(8877,Site(EditorResource()),interface='0.0.0.0')
    except Exception as e:
        _start_error=str(e)
        print('[KanalowyEditor] Startup failed:',type(e).__name__)

def show_info(session,**kwargs):
    if _application is None or _listener is None:
        session.open(MessageBox,'Edytor nie wystartował. Zrestartuj interfejs i sprawdź, czy OpenWebif jest zainstalowany.\n'+(_start_error or ''),MessageBox.TYPE_ERROR)
        return
    address='ADRES_IP_DEKODERA'
    try:
        from Components.Network import iNetwork
        for adapter in iNetwork.getAdapterList():
            if iNetwork.getAdapterAttribute(adapter,'up'):
                ip=iNetwork.getAdapterAttribute(adapter,'ip')
                if ip: address='.'.join(str(x) for x in ip); break
    except Exception:
        pass
    session.open(MessageBox,'Otwórz na komputerze lub telefonie:\nhttp://'+address+':8877\n\nStrona otwiera się od razu w sieci lokalnej.\nZmiany są zapisywane dopiero przyciskiem Zapisz na dekoderze.',MessageBox.TYPE_INFO,timeout=0)

def Plugins(**kwargs):
    return [PluginDescriptor(name='Edytor kanałów',description='Ręczne układanie listy przez przeglądarkę',where=PluginDescriptor.WHERE_SESSIONSTART,fnc=sessionstart,needsRestart=True),
            PluginDescriptor(name='Edytor kanałów',description='Adres strony edytora kanałów',where=PluginDescriptor.WHERE_PLUGINMENU,fnc=show_info)]


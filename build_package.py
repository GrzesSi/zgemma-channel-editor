from pathlib import Path
import hashlib,io,json,tarfile,zipfile,py_compile,subprocess
ROOT=Path(__file__).resolve().parent; SRC=ROOT/'src'/'KanalowyEditor'; DIST=ROOT/'dist'; DIST.mkdir(exist_ok=True)
readme=(ROOT/'INSTALACJA.txt').read_text(encoding='utf-8')
for p in SRC.glob('*.py'): py_compile.compile(str(p),doraise=True)
files=[p for p in SRC.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']
archive=DIST/'Edytor_Kanalow_Zgemma_1.0.2.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for p in files: z.write(p,'KanalowyEditor/'+p.relative_to(SRC).as_posix())
 z.writestr('INSTALACJA.txt',readme.encode('utf-8'))
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 assert 'KanalowyEditor/plugin.py' in z.namelist()
 assert all('__pycache__' not in n and '/tests/' not in n for n in z.namelist())

def tar_data(entries,directories=()):
 output=io.BytesIO()
 with tarfile.open(fileobj=output,mode='w:gz',format=tarfile.GNU_FORMAT) as tf:
  for name in sorted(directories,key=lambda n:(n.count('/'),n)):
   info=tarfile.TarInfo(name);info.type=tarfile.DIRTYPE;info.mode=0o755;info.uid=info.gid=0;info.uname=info.gname='root';tf.addfile(info)
  for name,data in entries.items():
   info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;info.uid=info.gid=0;info.uname=info.gname='root';tf.addfile(info,io.BytesIO(data))
 return output.getvalue()
base='usr/lib/enigma2/python/Plugins/Extensions/KanalowyEditor/'
datafiles={base+p.relative_to(SRC).as_posix():p.read_bytes() for p in files}
directories=set()
for n in datafiles:
 p=Path(n)
 for parent in p.parents:
  if str(parent)!='.': directories.add(parent.as_posix())
control='Package: enigma2-plugin-extensions-kanalowyeditor\nVersion: 1.0.2\nArchitecture: all\nMaintainer: Local project\nSection: extra\nPriority: optional\nDepends: enigma2, enigma2-plugin-extensions-openwebif\nDescription: Polish browser channel editor with backup and full channel preservation\n'
members={'debian-binary':b'2.0\n','control.tar.gz':tar_data({'control':control.encode()}),'data.tar.gz':tar_data(datafiles,directories)}
out=io.BytesIO();out.write(b'!<arch>\n')
for name,data in members.items():
 header=((name+'/').ljust(16)+'0'.ljust(12)+'0'.ljust(6)+'0'.ljust(6)+'100644'.ljust(8)+str(len(data)).ljust(10)+'`\n').encode('ascii')
 assert len(header)==60;out.write(header);out.write(data)
 if len(data)%2:out.write(b'\n')
ipk=DIST/'enigma2-plugin-extensions-kanalowyeditor_1.0.2_all.ipk';ipk.write_bytes(out.getvalue())
# Independently decode the resulting ar package and compare every deployed file.
raw=ipk.read_bytes();assert raw[:8]==b'!<arch>\n';i=8;decoded={}
while i<len(raw):
 h=raw[i:i+60];assert h[-2:]==b'`\n';n=h[:16].decode().strip().rstrip('/');size=int(h[48:58]);i+=60;decoded[n]=raw[i:i+size];i+=size+(size%2)
assert decoded['debian-binary']==b'2.0\n'
with tarfile.open(fileobj=io.BytesIO(decoded['data.tar.gz']),mode='r:gz') as tf:
 extracted={m.name:tf.extractfile(m).read() for m in tf if m.isfile()}
 assert extracted==datafiles
report={'version':'1.0.2','runtime':'OpenATV 8 / Python 3 / Twisted from OpenWebif','receiver_port':8877,'receiver_install_performed':False,'hardware_test_performed':False,'access':'local_network_no_login','package_files':len(files),'packages':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (archive,ipk)}}
for p in (archive,ipk):
 (DIST/(p.name+'.sha256')).write_text(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n',encoding='ascii')
(ROOT/'wersja_i_paczki.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))

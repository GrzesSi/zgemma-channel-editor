"""Channel editor core. No receiver imports; original databases remain byte-identical on edits."""
import base64
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import tarfile
import time
from .channel_types import channel_genre

MAX_BYTES = 20 * 1024 * 1024
ALLOWED = re.compile(r"^(?:lamedb5?|bouquets\.(?:tv|radio)|userbouquet\.[A-Za-z0-9_.()+-]+\.(?:tv|radio))$")
ROOTS = re.compile(rb'FROM BOUQUET "([^"]+)"')
STREAM_TYPES = {'4097', '5001', '5002', '8193'}

class EditorError(Exception):
    pass

def text(data):
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        return data.decode('cp1250', errors='replace')

def key(ref):
    p = ref.split(':')
    try:
        if p[:2] == ['1', '0'] and len(p) >= 7:
            return tuple(int(p[i], 16) for i in (3, 6, 4, 5))
    except ValueError:
        pass
    return None

def is_channel(ref):
    return key(ref) is not None or ref.split(':')[0] in STREAM_TYPES

def pieces(data):
    header, items, current = [], [], None
    for line in data.splitlines():
        if line.startswith(b'#SERVICE '):
            if current is not None:
                items.append(current)
            current = [line]
        elif current is None:
            header.append(line)
        else:
            current.append(line)
    if current is not None:
        items.append(current)
    return header, items

def database(data):
    lines = data.splitlines()
    if not lines or b'/4/' not in lines[0]:
        raise EditorError('Import wymaga bazy lamedb w formacie 4, razem z listą grup.')
    try:
        i = lines.index(b'transponders') + 1
        transponders = {}
        while lines[i] != b'end':
            ident = lines[i]
            i += 1
            params = []
            while lines[i] != b'/':
                params.append(lines[i]); i += 1
            tuple(int(x, 16) for x in ident.split(b':'))
            transponders[ident] = params
            i += 1
        i = lines.index(b'services') + 1
        services = {}
        while lines[i] != b'end':
            ident, name, provider = lines[i:i+3]
            fields = ident.split(b':')
            tuple(int(x, 16) for x in fields[:4])
            int(fields[4])
            if len(fields) < 7:
                ident += b':0' * (7 - len(fields))
            services[ident] = (name, provider)
            i += 3
        return transponders, services
    except (ValueError, IndexError):
        raise EditorError('Uszkodzona baza kanałów lamedb.')

def serialize_databases(transponders, services):
    v4 = [b'eDVB services /4/', b'transponders']
    v5 = [b'eDVB services /5/']
    for ident, params in sorted(transponders.items()):
        v4.extend([ident] + params + [b'/'])
        if len(params) != 1:
            raise EditorError('Nieobsługiwany zapis transpondera.')
        mode, body = params[0].strip().split(b' ', 1)
        fields, options = body.split(b':'), []
        if mode == b's' and len(fields) > 11:
            if len(fields) >= 14:
                options.append(b'MIS/PLS:' + b':'.join(fields[11:14]))
            if len(fields) >= 16:
                options.append(b'T2MI:' + b':'.join(fields[14:16]))
            body = b':'.join(fields[:11])
        line = b't:' + ident + b',' + mode + b':' + body
        if options:
            line += b',' + b','.join(options)
        v5.append(line)
    v4 += [b'end', b'services']
    for ident, (name, provider) in sorted(services.items()):
        v4 += [ident, name, provider]
        v5.append(b's:' + ident + b',"' + name + b'",' + provider)
    v4 += [b'end', b'Have a lot of bugs!']
    v5.append(('# done. %d channels and %d services' % (len(transponders), len(services))).encode())
    return {'lamedb': b'\n'.join(v4) + b'\n', 'lamedb5': b'\n'.join(v5) + b'\n'}

def fingerprint(files):
    h = hashlib.sha256()
    for name, data in sorted(files.items()):
        h.update(name.encode()); h.update(b'\0'); h.update(data); h.update(b'\0')
    return h.hexdigest()

def pack(files):
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode='w:gz', format=tarfile.GNU_FORMAT) as tf:
        for name, data in sorted(files.items()):
            if not ALLOWED.fullmatch(name):
                raise EditorError('Nieprawidłowa nazwa pliku kanałów.')
            info = tarfile.TarInfo('etc/enigma2/' + name)
            info.size = len(data); info.mode = 0o644; info.uid = info.gid = 0
            info.uname = info.gname = 'root'; info.mtime = 0
            tf.addfile(info, io.BytesIO(data))
    return out.getvalue()

def unpack(data):
    if len(data) > MAX_BYTES:
        raise EditorError('Paczka listy jest za duża (maksymalnie 20 MB).')
    files, total = {}, 0
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:*') as tf:
            for number, member in enumerate(tf):
                if number > 5000:
                    raise EditorError('Za dużo plików w paczce.')
                p = PurePosixPath(member.name)
                if p.is_absolute() or '..' in p.parts or '\\' in member.name:
                    raise EditorError('Paczka zawiera niebezpieczną ścieżkę.')
                if member.isdir():
                    continue
                if not member.isfile():
                    raise EditorError('Paczka listy nie może zawierać dowiązań.')
                total += member.size
                if member.size < 0 or total > MAX_BYTES:
                    raise EditorError('Rozpakowana lista jest za duża.')
                if not ALLOWED.fullmatch(p.name):
                    continue
                if len(p.parts) > 1 and tuple(p.parts[-3:-1]) != ('etc', 'enigma2'):
                    continue
                if p.name in files:
                    raise EditorError('Paczka zawiera powtórzone pliki.')
                files[p.name] = tf.extractfile(member).read()
    except (tarfile.TarError, EOFError, OSError):
        raise EditorError('Nie udało się otworzyć paczki. Użyj pliku .tar.gz z listą kanałów.')
    if not all(n in files for n in ('lamedb', 'bouquets.tv', 'bouquets.radio')):
        raise EditorError('Paczka musi zawierać lamedb, bouquets.tv i bouquets.radio.')
    if 'lamedb5' not in files:
        t, s = database(files['lamedb'])
        files['lamedb5'] = serialize_databases(t, s)['lamedb5']
    model(files)  # Validate references before any write.
    return files

def model(files):
    transponders, services = database(files['lamedb'])
    names = {}
    dbkeys = set()
    for ident, (name, provider) in services.items():
        k = tuple(int(x, 16) for x in ident.split(b':')[:4])
        names[k] = text(name); dbkeys.add(k)
    tpkeys = {tuple(int(x, 16) for x in ident.split(b':')) for ident in transponders}
    groups, catalog, private = [], {}, {}
    for kind in ('tv', 'radio'):
        seen_files = set()
        for rawname in ROOTS.findall(files['bouquets.' + kind]):
            filename = rawname.decode('ascii')
            if not ALLOWED.fullmatch(filename) or filename not in files:
                raise EditorError('Brak pliku grupy: ' + filename)
            if filename in seen_files:
                continue
            seen_files.add(filename)
            header, items = pieces(files[filename])
            title = text(header[0][6:]) if header and header[0].startswith(b'#NAME ') else filename
            ids = []
            for block in items:
                ref = text(block[0][9:]).strip()
                if 'FROM BOUQUET' in ref:
                    raise EditorError('Ta lista ma zagnieżdżone grupy; edytor ich jeszcze nie obsługuje.')
                channel = is_channel(ref)
                k = key(ref)
                if k is not None and (k not in dbkeys or (k[1], k[2], k[3]) not in tpkeys):
                    raise EditorError('Brak parametrów kanału w bazie: ' + names.get(k, 'nieznany'))
                description = next((text(line[13:]) for line in block if line.startswith(b'#DESCRIPTION ')), '')
                label = description or names.get(k) or ('Kanał internetowy' if channel else 'Separator')
                if not description and k is None and channel:
                    label = ref.rsplit(':', 1)[-1] or 'Kanał internetowy'
                placeholder = channel and not any(c.isalnum() for c in label)
                if placeholder: label = 'Kanał bez nazwy · ' + (format(k[0], 'X') if k else 'IPTV')
                identity = kind + '\0' + ref
                if not channel:
                    identity += '\0' + text(b'\n'.join(block))
                uid = hashlib.sha256(identity.encode('utf-8')).hexdigest()[:24]
                catalog.setdefault(uid, {'id': uid, 'name': label, 'placeholder': placeholder, 'kind': kind, 'type': 'channel' if channel else 'marker', 'ref': ref, 'genre': channel_genre(label, kind, placeholder) if channel else ''})
                private.setdefault(uid, block)
                ids.append(uid)
            groups.append({'id': filename, 'name': title, 'kind': kind, 'items': ids})
    return {'groups': groups, 'catalog': catalog}, private

class EditorCore:
    def __init__(self, directory, backup_directory=None, reload_callback=None):
        self.directory = Path(directory)
        self.backups = Path(backup_directory or (self.directory / 'kanaly_editor_kopie'))
        self.reload = reload_callback or (lambda: None)
        self.drafts = {}

    def snapshot(self):
        files = {}
        for name in ('lamedb', 'lamedb5', 'bouquets.tv', 'bouquets.radio'):
            p = self.directory / name
            if p.exists():
                files[name] = p.read_bytes()
        if not all(n in files for n in ('lamedb', 'bouquets.tv', 'bouquets.radio')):
            raise EditorError('Nie znaleziono pełnej listy w /etc/enigma2.')
        for kind in ('tv', 'radio'):
            for name in ROOTS.findall(files['bouquets.' + kind]):
                filename = name.decode('ascii')
                if not ALLOWED.fullmatch(filename):
                    raise EditorError('Nieprawidłowa nazwa grupy.')
                p = self.directory / filename
                if not p.is_file():
                    raise EditorError('Brakuje grupy: ' + filename)
                files[filename] = p.read_bytes()
        return files

    def state(self, imported=None, owner='local'):
        live = self.snapshot()
        files = live
        extra = {}
        if imported is not None:
            files = dict(imported)
            if files['lamedb'] != live['lamedb']:
                oldt, olds = database(live['lamedb']); newt, news = database(files['lamedb'])
                oldt.update(newt); olds.update(news)
                files.update(serialize_databases(oldt, olds))
            live_model, live_private = model(live)
            extra = (live_model['catalog'], live_private)
        state, private = model(files)
        if extra:
            previous_catalog, previous_private = extra
            for uid, item in previous_catalog.items():
                if item['type'] == 'channel' and uid not in state['catalog']:
                    state['catalog'][uid] = item; private[uid] = previous_private[uid]
        # Drafts expire and belong to the browser login that created them.
        now = time.time()
        self.drafts = {k:v for k,v in self.drafts.items() if now - v['time'] < 8*3600}
        if len(self.drafts) >= 64:
            self.drafts.pop(next(iter(self.drafts)))
        token = secrets.token_urlsafe(24)
        self.drafts[token] = {'files': files, 'model': state, 'private': private, 'revision': fingerprint(live), 'owner': owner, 'time': now}
        return dict(state, draft=token, source='import' if imported is not None else 'decoder', revision=fingerprint(live))

    def generate(self, token, groups, owner='local'):
        draft = self.drafts.get(token)
        if draft is None or draft['owner'] != owner or time.time() - draft['time'] > 8*3600:
            raise EditorError('Sesja edycji wygasła. Wczytaj listę ponownie.')
        if not isinstance(groups, list) or not 1 <= len(groups) <= 500:
            raise EditorError('Lista musi mieć co najmniej jedną grupę.')
        files = {n:b for n,b in draft['files'].items() if n in ('lamedb', 'lamedb5')}
        catalog, private = draft['model']['catalog'], draft['private']
        roots = {'tv': [], 'radio': []}; placed = set(); seen_names = set(); clean = []
        for g in groups:
            kind, title, filename, ids = g.get('kind'), g.get('name'), g.get('id'), g.get('items')
            if kind not in roots or not isinstance(title, str) or not title.strip() or len(title)>200 or '\n' in title or '\r' in title or '\0' in title:
                raise EditorError('Nieprawidłowa nazwa lub rodzaj grupy.')
            if not isinstance(filename, str) or not ALLOWED.fullmatch(filename) or not filename.startswith('userbouquet.') or not filename.endswith('.'+kind) or filename in seen_names:
                raise EditorError('Nieprawidłowy plik grupy.')
            if not isinstance(ids, list) or len(ids)>20000:
                raise EditorError('Za dużo kanałów w grupie.')
            seen_names.add(filename); entries=[]
            for uid in ids:
                if uid not in catalog or catalog[uid]['kind'] != kind:
                    raise EditorError('Kanał nie należy do tej listy lub rodzaju grupy.')
                entries.extend(private[uid])
                if catalog[uid]['type'] == 'channel':
                    placed.add(uid)
            files[filename] = b'\n'.join([('#NAME '+title.strip()).encode('utf-8')]+entries)+b'\n'
            roots[kind].append(filename); clean.append(dict(g))
        # Removing a group or an entry never silently deletes a channel.
        unassigned = {kind:[uid for uid,v in catalog.items() if v['type']=='channel' and v['kind']==kind and uid not in placed] for kind in roots}
        for kind, ids in unassigned.items():
            if not ids:
                continue
            filename = 'userbouquet.ke_pozostale.' + kind
            while filename in seen_names:
                filename = filename.replace('ke_', 'ke_x', 1)
            seen_names.add(filename); entries=[]
            for uid in ids: entries.extend(private[uid])
            files[filename] = b'\n'.join(['#NAME Pozostałe kanały'.encode('utf-8')]+entries)+b'\n'; roots[kind].append(filename)
            clean.append({'id':filename,'name':'Pozostałe kanały','kind':kind,'items':ids})
        for kind, names in roots.items():
            lines=[('#NAME Bouquets '+kind.upper()).encode()]
            for filename in names:
                lines.append(('#SERVICE 1:7:'+('2' if kind=='radio' else '1')+':0:0:0:0:0:0:0:FROM BOUQUET "'+filename+'" ORDER BY bouquet').encode())
            files['bouquets.'+kind] = b'\n'.join(lines)+b'\n'
        result, unused = model(files)
        channels={uid for uid,v in catalog.items() if v['type']=='channel'}
        assert channels <= set(result['catalog']), 'Channel preservation failed'
        return files, draft, sum(len(x) for x in unassigned.values())

    def _write(self, files):
        for name, data in files.items():
            if not ALLOWED.fullmatch(name): raise EditorError('Nieprawidłowy plik.')
            target=self.directory/name
            tmp=self.directory/('.ke_'+secrets.token_hex(8)+'.tmp')
            try:
                with tmp.open('wb') as f:
                    f.write(data); f.flush(); os.fsync(f.fileno())
                os.chmod(str(tmp),0o644); os.replace(str(tmp),str(target))
            finally:
                if tmp.exists(): tmp.unlink()

    def _backup(self, files):
        self.backups.mkdir(parents=True, exist_ok=True)
        name=time.strftime('kanaly_%Y%m%d_%H%M%S_')+secrets.token_hex(3)+'.tar.gz'
        p=self.backups/name
        with p.open('wb') as f:
            f.write(pack(files)); f.flush(); os.fsync(f.fileno())
        os.chmod(str(p),0o600)
        return name

    def _apply(self, files, original):
        backup=self._backup(original)
        existing={name:(self.directory/name).read_bytes() if (self.directory/name).exists() else None for name in files}
        try:
            self._write(files); self.reload()
        except Exception:
            try:
                self._write({n:b for n,b in existing.items() if b is not None})
                for name,b in existing.items():
                    if b is None and (self.directory/name).exists(): (self.directory/name).unlink()
                self.reload()
            except Exception:
                raise EditorError('Zapis nie powiódł się. Przywróć kopię '+backup+' z folderu kanaly_editor_kopie.')
            raise EditorError('Zapis nie powiódł się. Przywrócono poprzednią listę.')
        return backup

    def save(self, token, groups, owner='local'):
        files,draft,unassigned=self.generate(token,groups,owner)
        live=self.snapshot()
        if fingerprint(live)!=draft['revision']:
            raise EditorError('Lista w dekoderze zmieniła się od wczytania. Wczytaj ją ponownie, aby nie nadpisać cudzych zmian.')
        backup=self._apply(files,live)
        self.drafts.clear()
        return {'backup':backup,'unassigned':unassigned,'state':self.state(owner=owner)}

    def export(self, token, groups, owner='local'):
        files,draft,unassigned=self.generate(token,groups,owner)
        return {'filename':'moja_lista_kanalow.tar.gz','data':base64.b64encode(pack(files)).decode('ascii'),'unassigned':unassigned}

    def list_backups(self):
        return sorted((p.name for p in self.backups.glob('kanaly_*.tar.gz') if p.is_file()), reverse=True)[:30]

    def restore(self, name, owner='local'):
        if name not in self.list_backups(): raise EditorError('Nie znaleziono kopii.')
        files=unpack((self.backups/name).read_bytes()); backup=self._apply(files,self.snapshot()); self.drafts.clear()
        return {'backup':backup,'state':self.state(owner=owner)}



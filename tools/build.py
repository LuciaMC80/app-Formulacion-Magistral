"""Construye el dietario de consulta (HTML) a partir del volcado del cuaderno OneNote.

Uso:
    python tools/build.py                 # genera index.html (app instalable)
    python tools/build.py --artifact X    # genera la versión sin <head> para publicar como Artifact
"""
import argparse, json, os, re, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

ap = argparse.ArgumentParser()
ap.add_argument('--src', default=os.path.join(HERE, 'onenote-export.json'))
ap.add_argument('--images', default=os.path.join(HERE, 'imagenes.json'),
                help='fórmulas transcritas a mano de las imágenes del cuaderno')
ap.add_argument('--template', default=os.path.join(HERE, 'template.html'))
ap.add_argument('--out', default=os.path.join(ROOT, 'index.html'))
ap.add_argument('--data-out', default=os.path.join(HERE, 'data.json'))
ap.add_argument('--artifact', metavar='OUT', help='escribe solo el fragmento para Artifact en OUT')
args = ap.parse_args()

dump = json.load(open(args.src, encoding='utf-8'))
image_blocks = {}
if os.path.exists(args.images):
    for e in json.load(open(args.images, encoding='utf-8')):
        image_blocks.setdefault((e['sec'], e['page']), []).extend(e['blocks'])

DATE_RE = re.compile(r'^(lunes|martes|miércoles|jueves|viernes|sábado|domingo),? \d{1,2} de \w+ de \d{4}', re.I)
TIME_RE = re.compile(r'^\d{1,2}:\d{2}$')

def strip_acc(t):
    return ''.join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')

DOSE_RE = re.compile(r'\d[\d.,]*\s*(%|mg|g\b|ml|mL|μg|µg|mcg|UI|gotas?)', re.I)
USE_RE = re.compile(r'^(modo de (aplicaci[oó]n|empleo|uso)|posolog[ií]a|aplicaci[oó]n|aplicar|se aplica|tomar|\d+\s*v\s*/|\d+\s*/\s*\d+\s*h)', re.I)

def is_head(l):
    letters_ = re.sub(r'[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ]', '', l)
    if len(letters_) < 4 or len(l) > 70:
        return False
    up = sum(1 for c in letters_ if c.isupper())
    return up / len(letters_) > 0.85 and not DOSE_RE.search(l)

def split_formulas(paras):
    """Corta en párrafos vacíos; un trozo que no empieza por un componente con dosis
    o por un encabezado se une al anterior (modo de aplicación, notas)."""
    chunks, cur = [], []
    for p in paras + ['']:
        if p:
            cur.append(p)
        elif cur:
            chunks.append(cur)
            cur = []
    out = []
    pending_head = None
    for c in chunks:
        if pending_head:
            c = pending_head + c
            pending_head = None
        starts_new = bool(DOSE_RE.search(c[0])) or is_head(c[0])
        if len(c) == 1 and is_head(c[0]):
            pending_head = c
            continue
        if out and not starts_new:
            out[-1].extend(c)
        else:
            out.append(c)
    if pending_head:
        if out:
            out[-1].extend(pending_head)
        else:
            out.append(pending_head)
    return out

# páginas con el mismo nombre en una sección: se fusionan, no se sustituyen
pages = {}
for d in dump:
    key = (d['sec'], d['page'])
    if key not in pages or not pages[key]['ok']:
        pages[key] = dict(d, outlines=list(d['outlines']))
    elif d['ok']:
        pages[key]['outlines'] += d['outlines']

letters = []
order = []
for d in dump:
    if d['sec'] not in order:
        order.append(d['sec'])

stats = {'pages': 0, 'blocks': 0, 'notok': []}
for sec in order:
    items = []
    for (s_, name), d in pages.items():
        if s_ != sec:
            continue
        title = re.sub(r'\s+', ' ', name).strip()
        blocks = []
        outl = sorted(d['outlines'], key=lambda o: (round(o['x'] / 200), o['y']))
        for o in outl:
            paras = o['p'] if 'p' in o else [l.strip() for l in o['t'].split('\n')]
            # saltos de línea internos perdidos: "50 mgPara una cáp" -> dos líneas
            paras = [x for p in paras for x in re.split(r'(?<=[a-z0-9%.])(?=(?:Para|Exc|Modo de|Posolog)\b)', p)]
            body = [p for p in paras if p]
            if not body:
                continue
            if ' '.join(body).upper() == title.upper():
                continue
            if DATE_RE.match(body[0]):
                paras = [p for p in paras[1:] if not TIME_RE.match(p)]
                if not any(paras):
                    continue
            for chunk in split_formulas(paras):
                blocks.append(chunk)
        blocks += image_blocks.get((s_, name), [])
        if title.lower() == 'página sin título' and not blocks:
            continue
        if blocks and blocks[0][0].upper() == title.upper():
            blocks[0] = blocks[0][1:] or blocks[0]
        if not blocks:
            stats.setdefault('empty', []).append(f'{sec}/{title}')
        stats['pages'] += 1
        stats['blocks'] += len(blocks)
        items.append({'name': title, 'blocks': blocks})
    items.sort(key=lambda i: strip_acc(i['name']).upper())
    letters.append({'letter': sec, 'items': items})

data = {'letters': letters}
js = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
html = open(args.template, encoding='utf-8').read().replace('/*__DATA__*/null', js)
html = html.replace('__NPAT__', str(stats['pages'])).replace('__NFORM__', str(stats['blocks']))

HEAD = '''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0d6655">
<meta name="description" content="Fórmulas magistrales dermatológicas ordenadas por letra y patología, con buscador por principio activo.">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icons/icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="icons/icon-192.png">
<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>
'''
SW = '''<script>
if ('serviceWorker' in navigator && location.protocol.startsWith('http')) {
  navigator.serviceWorker.register('sw.js').catch(() => {});
}
</script>
'''

if args.artifact:
    open(args.artifact, 'w', encoding='utf-8').write(html)
else:
    # el <title> y los <link>/<style> de la plantilla quedan dentro del <head>; el resto va al <body>
    cut = html.index('<header')
    page = HEAD + html[:cut] + '</head>\n<body>\n' + html[cut:] + SW + '</body>\n</html>\n'
    open(args.out, 'w', encoding='utf-8').write(page)
json.dump(data, open(args.data_out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(stats, ensure_ascii=False))

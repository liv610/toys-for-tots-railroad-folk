"""Build the 'enter Toy Town' page: a copy of the map viewer (usmap/viewer_tt) where clicking Toy Town zooms in and
dissolves into the painted 3D village. The live viewer, the map, the routes and the engine are not touched.

  enter/out/                 the copied viewer, with enter.js and enter.css added to its page
  enter/out/toytown/         the 3D village (../painted), its textures packed into a few script bundles (WebP),
                             and the map's own tree and cloud sprites taken from the viewer's sprites/ folder

    python3 build_enter.py          (needs usmap/viewer_tt from to_viewer.py, and painted/tex from the paint scripts)
"""
import os, sys, json, shutil, base64, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..', '..', '..')
SRC = os.path.join(ROOT, 'usmap', 'viewer_tt'); OUT = os.path.join(HERE, 'out')
SCENE = (sys.argv[1:] or ['folk'])[0]                       # 'folk': the painted scene in depth; 'painted': the 3D village
P3 = os.path.join(HERE, '..', SCENE)
VIEWS = {'folk': [('square', 'Into the square'), ('tree', 'The tree and toys'), ('toyshop', 'The toy shop'), ('donation', 'Toy donation'), ('station', 'Up to the station')],
         'painted': [('square', 'In the square'), ('toyshop', 'By the toy shop'), ('entrance', 'Station entrance'), ('south', 'Over the wall'), ('overview', 'From above')]}
S = 2.747; OX, OY = 1293 - 195 * S, 1173 - 285 * S; DET0 = (2560, 1024)      # Toy Town painting px -> map px (to_viewer.py)
t2m = lambda x, y: [(OX + x * S) / 2 + DET0[0], (OY + y * S) / 2 + DET0[1]]
CORE = [(186, 262), (362, 108), (560, 8), (840, 8), (1038, 108), (1214, 262), (1220, 392), (1296, 472), (1302, 860), (1399, 826),
        (1399, 966), (1280, 1004), (1000, 1034), (560, 1044), (260, 1014), (10, 936), (0, 700), (22, 628), (92, 556), (186, 522)]
BUNDLE_MAX = 11_000_000

def main():
    shutil.rmtree(OUT, ignore_errors=True); shutil.copytree(SRC, OUT)
    # the station's painted face on the map (the map's Toy Town painting is in the kit's units)
    f = json.load(open(os.path.join(HERE, '..', 'painted', 'tex', 'assets.json')))['station_face']
    cfg = dict(town=[t2m(*p) for p in CORE], town_box=t2m(0, -40) + t2m(1399, 1124),
               face=t2m(f['x0'], f['y0']) + t2m(f['x0'] + f['w'], f['y0'] + f['h']), views=VIEWS[SCENE])
    # the map page: add the entry code
    p = os.path.join(OUT, 'index.html'); html = open(p).read()
    html = html.replace('<title>Toy Town Preview</title>', '<title>Step into Toy Town</title>')
    html = html.replace('<h1>Toy Town preview</h1>', '<h1>Step into Toy Town</h1>')
    html = html.replace('</style>', open(os.path.join(HERE, 'enter.css')).read() + '\n</style>', 1)
    tail = '<script>window.TT_ENTER = ' + json.dumps(cfg) + ';</script>\n<script src="toytown/campaigns.js"></script>\n<script>\n' + open(os.path.join(HERE, 'enter.js')).read() + '\n</script>\n'
    i = html.rfind('</body>'); html = html[:i] + tail + html[i:] if i >= 0 else html + tail
    open(p, 'w').write(html)
    # the 3D village, textures packed into bundles
    d = os.path.join(OUT, 'toytown'); os.makedirs(d)
    for n in ('diorama.js', 'landscape.js', 'folk.js', 'campaigns.js', 'ticket.js'):
        if os.path.exists(os.path.join(P3, n)): shutil.copy(os.path.join(P3, n), d)
    if os.path.exists(os.path.join(P3, 'layout.js')): shutil.copy(os.path.realpath(os.path.join(P3, 'layout.js')), os.path.join(d, 'layout.js'))
    tex = os.path.join(P3, 'tex'); entries = {}
    for n in sorted(os.listdir(tex)):
        fp = os.path.join(tex, n)
        if os.path.isdir(fp) or n == 'station.png': continue
        if n.endswith('.json'): entries[n] = json.load(open(fp)); continue
        if n.endswith('.png'):
            im = cv2.imread(fp, cv2.IMREAD_UNCHANGED); ok, buf = cv2.imencode('.webp', im, [cv2.IMWRITE_WEBP_QUALITY, 92]); mime = 'image/webp'
        else:
            buf = open(fp, 'rb').read(); mime = 'image/jpeg'
        entries[n] = 'data:' + mime + ';base64,' + base64.b64encode(bytes(buf)).decode()
    if os.path.isdir(os.path.join(tex, 'map')):
        for n in os.listdir(os.path.join(tex, 'map')): entries['map/' + n] = '../sprites/' + n     # the map's own sprites
    bundles, cur, size = [], {}, 0
    for k, v in entries.items():
        s = len(json.dumps(v))
        if cur and size + s > BUNDLE_MAX: bundles.append(cur); cur, size = {}, 0
        cur[k] = v; size += s
    bundles.append(cur)
    tags = []
    for i, b in enumerate(bundles):
        open(os.path.join(d, f'tex_bundle_{i}.js'), 'w').write('window.TT_BUNDLE = Object.assign(window.TT_BUNDLE || {}, ' + json.dumps(b) + ');\n')
        tags.append(f'<script src="tex_bundle_{i}.js"></script>')
    page = open(os.path.join(P3, 'index.html')).read()
    if '<section class="card"' in page:
        a, b = page.index('<section class="card"'), page.index('</section>') + len('</section>')
        page = page[:a] + '\n'.join(tags) + page[b:]
    else: page = page.replace('<body>', '<body>\n' + '\n'.join(tags), 1)
    page = page.replace("document.querySelectorAll('[data-view]').forEach(b => b.onclick = () => window.__setView(b.dataset.view));\n", '')
    page = page.replace("  document.getElementById('walk').onclick = () => { window.__setView('square'); window.__glide('square', 'entrance', 5); };\n", '')
    open(os.path.join(d, 'index.html'), 'w').write(page)
    n_files = sum(len(fs) for _, _, fs in os.walk(OUT)); mb = sum(os.path.getsize(os.path.join(r, x)) for r, _, fs in os.walk(OUT) for x in fs) / 1e6
    print(f'built {OUT}: {n_files} files, {mb:.1f} MB; {len(bundles)} texture bundles ' + ', '.join(f"{os.path.getsize(os.path.join(d, f'tex_bundle_{i}.js')) / 1e6:.1f}" for i in range(len(bundles))) + ' MB')

if __name__ == '__main__':
    main()

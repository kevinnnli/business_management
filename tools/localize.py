import json, sys, os, shutil
from PIL import Image
content, mapfile, imgdir, outdir = sys.argv[1:5]
d = json.load(open(content)); m = json.load(open(mapfile))
os.makedirs(outdir, exist_ok=True)
miss = 0
for key, p in d.items():
    for sec in p['sections']:
        for col in sec['cols']:
            for b in col:
                field = 'src' if b['type'] == 'image' else ('img' if b['type'] == 'linkcard' else None)
                if not field or not b.get(field): continue
                name = m.get(b[field])
                if not name: miss += 1; print('MISSING', key, b[field][:80]); continue
                src = os.path.join(imgdir, name); dst = os.path.join(outdir, name)
                im = Image.open(src)
                if im.width > 1400:
                    im.thumbnail((1400, 10000))
                if name.endswith('.jpg'):
                    im.convert('RGB').save(dst, quality=82, optimize=True, progressive=True)
                elif name.endswith('.png'):
                    im.save(dst, optimize=True)
                else:
                    shutil.copy(src, dst)
                b[field] = 'assets/img/' + name
                if field == 'src': b['w'], b['h'] = im.width, im.height
json.dump(d, open(content, 'w'), indent=1)
print('missing', miss)

import subprocess, time, os, json, sys, re
from bs4 import BeautifulSoup
base = sys.argv[1]; pages_file = sys.argv[2]
raw = os.path.join(base, 'raw'); imgd = os.path.join(base, 'img')
mapping = {}
mp = os.path.join(base, 'map.json')
if os.path.exists(mp): mapping = json.load(open(mp))
slugs = ['home'] + [l.strip()[len('/view/mrmo-businessmanagement/'):] for l in open(pages_file) if l.strip()]
def curl(url, out):
    r = subprocess.run(['curl', '-sSL', '--max-time', '40', '-o', out, '-w', '%{http_code} %{content_type}', url], capture_output=True, text=True)
    return r.stdout
for slug in slugs:
    key = slug.replace('/', '_')
    url = 'https://sites.google.com/view/mrmo-businessmanagement' + ('' if slug == 'home' else '/' + slug)
    rp = os.path.join(raw, key + '.html')
    for attempt in range(3):
        st = curl(url, rp)
        if st.startswith('200'): break
        time.sleep(5)
    soup = BeautifulSoup(open(rp).read(), 'html.parser')
    imgs = [i['src'] for i in soup.find_all('img', class_='CENy8b')] + [i['src'] for i in soup.select('div.zGRpZc img')]
    n = 0
    for u in imgs:
        if u in mapping: continue
        n += 1
        tmp = os.path.join(imgd, 'tmp')
        ok = False
        for attempt in range(3):
            st = curl(u, tmp)
            if st.startswith('200') and 'image' in st:
                ok = True; break
            time.sleep(3)
        if ok:
            ext = {'image/png': '.png', 'image/jpeg': '.jpg', 'image/gif': '.gif', 'image/webp': '.webp'}.get(st.split(' ', 1)[1].split(';')[0], '.img')
            name = f"{key}-{len([v for v in mapping.values() if v.startswith(key + '-')]) + 1:02d}{ext}"
            os.replace(tmp, os.path.join(imgd, name))
            mapping[u] = name
        else:
            print('FAIL', key, st, flush=True)
        time.sleep(0.5)
    json.dump(mapping, open(mp, 'w'), indent=1)
    print(key, len(imgs), 'imgs', flush=True)
print('DONE', len(mapping))

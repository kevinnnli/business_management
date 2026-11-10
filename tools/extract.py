import warnings
from bs4 import MarkupResemblesLocatorWarning
warnings.filterwarnings('ignore', category=MarkupResemblesLocatorWarning)
import re, json, sys, glob, os, html as H
from urllib.parse import urlparse, parse_qs, unquote
from bs4 import BeautifulSoup, NavigableString, Tag

RAW = sys.argv[1]; OUT = sys.argv[2]
SITE = '/view/mrmo-businessmanagement'

def unwrap(u):
    if not u: return u
    if u.startswith('https://www.google.com/url'):
        q = parse_qs(urlparse(u).query).get('q')
        if q: u = q[0]
    if u.startswith(SITE) or u.startswith('https://sites.google.com'+SITE):
        p = u.split(SITE,1)[1].split('?')[0].split('#')[0].strip('/')
        return 'page:' + (p or 'home')
    return u

def inline(node):
    out=[]
    for c in node.children:
        if isinstance(c, NavigableString):
            out.append(H.escape(str(c)))
        elif isinstance(c, Tag):
            if c.name == 'br': out.append('<br>'); continue
            inner = inline(c)
            st = c.get('style','')
            if c.name == 'a' and c.get('href'):
                inner = f'<a href="{H.escape(unwrap(c["href"]),quote=True)}">{inner}</a>'
            elif c.name in ('strong','b') or 'font-weight: 700' in st or 'font-weight: 600' in st:
                if inner.strip(): inner = f'<strong>{inner}</strong>'
            if c.name in ('em','i') or 'font-style: italic' in st:
                if inner.strip(): inner = f'<em>{inner}</em>'
            if 'text-decoration: underline' in st and c.name!='a' and inner.strip():
                inner = f'<u>{inner}</u>'
            out.append(inner)
    s=''.join(out)
    s=s.replace('</strong><strong>','').replace('</em><em>','')
    return s

def textblocks(tile):
    blocks=[]
    for el in tile.find_all(['h1','h2','h3','h4','h5','h6','p','ul','ol','small'], recursive=True):
        if el.find_parent(['ul','ol','li']) and el.name in ('p','ul','ol','small'):
            continue  # handled within list
        if el.name in ('ul','ol'):
            items=[]
            for li in el.find_all('li', recursive=False):
                parts=[]
                for ch in li.children:
                    if isinstance(ch,Tag) and ch.name in ('ul','ol'):
                        sub=[inline(x).strip() for x in ch.find_all('li',recursive=False)]
                        parts.append({'sub':sub, 'ordered': ch.name=='ol'})
                    elif isinstance(ch,Tag):
                        parts.append(inline(ch))
                    else: parts.append(H.escape(str(ch)))
                txt=''.join(p for p in parts if isinstance(p,str)).strip()
                subs=[p for p in parts if isinstance(p,dict)]
                items.append({'html':txt, 'sub': subs[0] if subs else None})
            blocks.append({'type':'list','ordered':el.name=='ol','items':items})
        else:
            h=inline(el).strip()
            plain=BeautifulSoup(h,'html.parser').get_text().strip()
            if not plain: continue
            t = el.name if el.name.startswith('h') else 'p'
            if el.name=='small': t='small'
            blocks.append({'type':t,'html':h,'text':plain})
    return blocks

def tile_blocks(tile):
    emb = tile.find(attrs={'data-embed-open-url':True})
    if emb:
        ifr = emb.find('iframe')
        label = (ifr.get('aria-label') if ifr else '') or ''
        kind, _, title = label.partition(', ')
        return [{'type':'embed','kind':kind or 'File','title':title or label,
                 'open':emb['data-embed-open-url'],
                 'src': (ifr.get('data-src') or ifr.get('src')) if ifr else None,
                 'thumb': emb.get('data-embed-thumbnail-url')}]
    card = tile.find('div', class_='zGRpZc')
    if card:
        a=card.find('a'); im=card.find('img'); sp=card.find_all('span',class_='nWW5Nb')
        return [{'type':'linkcard','href':unwrap(a.get('href')) if a else None,'img':im['src'] if im else None,
                 'title':sp[0].get_text(' ',strip=True) if sp else '', 'desc':sp[1].get_text(' ',strip=True) if len(sp)>1 else ''}]
    du = tile.find(attrs={'data-url':True,'aria-label':'Whole page embed'})
    if du:
        return [{'type':'urlembed','href':du['data-url']}]
    ifr = tile.find('iframe')
    if ifr:
        src = ifr.get('src') or ifr.get('data-src') or ''
        m = re.search(r'youtube\.com/embed/([\w-]+)', src)
        if m:
            lab=ifr.get('aria-label','')
            return [{'type':'video','id':m.group(1),'title': lab.partition(', ')[2] or 'YouTube video'}]
        return [{'type':'iframe','src':src,'title':ifr.get('aria-label','Embedded content')}]
    img = tile.find('img', class_='CENy8b')
    if img:
        a = img.find_parent('a')
        return [{'type':'image','src':img['src'],'alt':img.get('alt') or img.get('aria-label') or '',
                 'href': unwrap(a['href']) if a and a.get('href') else None}]
    btn = tile.find('a', class_='FKF6mc')
    if btn:
        return [{'type':'button','text':btn.get_text(' ',strip=True),'href':unwrap(btn.get('href'))}]
    tb = textblocks(tile)
    if not tb:
        t = tile.get_text(' ',strip=True)
        if t: return [{'type':'unknown','text':t[:200],'cls':tile.get('class')}]
    return tb

pages={}
for f in sorted(glob.glob(RAW+'/*.html')):
    slug=os.path.basename(f)[:-5].replace('__','/').replace('_','/') if False else os.path.basename(f)[:-5]
    soup=BeautifulSoup(open(f).read(),'html.parser')
    for s in soup(['script','style']): s.decompose()
    for s in soup.select('div.PPhIP'): s.decompose()
    title = soup.find('title').get_text()
    secs=[]
    first=True
    for sec in soup.find_all('section'):
        if sec.find_parent('footer') or sec.find_parent('header'): continue
        bg=None
        bgd=sec.find('div',class_='IFuOkc')
        if bgd and 'background-image' in bgd.get('style',''):
            m=re.search(r'url\(([^)]+)\)',bgd['style']); bg=m.group(1) if m else None
        cols=[]
        for col in sec.select('div.JNdkSc'):
            if col.find_parent('div',class_='JNdkSc'): continue
            items=[]
            for tile in col.find_all('div',class_='tyJCtd'):
                items+=tile_blocks(tile)
            if items: cols.append(items)
        if cols or bg: secs.append({'bg':bg,'cols':cols})
    pages[slug]={'title':title,'sections':secs}
json.dump(pages,open(OUT,'w'),indent=1)
print(len(pages))

#!/usr/bin/env python3
"""Build the static site from tools/content.json.

Usage:  python3 tools/build.py

content.json is produced by tools/extract.py from the original Google Site.
Every page is written to <slug>/index.html (home -> index.html) and all links
are relative, so the site works on GitHub Pages, any static host, or opened
straight from disk.
"""
import html
import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "tools", "content.json")
ORIGINAL = "https://sites.google.com/view/mrmo-businessmanagement"
SITE_NAME = "Mr. Mo · IBDP Business Management"

# ---------------------------------------------------------------- navigation
# Order and grouping follow the original site's menu.
NAV = [
    ("home", "Home", None),
    ("introduction", "Introduction", None),
    ("bm-start-point", "BM Start Point", None),
    ("unit-1-intro-to-business-management", "Unit 1 · Introduction to Business Management", [
        ("1-1-intro-to-business-management", "1.1 Introduction to Business Management"),
        ("1-2-types-of-business", "1.2 Types of Business"),
        ("1-3-business-objectives", "1.3 Business Objectives"),
        ("1-4-different-stakeholders", "1.4 Stakeholders"),
        ("1-5-growth-and-evolution", "1.5 Growth and Evolution"),
        ("1-6-mncs", "1.6 Multinational Companies (MNCs)"),
    ]),
    ("unit-2-hrm", "Unit 2 · Human Resource Management", [
        ("2-1-intro-to-hrm", "2.1 Introduction to HRM"),
        ("2-2-organisational-structure", "2.2 Organisational Structure"),
        ("2-3-leadership-and-management", "2.3 Leadership and Management"),
        ("2-4-motivation", "2.4 Motivation"),
        ("2-5-hl-only-organisational-corporate-culture", "2.5 Organisational (Corporate) Culture|HL"),
        ("2-6-communication", "2.6 Communication"),
        ("2-7hl-only-industrial-employee-relations", "2.7 Industrial / Employee Relations|HL"),
    ]),
    ("unit-3-finance-and-accounts", "Unit 3 · Finance and Accounts", [
        ("unit-3-1-intro-to-finance", "3.1 Introduction to Finance"),
        ("unit-3-2-sources-of-finance", "3.2 Sources of Finance"),
        ("unit-3-3-costs-and-revenues", "3.3 Costs and Revenues"),
        ("unit-3-4-final-accounts", "3.4 Final Accounts"),
        ("unit-3-5-profitability-and-liquidity-ratio-analysis", "3.5 Profitability and Liquidity Ratio Analysis"),
        ("unit-3-6-debt-equity-ratio-analysis-hl", "3.6 Debt/Equity Ratio Analysis|HL"),
        ("unit-3-7-cash-flow", "3.7 Cash Flow"),
        ("unit-3-8-investment-appraisal", "3.8 Investment Appraisal"),
        ("unit-3-9-budgets-hl-only", "3.9 Budgets|HL"),
    ]),
    ("unit-4-marketing", "Unit 4 · Marketing", [
        ("4-1-marketing", "4.1 Introduction to Marketing"),
        ("4-2-marketing-palnning", "4.2 Marketing Planning"),
        ("4-3-hl-sales-forecasting", "4.3 Sales Forecasting|HL"),
        ("4-4-market-research", "4.4 Market Research"),
        ("4-5-the-7ps-of-marketing-mix", "4.5 The 7 Ps of the Marketing Mix"),
        ("4-6-hl-international-marketing", "4.6 International Marketing|HL"),
    ]),
    ("unit-5-operations-management", "Unit 5 · Operations Management", [
        ("5-1-intro", "5.1 Introduction to Operations Management"),
        ("5-2-production-methods", "5.2 Production Methods"),
        ("5-3-hl-only-lean-production", "5.3 Lean Production and Quality Management|HL"),
        ("5-4-location", "5.4 Location"),
        ("5-5-break-even-analysis", "5.5 Break-even Analysis"),
        ("5-6-hl-only-production-planning-hl-only", "5.6 Production Planning|HL"),
        ("5-7-hl-only-crisis-management-and-contingency-planning", "5.7 Crisis Management and Contingency Planning|HL"),
        ("5-8-hl-only-rd", "5.8 Research and Development|HL"),
        ("5-9-hl-only-management-information-systems", "5.9 Management Information Systems|HL"),
    ]),
    ("bm-toolkit", "BM Toolkit", [
        ("business-plan", "Business Plan"),
        ("swot-analysis", "SWOT Analysis"),
        ("ansoff-matrix", "Ansoff Matrix"),
        ("porters-generic-strategies", "Porter's Generic Strategies|HL"),
        ("bcg-matrix", "BCG Matrix"),
        ("steeple", "STEEPLE"),
        ("simple-linear-regression", "Simple Linear Regression|HL"),
        ("cpa", "Critical Path Analysis (CPA)"),
        ("decision-tree", "Decision Tree"),
        ("descriptive-statistics", "Descriptive Statistics"),
    ]),
    ("grading-criteria", "Grading Criteria", None),
    ("oxford-practise-question-answers", "Oxford Practice Question Answers", None),
    ("ia", "Internal Assessment (IA)", None),
    ("assessment-ib-paper-1-2-and-3", "Assessment · IB Papers 1, 2 and 3", None),
    ("exam-tracker", "Exam Tracker", None),
]

# Pages kept only as redirects (the original home and "who is Mr. Mo" are the same page).
REDIRECTS = {"who-is-mr-mo": "home"}

UNIT_BLURB = {
    "unit-1-intro-to-business-management": "What businesses are, how they are organised, what they aim for and who they answer to.",
    "unit-2-hrm": "How organisations plan, structure, lead, motivate and communicate with their people.",
    "unit-3-finance-and-accounts": "Where money comes from, how it is recorded, and how to judge a business's financial health.",
    "unit-4-marketing": "Understanding customers and markets, and planning the marketing mix.",
    "unit-5-operations-management": "How goods and services are produced, located, planned and improved.",
    "bm-toolkit": "The analytical tools the IB expects you to apply across the course.",
}


def build_index():
    """Flatten NAV into an ordered list of page records."""
    pages = []
    for slug, label, children in NAV:
        top_label, top_hl = split_label(label)
        pages.append({"slug": slug, "label": top_label, "hl": top_hl, "parent": None,
                      "children": [f"{slug}/{c}" for c, _ in (children or [])]})
        for cslug, clabel in children or []:
            lab, hl = split_label(clabel)
            pages.append({"slug": f"{slug}/{cslug}", "label": lab, "hl": hl, "parent": slug, "children": []})
    return pages


def split_label(label):
    if label.endswith("|HL"):
        return label[:-3], True
    return label, False


# ------------------------------------------------------------------ helpers
def esc(s):
    return html.escape(s or "", quote=True)


def out_path(slug):
    return os.path.join(ROOT, "index.html") if slug == "home" else os.path.join(ROOT, slug, "index.html")


def rel(from_slug, to_slug, anchor=""):
    """Relative URL from one page to another (explicit index.html so it also works from disk)."""
    depth = 0 if from_slug == "home" else from_slug.count("/") + 1
    prefix = "../" * depth
    target = "index.html" if to_slug == "home" else f"{to_slug}/index.html"
    return prefix + target + anchor


def asset(from_slug, path):
    depth = 0 if from_slug == "home" else from_slug.count("/") + 1
    return "../" * depth + path


def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:60] or "section"


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).replace("\xa0", " ").strip()


def fully_wrapped(h):
    """True when the whole paragraph is emphasised (bold/underline), i.e. it reads as a label."""
    inner = re.sub(r"</?(strong|u|em)>", "", h).strip()
    outer = re.sub(r"<(strong|u|em)>.*?</\1>", "", h, flags=re.S)
    return bool(inner) and not strip_tags(outer).strip()


PLACEHOLDER = re.compile(r"\[Link\]|Caption for an image of your class|Tell your students more about yourself|"
                         r"Help students and parents to help themselves")


# --------------------------------------------------------------- rendering
class Renderer:
    def __init__(self, slug, pages_by_slug):
        self.slug = slug
        self.pages = pages_by_slug
        self.toc = []
        self.ids = set()
        self.figure_no = 0

    def link(self, href):
        if href and href.startswith("page:"):
            target = href[5:]
            target, _, anchor = target.partition("#")
            target = REDIRECTS.get(target, target)
            if target in self.pages:
                return rel(self.slug, target), False
            return f"{ORIGINAL}/{target}", True
        return href, bool(href and re.match(r"https?://", href))

    def fix_inline(self, h):
        def sub(m):
            url, external = self.link(html.unescape(m.group(1)))
            attrs = f' href="{esc(url)}"'
            if external:
                attrs += ' target="_blank" rel="noopener"'
            return f"<a{attrs}>"
        h = re.sub(r'<a href="([^"]*)">', sub, h)
        h = re.sub(r"<u>(.*?)</u>", r"\1", h, flags=re.S) if "<a" in h else h
        h = h.replace("\xa0", " ")
        return h

    def unique_id(self, text):
        base = slugify(text)
        i, cand = 2, base
        while cand in self.ids:
            cand = f"{base}-{i}"
            i += 1
        self.ids.add(cand)
        return cand

    def heading(self, level, text):
        hid = self.unique_id(text)
        if level == 2:
            self.toc.append((hid, text))
        return f'<h{level} id="{hid}">{esc(text)}</h{level}>'

    def block(self, b, context_label):
        t = b["type"]
        if t in ("h1", "h2", "h3", "h4", "h5", "h6"):
            text = strip_tags(b["html"])
            if len(text) > 140:  # long "headings" in the original are really paragraphs
                return f"<p>{self.fix_inline(b['html'])}</p>"
            level = {"h1": 2, "h2": 3, "h3": 3}.get(t, 4)
            return self.heading(level, text)
        if t in ("p", "small"):
            h = b["html"]
            text = strip_tags(h)
            if PLACEHOLDER.search(text):
                return ""
            if fully_wrapped(h) and len(text) <= 90 and "<a" not in h and "<br>" not in h:
                return self.heading(3, text.rstrip(" -:"))
            if fully_wrapped(h) and len(text) > 90:
                h = re.sub(r"</?(strong|u)>", "", h)
            cls = ' class="note"' if t == "small" else ""
            return f"<p{cls}>{self.fix_inline(h)}</p>"
        if t == "list":
            if all(PLACEHOLDER.search(strip_tags(i["html"])) for i in b["items"]):
                return ""
            tag = "ol" if b["ordered"] else "ul"
            items = []
            for it in b["items"]:
                inner = self.fix_inline(it["html"])
                if it.get("sub"):
                    st = "ol" if it["sub"]["ordered"] else "ul"
                    inner += f"<{st}>" + "".join(f"<li>{self.fix_inline(x)}</li>" for x in it["sub"]["sub"]) + f"</{st}>"
                if strip_tags(inner):
                    items.append(f"<li>{inner}</li>")
            return f"<{tag}>{''.join(items)}</{tag}>" if items else ""
        if t == "image":
            self.figure_no += 1
            src = asset(self.slug, b["src"]) if not b["src"].startswith("http") else b["src"]
            alt = b.get("alt") or f"{context_label} — figure {self.figure_no}"
            w, hgt = b.get("w"), b.get("h")
            dims = f' width="{w}" height="{hgt}"' if w and hgt else ""
            img = f'<img src="{esc(src)}" alt="{esc(alt)}" loading="lazy" decoding="async" referrerpolicy="no-referrer"{dims}>'
            href = b.get("href")
            if href:
                url, external = self.link(href)
                tgt = ' target="_blank" rel="noopener"' if external else ""
                img = f'<a href="{esc(url)}"{tgt}>{img}</a>'
            else:
                img = (f'<a class="zoom" href="{esc(src)}" target="_blank" rel="noopener" '
                       f'aria-label="Open image full size in a new tab">{img}</a>')
            return f'<figure class="figure">{img}</figure>'
        if t == "embed":
            return self.embed(b)
        if t == "video":
            title = b.get("title") or "YouTube video"
            if title == "YouTube video":
                title = f"Video for {context_label}"
            vid = esc(b["id"])
            return (f'<figure class="resource resource--video">'
                    f'<div class="frame frame--16x9"><iframe src="https://www.youtube-nocookie.com/embed/{vid}" '
                    f'title="{esc(title)}" loading="lazy" allow="accelerometer; encrypted-media; gyroscope; picture-in-picture; fullscreen" '
                    f'allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe></div>'
                    f'<figcaption><span class="kind">Video</span>'
                    f'<a href="https://www.youtube.com/watch?v={vid}" target="_blank" rel="noopener">Watch on YouTube</a></figcaption></figure>')
        if t == "linkcard":
            img = ""
            if b.get("img"):
                src = asset(self.slug, b["img"]) if not b["img"].startswith("http") else b["img"]
                img = f'<img src="{esc(src)}" alt="" loading="lazy" referrerpolicy="no-referrer">'
            domain = re.sub(r"^https?://(www\.)?", "", b["href"] or "").split("/")[0]
            return (f'<a class="linkcard" href="{esc(b["href"])}" target="_blank" rel="noopener">{img}'
                    f'<span class="linkcard__body"><span class="linkcard__title">{esc(b["title"])}</span>'
                    f'<span class="linkcard__desc">{esc(b["desc"])}</span>'
                    f'<span class="linkcard__domain">{esc(domain)}</span></span></a>')
        if t == "urlembed":
            return (f'<p class="resource-link"><span class="kind">Presentation</span> '
                    f'<a href="{esc(b["href"])}" target="_blank" rel="noopener">Open the class presentation (OneDrive)</a></p>')
        return ""

    def embed(self, b):
        kind = b.get("kind") or "File"
        title = b.get("title") or kind
        open_url = b["open"]
        src = b.get("src") or ""
        if "drive.google.com/file" in open_url and not src:
            src = re.sub(r"/view.*$", "/preview", open_url)
        label = {"Presentation": "Slides", "Document": "Document", "Spreadsheet": "Spreadsheet",
                 "PDF": "PDF", "Form": "Form"}.get(kind, kind)
        ratio = "frame--slides" if kind == "Presentation" else "frame--doc"
        frame = ""
        if src:
            frame = (f'<div class="frame {ratio}"><iframe src="{esc(src)}" title="{esc(label)}: {esc(title)}" '
                     f'loading="lazy" allowfullscreen></iframe></div>')
        return (f'<figure class="resource">'
                f'<figcaption><span class="kind">{esc(label)}</span><span class="resource__title">{esc(title)}</span>'
                f'<a href="{esc(open_url)}" target="_blank" rel="noopener">Open<span class="sr-only"> {esc(title)}</span> in new tab</a>'
                f'</figcaption>{frame}</figure>')

    def section(self, sec, context_label):
        cols = []
        for col in sec["cols"]:
            parts = [self.block(b, context_label) for b in col]
            parts = [p for p in parts if p]
            if parts:
                cols.append("".join(parts))
        if not cols:
            return ""
        if len(cols) == 1:
            return f'<div class="block">{cols[0]}</div>'
        return (f'<div class="block block--cols" style="--cols:{len(cols)}">'
                + "".join(f'<div class="col">{c}</div>' for c in cols) + "</div>")


# ------------------------------------------------------------------ layout
def nav_html(slug, pages):
    cur = pages[slug]
    open_group = cur["parent"] or (slug if cur["children"] else None)
    out = ['<ul class="nav__list" role="list">']
    for p in pages.values():
        if p["parent"]:
            continue
        current = ' aria-current="page"' if p["slug"] == slug else ""
        if p["children"]:
            expanded = "true" if p["slug"] == open_group else "false"
            gid = "g-" + p["slug"]
            out.append(f'<li class="nav__group" data-open="{expanded}">'
                       f'<div class="nav__row"><a href="{rel(slug, p["slug"])}"{current}>{esc(p["label"])}</a>'
                       f'<button class="nav__toggle" type="button" aria-expanded="{expanded}" aria-controls="{gid}">'
                       f'<span class="sr-only">Show topics in {esc(p["label"])}</span>'
                       f'<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6 4l4 4-4 4" fill="none" stroke="currentColor" stroke-width="1.6"/></svg></button></div>'
                       f'<ul class="nav__sub" id="{gid}" role="list">')
            for cs in p["children"]:
                c = pages[cs]
                cc = ' aria-current="page"' if cs == slug else ""
                hl = ' <span class="tag tag--hl">HL</span>' if c["hl"] else ""
                out.append(f'<li><a href="{rel(slug, cs)}"{cc}>{esc(c["label"])}{hl}</a></li>')
            out.append("</ul></li>")
        else:
            out.append(f'<li><div class="nav__row"><a href="{rel(slug, p["slug"])}"{current}>{esc(p["label"])}</a></div></li>')
    out.append("</ul>")
    return "".join(out)


def breadcrumbs(slug, pages):
    if slug == "home":
        return ""
    trail = [("home", "Home")]
    p = pages[slug]
    if p["parent"]:
        trail.append((p["parent"], short_unit(pages[p["parent"]]["label"])))
    items = "".join(f'<li><a href="{rel(slug, s)}">{esc(l)}</a></li>' for s, l in trail)
    items += f'<li aria-current="page">{esc(short_label(p["label"]))}</li>'
    return f'<nav class="crumbs" aria-label="Breadcrumb"><ol role="list">{items}</ol></nav>'


def short_unit(label):
    return label.split(" · ")[0] if label.startswith("Unit") else label


def short_label(label):
    return label


def pager(slug, order, pages):
    i = order.index(slug)
    prev_s = order[i - 1] if i > 0 else None
    next_s = order[i + 1] if i + 1 < len(order) else None
    parts = []
    if prev_s:
        parts.append(f'<a class="pager__link pager__link--prev" href="{rel(slug, prev_s)}" rel="prev">'
                     f'<span class="pager__dir">Previous</span><span class="pager__title">{esc(pages[prev_s]["label"])}</span></a>')
    else:
        parts.append("<span></span>")
    if next_s:
        parts.append(f'<a class="pager__link pager__link--next" href="{rel(slug, next_s)}" rel="next">'
                     f'<span class="pager__dir">Next</span><span class="pager__title">{esc(pages[next_s]["label"])}</span></a>')
    return f'<nav class="pager" aria-label="Previous and next page">{"".join(parts)}</nav>'


def child_list(slug, pages, heading="Topics in this unit"):
    p = pages[slug]
    if not p["children"]:
        return ""
    items = []
    for cs in p["children"]:
        c = pages[cs]
        hl = '<span class="tag tag--hl">HL</span>' if c["hl"] else ""
        num, _, name = c["label"].partition(" ")
        if not re.match(r"^\d", num):
            num, name = "", c["label"]
        items.append(f'<li><a href="{rel(slug, cs)}"><span class="topic__num">{esc(num)}</span>'
                     f'<span class="topic__name">{esc(name)}</span>{hl}</a></li>')
    return (f'<section class="topics" aria-labelledby="topics-h"><h2 id="topics-h">{heading}</h2>'
            f'<ol class="topics__list" role="list">{"".join(items)}</ol></section>')


def course_map(pages):
    cards = []
    for p in pages.values():
        if p["parent"] or not p["children"]:
            continue
        blurb = UNIT_BLURB.get(p["slug"], "")
        n = len(p["children"])
        cards.append(f'<li class="unit"><a href="{rel("home", p["slug"])}">'
                     f'<span class="unit__name">{esc(p["label"])}</span>'
                     f'<span class="unit__blurb">{esc(blurb)}</span>'
                     f'<span class="unit__meta">{n} topics</span></a></li>')
    quick = [("introduction", "Course introduction"), ("bm-start-point", "Start point and IB guide"),
             ("ia", "Internal Assessment"), ("assessment-ib-paper-1-2-and-3", "Papers 1, 2 and 3"),
             ("exam-tracker", "Exam tracker"), ("grading-criteria", "Grading criteria")]
    ql = "".join(f'<li><a href="{rel("home", s)}">{esc(l)}</a></li>' for s, l in quick)
    return (f'<section class="course" aria-labelledby="course-h"><h2 id="course-h">Course map</h2>'
            f'<ul class="units" role="list">{"".join(cards)}</ul>'
            f'<h3 class="course__quick-h">Assessment and planning</h3><ul class="quick" role="list">{ql}</ul></section>')


def page_html(slug, pages, order, data):
    p = pages[slug]
    raw = data.get(slug.replace("/", "_"))
    r = Renderer(slug, pages)
    label = p["label"]
    blocks = []
    if raw:
        secs = raw["sections"]
        # The first (banner) section only carries the page title; skip its headings.
        if secs and secs[0].get("bg"):
            rest = [b for col in secs[0]["cols"] for b in col if not b["type"].startswith("h")]
            secs = ([{"cols": [rest]}] if rest else []) + secs[1:]
        for sec in secs:
            h = r.section(sec, label)
            if h:
                blocks.append(h)

    if slug == "home":
        title_h = "IBDP Business Management"
        kicker = "Mr. Mo's course website"
        lede = ("Class notes, slides, practice questions and assessment guidance for the IB Diploma "
                "Business Management course, SL and HL.")
    else:
        title_h = label.split(" · ", 1)[1] if label.startswith("Unit") and " · " in label else label
        m = re.match(r"^(\d+\.\d+)\s+(.*)$", label)
        if m:
            title_h = m.group(2)
            kicker = f"Unit {m.group(1).split('.')[0]} · Topic {m.group(1)}"
        elif label.startswith("Unit"):
            kicker = label.split(" · ")[0]
        elif p["parent"] == "bm-toolkit":
            kicker = "BM Toolkit"
        else:
            kicker = "Course guide"
        lede = UNIT_BLURB.get(slug, "")

    hl = '<span class="tag tag--hl" title="Higher Level only">HL only</span>' if p["hl"] else ""
    body_main = "".join(blocks)

    extra = ""
    if slug == "home":
        extra_top = course_map(pages)
    else:
        extra_top = ""
    if p["children"]:
        extra = child_list(slug, pages, "Toolkit topics" if slug == "bm-toolkit" else "Topics in this unit")
        # Unit landing pages: show the topic list first when the page has little content of its own.
        if len(body_main) < 400:
            extra_top, extra = extra, ""
    if not body_main and not extra_top and not extra:
        body_main = ('<p class="empty">Materials for this page have not been published yet. '
                     f'Check the <a href="{ORIGINAL}/{slug}" target="_blank" rel="noopener">original page</a> '
                     'or ask Mr. Mo in class.</p>')

    toc = ""
    if len(r.toc) >= 3:
        links = "".join(f'<li><a href="#{hid}">{esc(t)}</a></li>' for hid, t in r.toc)
        toc = (f'<details class="toc"><summary>On this page</summary>'
               f'<ol role="list">{links}</ol></details>')

    lede_html = f'<p class="lede">{esc(lede)}</p>' if lede else ""
    doc_title = SITE_NAME if slug == "home" else f"{label.replace(' · ', ' – ')} | {SITE_NAME}"
    original = f"{ORIGINAL}" + ("" if slug == "home" else f"/{slug}")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(doc_title)}</title>
<meta name="description" content="{esc(lede or ('IBDP Business Management: ' + label))}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Sans+3:ital,wght@0,400;0,600;0,700;1,400&family=Source+Serif+4:opsz,wght@8..60,600;8..60,700&display=swap">
<link rel="stylesheet" href="{asset(slug, 'assets/css/site.css')}">
<link rel="icon" href="{asset(slug, 'assets/img/favicon.svg')}" type="image/svg+xml">
<script src="{asset(slug, 'assets/js/site.js')}" defer></script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="topbar">
  <div class="topbar__inner">
    <button class="menu-btn" type="button" aria-expanded="false" aria-controls="sidebar">
      <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 5h14M3 10h14M3 15h14" stroke="currentColor" stroke-width="1.8" fill="none"/></svg>
      <span>Menu</span>
    </button>
    <a class="brand" href="{rel(slug, 'home')}"><span class="brand__mark" aria-hidden="true">BM</span><span class="brand__text">Mr. Mo <span class="brand__sub">IBDP Business Management</span></span></a>
  </div>
</header>
<div class="shell">
  <aside class="sidebar" id="sidebar" aria-label="Site navigation">
    <div class="sidebar__search">
      <label for="nav-filter" class="sr-only">Filter topics</label>
      <input id="nav-filter" type="search" placeholder="Find a topic…" autocomplete="off">
    </div>
    <nav class="nav" aria-label="Course pages">{nav_html(slug, pages)}</nav>
  </aside>
  <div class="scrim" hidden></div>
  <main id="main" class="main" tabindex="-1">
    <article class="page">
      {breadcrumbs(slug, pages)}
      <header class="page__head">
        <p class="kicker">{esc(kicker)}</p>
        <h1>{esc(title_h)} {hl}</h1>
        {lede_html}
      </header>
      {toc}
      {extra_top}
      <div class="prose">{body_main}</div>
      {extra}
      {pager(slug, order, pages)}
    </article>
    <footer class="footer">
      <p><strong>Mr. Mo</strong> · <a href="mailto:mrajdev@sis.gl">mrajdev@sis.gl</a> · Ubuntu Building, U3</p>
      <p><a href="{esc(original)}" target="_blank" rel="noopener">View this page on the original Google Site</a></p>
    </footer>
  </main>
</div>
</body>
</html>
"""


def redirect_html(slug, target):
    url = rel(slug, target)
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Redirecting…</title>'
            f'<meta http-equiv="refresh" content="0; url={url}"><link rel="canonical" href="{url}"></head>'
            f'<body><p>This page has moved to <a href="{url}">{url}</a>.</p></body></html>')


def main():
    data = json.load(open(CONTENT))
    plist = build_index()
    pages = {p["slug"]: p for p in plist}
    order = [p["slug"] for p in plist]
    for slug in order:
        path = out_path(slug)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(page_html(slug, pages, order, data))
    for slug, target in REDIRECTS.items():
        path = out_path(slug)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(redirect_html(slug, target))
    with open(os.path.join(ROOT, "404.html"), "w") as f:
        f.write(redirect_html("home", "home").replace("This page has moved to", "Page not found. Go to"))
    print(f"Built {len(order)} pages and {len(REDIRECTS)} redirect(s).")


if __name__ == "__main__":
    main()

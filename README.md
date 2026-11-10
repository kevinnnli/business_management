# Mr. Mo · IBDP Business Management

A static rebuild of Mr. Mo's Google Site
(<https://sites.google.com/view/mrmo-businessmanagement>) with a simpler, academic design.

## Structure

- `index.html` and one folder per page (`unit-5-operations-management/5-4-location/index.html`, …).
  The paths mirror the original site's URLs, and all links are relative, so the site works on GitHub Pages,
  on any static host, or opened straight from disk.
- `assets/css/site.css`: the design system (colour, type and spacing tokens at the top).
- `assets/js/site.js`: mobile menu, collapsible units, topic filter, image fallback.
- `tools/content.json`: page content extracted from the Google Site.
- `tools/build.py`: generates every page from `content.json`. Navigation order and labels live in `NAV`.
- `tools/extract.py`: re-extracts `content.json` from saved copies of the Google Site pages.

## Rebuild

```bash
python3 tools/build.py
```

## Preview

```bash
python3 -m http.server 8000
```

Then open http://localhost:8000.

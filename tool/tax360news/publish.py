"""Pubblicazione sul sito: pagina /news/<slug>.html + indice assets/news.js + sitemap.

La pagina articolo riusa testata, menu e piè di pagina di site/news.html,
così resta sempre allineata al resto del sito."""
import datetime as dt
import html
import json
import os
import re

import markdown

from .gate import check

SITE_URL = "https://tax360.it"
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]
STATO_LABEL = {
    "proposta": "Proposta, non ancora approvata",
    "pubblicato": "Atto pubblicato",
    "in_vigore": "In vigore",
    "in_attesa_attuazione": "In attesa dei provvedimenti attuativi",
    "prassi": "Documento di prassi",
    "giurisprudenza": "Pronuncia giurisprudenziale",
}
NEWS_RE = re.compile(r"/\*NEWS:START\*/(.*?)/\*NEWS:END\*/", re.S)
STATIC_PAGES = ["", "chisiamo", "servizi", "news", "scadenziario", "contatti", "prenota",
                "enrico-assunto", "davide-spiniello"]


class PublishBlocked(Exception):
    pass


def esc(s):
    return html.escape(str(s or ""), quote=True)


def data_it(s):
    try:
        d = dt.date.fromisoformat(str(s)[:10])
        return f"{d.day} {MESI[d.month - 1]} {d.year}"
    except ValueError:
        return esc(s)


def md_to_html(text):
    """Markdown → HTML senza HTML grezzo; link esterni in nuova scheda."""
    safe = (text or "").replace("<", "&lt;")
    out = markdown.markdown(safe, extensions=["extra", "sane_lists"], output_format="html")
    out = re.sub(r'href="(?!https?://)[^"]*"', 'href="#"', out)   # niente javascript:, data:, ecc.
    out = out.replace('<a href="http', '<a target="_blank" rel="noopener" href="http')
    # i titoli dell'articolo partono da h2 (h1 è il titolo della pagina)
    out = re.sub(r"<(/?)h1>", r"<\1h2>", out)
    return out


# ------------------------------------------------------------------ news.js
def read_index(site_dir):
    s = open(os.path.join(site_dir, "assets", "news.js"), encoding="utf-8").read()
    m = NEWS_RE.search(s)
    if not m:
        raise ValueError("assets/news.js: marcatori NEWS:START/END non trovati")
    return json.loads(m.group(1) or "[]"), s


def write_index(site_dir, items):
    _, s = read_index(site_dir)
    items = sorted(items, key=lambda x: (x.get("data", ""), x.get("slug", "")), reverse=True)
    body = json.dumps(items, ensure_ascii=False, indent=2)
    s = NEWS_RE.sub(lambda _: "/*NEWS:START*/" + body + "/*NEWS:END*/", s)
    open(os.path.join(site_dir, "assets", "news.js"), "w", encoding="utf-8").write(s)


# ------------------------------------------------------------------ page shell
def _shell(site_dir):
    s = open(os.path.join(site_dir, "news.html"), encoding="utf-8").read()
    head = s[: s.index('<section class="page-hero">')]
    foot = s[s.index("<!-- ===== FOOTER ===== -->"):]

    def rel(x):  # la pagina vive in /news/: i percorsi relativi salgono di un livello
        return re.sub(r'(href|src)="(?!https?:|mailto:|tel:|#|/|\.\./)([^"]+)"', r'\1="../\2"', x)
    return rel(head), rel(foot)


def render_article(d, site_dir, today=None):
    head, foot = _shell(site_dir)
    url = f"{SITE_URL}/news/{d['slug']}"
    pub = d.get("pubblicataIl") or (today or dt.date.today().isoformat())
    agg = d.get("aggiornataIl")
    title_tag = f"<title>{esc(d['titoloSeo'])} | TAX360</title>"
    head = re.sub(r"<title>.*?</title>", title_tag, head, count=1, flags=re.S)
    head = re.sub(r'<meta name="description" content="[^"]*">',
                  f'<meta name="description" content="{esc(d["metaDescription"])}">', head, count=1)
    ld = {
        "@context": "https://schema.org", "@type": "NewsArticle",
        "headline": d["titolo"], "description": d["metaDescription"],
        "datePublished": pub, "dateModified": agg or pub, "inLanguage": "it-IT",
        "mainEntityOfPage": url,
        "author": {"@type": "Organization", "name": "TAX360 — Professional Advisory"},
        "publisher": {"@type": "Organization", "name": "TAX360 — Professional Advisory",
                      "logo": {"@type": "ImageObject", "url": f"{SITE_URL}/assets/logo-light.png"}},
    }
    extra = (f'<link rel="canonical" href="{url}">\n'
             f'<meta property="og:type" content="article">\n'
             f'<meta property="og:title" content="{esc(d["titoloSeo"])}">\n'
             f'<meta property="og:description" content="{esc(d["metaDescription"])}">\n'
             f'<meta property="og:url" content="{url}">\n'
             f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n')
    head = head.replace("</head>", extra + "</head>", 1)

    date = d.get("date") or {}
    facts = [("Stato", STATO_LABEL.get(d.get("statoAtto"), d.get("statoAtto")))]
    facts.append(("Data del documento", data_it(date.get("pubblicazione"))))
    facts.append(("Entrata in vigore", data_it(date["entrataInVigore"]) if date.get("entrataInVigore") else "Non applicabile o non ancora definita"))
    facts.append(("Decorrenza", data_it(date["decorrenza"]) if date.get("decorrenza") else "Non applicabile o non ancora definita"))
    for sc in date.get("scadenze") or []:
        facts.append(("Scadenza", f"{data_it(sc.get('data'))} — {esc(sc.get('descrizione'))}"))
    facts_html = "".join(f"<div class=\"af-row\"><dt>{esc(k)}</dt><dd>{v if k == 'Scadenza' else esc(v)}</dd></div>"
                         for k, v in facts)
    if d.get("dateNote"):
        facts_html += f'<p class="af-note">{esc(d["dateNote"])}</p>'

    uff = "".join(
        f'<li><a href="{esc(f["url"])}" target="_blank" rel="noopener">{esc(f.get("titolo") or f["url"])}</a>'
        f'{" — " + esc(f.get("ente")) if f.get("ente") else ""}</li>'
        for f in d.get("fontiUfficiali") or [] if f.get("aperta"))
    spec = "".join(
        f'<li><a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s.get("titolo") or s["url"])}</a>'
        f' — {esc(s.get("testata"))}{", " + esc(s.get("autore")) if s.get("autore") else ""}</li>'
        for s in d.get("fontiSpecialistiche") or [])
    refs = f'<h3>Fonti ufficiali</h3><ul>{uff}</ul>'
    if spec:
        refs += f'<h3>Approfondimenti della stampa specializzata</h3><ul>{spec}</ul>'

    meta_line = f"Pubblicato il {data_it(pub)}" + (f" &middot; Aggiornato il {data_it(agg)}" if agg else "")
    body = f'''<section class="page-hero">
  <div class="hero-glow"></div>
  <div class="container">
    <span class="eyebrow">{esc(d["categoria"])}</span>
    <h1 class="art-h1">{esc(d["titolo"])}</h1>
    <p class="lead">{esc(d["sintesi"])}</p>
    <p class="art-meta">{meta_line}</p>
    <div class="breadcrumb"><a href="../index.html">Home</a><span>/</span><a href="../news.html">News Fiscali</a><span>/</span>{esc(d["categoria"])}</div>
  </div>
</section>

<section style="background:var(--paper)">
  <div class="container art-wrap">
    <article class="art">
      <aside class="art-facts"><div class="af-title">In sintesi</div><dl>{facts_html}</dl></aside>
      <div class="art-body">{md_to_html(d["corpo"])}</div>
      <div class="art-refs"><h2>Riferimenti</h2>{refs}</div>
      <p class="art-note">Contenuto informativo aggiornato alla data di pubblicazione: non sostituisce una consulenza
      sul caso specifico. Per valutare gli effetti sulla tua situazione <a href="../prenota.html">prenota un confronto con lo studio</a>.</p>
    </article>
    <aside class="art-side">
      <div class="art-cta">
        <div class="ac-k">Ti riguarda?</div>
        <p>Verifichiamo insieme cosa cambia per la tua impresa o la tua attivit&agrave;.</p>
        <a href="../prenota.html" class="btn btn-gold">Prenota una consulenza <span class="arr">&rarr;</span></a>
      </div>
      <a href="../news.html" class="art-back">&larr; Tutte le news</a>
    </aside>
  </div>
</section>
<style>
.art-h1{{max-width:22ch!important;font-size:clamp(2.1rem,4.4vw,3.4rem)!important}}
.art-meta{{margin-top:1rem;font-size:.82rem;color:rgba(255,255,255,.6);letter-spacing:.03em}}
.art-wrap{{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:4rem;align-items:start}}
.art{{max-width:72ch}}
.art-facts{{background:#fff;border:1px solid rgba(30,58,95,.1);border-left:3px solid var(--gold);border-radius:3px;padding:1.4rem 1.6rem;margin-bottom:2.6rem}}
.af-title{{font-size:.7rem;letter-spacing:.2em;text-transform:uppercase;color:var(--gold);font-weight:700;margin-bottom:.8rem}}
.art-facts dl{{display:grid;gap:.45rem}}
.af-row{{display:grid;grid-template-columns:150px 1fr;gap:1rem;font-size:.92rem}}
.af-row dt{{color:#6b7480;font-weight:500}} .af-row dd{{color:var(--navy);font-weight:600}}
.af-note{{margin-top:.8rem;font-size:.85rem;color:#5a6573;font-weight:300}}
.art-body{{font-size:1.06rem;line-height:1.85;color:#2c3845;font-weight:300}}
.art-body p,.art-body ul,.art-body ol,.art-body table,.art-body blockquote{{margin-bottom:1.3rem}}
.art-body h2{{font-family:var(--serif);font-size:1.8rem;color:var(--navy);font-weight:600;margin:2.4rem 0 .9rem;line-height:1.2}}
.art-body h3{{font-family:var(--serif);font-size:1.35rem;color:var(--navy);font-weight:600;margin:1.8rem 0 .6rem}}
.art-body ul,.art-body ol{{padding-left:1.3rem}} .art-body li{{margin-bottom:.4rem}}
.art-body strong{{font-weight:600;color:var(--ink)}}
.art-body a,.art-refs a,.art-note a{{color:var(--gold);text-decoration:none;border-bottom:1px solid rgba(184,151,62,.35)}}
.art-body blockquote{{border-left:2px solid var(--gold);padding-left:1.2rem;font-style:italic;color:#42505f}}
.art-body table{{width:100%;border-collapse:collapse;font-size:.95rem}}
.art-body th,.art-body td{{border-bottom:1px solid rgba(30,58,95,.12);padding:.6rem .5rem;text-align:left}}
.art-body th{{color:var(--navy);font-weight:600}}
.art-refs{{margin-top:3rem;padding-top:2rem;border-top:1px solid rgba(30,58,95,.12)}}
.art-refs h2{{font-family:var(--serif);font-size:1.5rem;color:var(--navy);margin-bottom:1rem}}
.art-refs h3{{font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;color:var(--gold);margin:1.2rem 0 .5rem}}
.art-refs ul{{padding-left:1.1rem;font-size:.95rem;color:#42505f;line-height:1.7}}
.art-note{{margin-top:2.4rem;font-size:.86rem;color:#6b7480;font-weight:300;line-height:1.7;background:var(--paper-warm);padding:1rem 1.2rem;border-radius:3px}}
.art-side{{position:sticky;top:110px}}
.art-cta{{background:linear-gradient(135deg,var(--navy) 0%,var(--navy-deep) 100%);color:#fff;border-radius:4px;padding:2rem}}
.ac-k{{font-family:var(--serif);font-size:1.6rem;font-weight:600;margin-bottom:.6rem}}
.art-cta p{{font-weight:300;color:rgba(255,255,255,.8);margin-bottom:1.4rem;font-size:.95rem}}
.art-cta .btn{{width:100%;justify-content:center}}
.art-back{{display:inline-block;margin-top:1.4rem;font-size:.8rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--navy);text-decoration:none}}
@media(max-width:960px){{.art-wrap{{grid-template-columns:1fr;gap:2.5rem}}.art-side{{position:static}}.af-row{{grid-template-columns:1fr;gap:0}}}}
</style>
'''
    return head + body + foot


def write_sitemap(site_dir, items):
    urls = [f"{SITE_URL}/{p}" if p else f"{SITE_URL}/" for p in STATIC_PAGES]
    urls += [f"{SITE_URL}/news/{n['slug']}" for n in items]
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    xml += [f"  <url><loc>{u}</loc></url>" for u in urls]
    xml.append("</urlset>")
    open(os.path.join(site_dir, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(xml) + "\n")


def publish(draft, site_dir, fonti, today=None):
    """Pubblica (o aggiorna) un articolo. Rifiuta se il controllo di pubblicabilità fallisce."""
    motivi = check(draft, fonti)
    if motivi:
        raise PublishBlocked("; ".join(motivi))
    today = today or dt.date.today().isoformat()
    items, _ = read_index(site_dir)
    existing = next((x for x in items if x["slug"] == draft["slug"]), None)
    d = dict(draft)
    d["pubblicataIl"] = (existing or {}).get("data") or d.get("pubblicataIl") or today
    if existing:
        d["aggiornataIl"] = today
    os.makedirs(os.path.join(site_dir, "news"), exist_ok=True)
    path = os.path.join(site_dir, "news", f"{d['slug']}.html")
    open(path, "w", encoding="utf-8").write(render_article(d, site_dir, today))
    first_uff = next((f for f in d.get("fontiUfficiali") or [] if f.get("aperta")), {})
    entry = {"data": d["pubblicataIl"], "cat": d["categoria"], "titolo": d["titolo"],
             "sintesi": d["sintesi"], "slug": d["slug"], "url": f"news/{d['slug']}.html",
             "fonte": first_uff.get("ente") or ""}
    items = [x for x in items if x["slug"] != d["slug"]] + [entry]
    write_index(site_dir, items)
    write_sitemap(site_dir, items)
    return {"url": f"{SITE_URL}/news/{d['slug']}", "file": path, "aggiornato": bool(existing)}


def unpublish(slug, site_dir):
    items, _ = read_index(site_dir)
    items = [x for x in items if x["slug"] != slug]
    write_index(site_dir, items)
    write_sitemap(site_dir, items)
    path = os.path.join(site_dir, "news", f"{slug}.html")
    if os.path.exists(path):
        os.remove(path)
    return {"rimosso": slug}

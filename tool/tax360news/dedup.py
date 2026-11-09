"""Doppioni e sviluppi sostanziali.

Una notizia già trattata si ripropone solo se c'è uno sviluppo sostanziale,
e in quel caso si dichiara che cosa è cambiato."""
import re
from urllib.parse import urlsplit, urlunsplit

# campi il cui cambiamento rende la notizia di nuovo rilevante
CAMPI_SOSTANZIALI = {
    "statoAtto": "stato dell'atto",
    "entrataInVigore": "entrata in vigore",
    "decorrenza": "decorrenza",
    "scadenze": "scadenze",
    "importiChiave": "importi / aliquote / soglie",
    "tipoDocumento": "tipo di documento",
}


def canonical_url(url):
    p = urlsplit(str(url).strip())
    host = (p.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = re.sub(r"/+$", "", p.path) or "/"
    return urlunsplit(("https", host, path, "", ""))


def _norm_id(s):
    s = str(s).lower()
    s = s.replace("numero", "n").replace("n°", "n").replace("nr.", "n").replace("n.", "n")
    return re.sub(r"[^a-z0-9]", "", s)


def event_key(n):
    """Chiave dell'atto/evento: ente + identificativo se disponibile, altrimenti
    il link ufficiale canonico, altrimenti il link principale."""
    ident = n.get("identificativo")
    if ident:
        return "id:" + _norm_id(n.get("ente", "")) + ":" + _norm_id(ident)
    for f in n.get("fontiUfficiali") or []:
        if f.get("url"):
            return "url:" + canonical_url(f["url"])
    if n.get("link"):
        return "url:" + canonical_url(n["link"])
    return "title:" + _norm_id(n.get("titolo", ""))


def _official_urls(n):
    return {canonical_url(f["url"]) for f in (n.get("fontiUfficiali") or []) if f.get("url")}


def _val(n, campo):
    if campo in ("entrataInVigore", "decorrenza"):
        return (n.get("date") or {}).get(campo, n.get(campo))
    if campo == "scadenze":
        sc = (n.get("date") or {}).get("scadenze", n.get("scadenze")) or []
        return sorted((s.get("data"), s.get("descrizione", "")) for s in sc)
    v = n.get(campo)
    return sorted(v) if isinstance(v, list) else v


def find_previous(n, history):
    key = event_key(n)
    urls = _official_urls(n)
    for old in history:
        if event_key(old) == key or (urls and urls & _official_urls(old)):
            return old
    return None


def classify(n, history):
    """('nuova', [], None) | ('duplicato', [], prev) | ('sviluppo', [cambiamenti], prev)."""
    prev = find_previous(n, history)
    if prev is None:
        return "nuova", [], None
    changes = []
    for campo, label in CAMPI_SOSTANZIALI.items():
        a, b = _val(prev, campo), _val(n, campo)
        if b not in (None, [], "") and a != b:
            changes.append(f"{label}: {a or '—'} → {b}")
    new_docs = _official_urls(n) - _official_urls(prev)
    if new_docs:
        changes.append("nuovo documento ufficiale: " + ", ".join(sorted(new_docs)))
    return ("sviluppo", changes, prev) if changes else ("duplicato", [], prev)

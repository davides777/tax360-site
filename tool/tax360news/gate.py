"""Controllo di pubblicabilità di una bozza.

Una bozza può essere approvata/pubblicata SOLO se `check(...)` non restituisce
motivi di blocco. La pubblicazione automatica e la Scrivania applicano la stessa
regola: nessun dato fiscale essenziale può andare online senza riscontro su un
documento ufficiale effettivamente consultato."""
import re
from . import CATEGORIE, STATI_ATTO
from .domains import source_for

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LINK_RE = re.compile(r"\]\((https?://[^)\s]+)\)")
PROPOSTA_WORDS = ("proposta", "disegno di legge", "ddl", "bozza", "schema di decreto",
                  "in discussione", "emendament", "in esame", "non ancora approvat")
VIGORE_CLAIMS = (r"\bè in vigore\b", r"\bsono in vigore\b", r"\bè entrat[ao] in vigore\b",
                 r"\bsono entrat[ei] in vigore\b", r"\bsi applica dal\b")


def _first_paragraph(md):
    for block in re.split(r"\n\s*\n", md or ""):
        b = block.strip()
        if b and not b.startswith("#"):
            return b
    return ""


def check(draft, fonti):
    """Ritorna l'elenco dei motivi di blocco (vuoto = pubblicabile)."""
    r = []
    req = ("titolo", "titoloSeo", "slug", "metaDescription", "sintesi", "corpo", "categoria", "statoAtto")
    for k in req:
        if not str(draft.get(k) or "").strip():
            r.append(f"campo obbligatorio mancante: {k}")
    slug = draft.get("slug") or ""
    if slug and (not SLUG_RE.match(slug) or len(slug) > 80):
        r.append("slug non valido (solo minuscole, numeri e trattini, max 80)")
    if len(draft.get("titoloSeo") or "") > 65:
        r.append("titolo SEO oltre 65 caratteri")
    md = draft.get("metaDescription") or ""
    if md and not (50 <= len(md) <= 160):
        r.append("meta description fuori dall'intervallo 50–160 caratteri")
    if draft.get("categoria") and draft["categoria"] not in CATEGORIE:
        r.append("categoria non ammessa")

    # --- stato dell'atto e date distinte ---
    stato = draft.get("statoAtto")
    if stato and stato not in STATI_ATTO:
        r.append("stato dell'atto non riconosciuto")
    date = draft.get("date") or {}
    if not DATE_RE.match(str(date.get("pubblicazione") or "")):
        r.append("data di pubblicazione dell'atto/documento mancante (AAAA-MM-GG)")
    for k in ("entrataInVigore", "decorrenza"):
        if k not in date:
            r.append(f"campo '{k}' non indicato: va valorizzato o dichiarato non applicabile (null + nota)")
    if stato in ("pubblicato", "in_vigore", "in_attesa_attuazione") and \
            not date.get("entrataInVigore") and not date.get("decorrenza") and not draft.get("dateNote"):
        r.append("atto normativo senza entrata in vigore/decorrenza e senza nota esplicativa")
    corpo = draft.get("corpo") or ""
    if stato == "proposta":
        head = (draft.get("titolo", "") + " " + _first_paragraph(corpo)).lower()
        if not any(w in head for w in PROPOSTA_WORDS):
            r.append("misura ancora in proposta: titolo o apertura devono dirlo esplicitamente")
        if any(re.search(p, corpo.lower()) for p in VIGORE_CLAIMS):
            r.append("misura in proposta descritta come in vigore/applicabile")

    # --- fonti ---
    uff = [f for f in draft.get("fontiUfficiali") or []
           if f.get("aperta") and (source_for(f.get("url"), fonti) or {}).get("categoria") == "ufficiale"]
    if not uff:
        r.append("nessun documento ufficiale consultato su un dominio ufficiale approvato (segnalazione da verificare)")
    for f in draft.get("fontiUfficiali") or []:
        if source_for(f.get("url"), fonti) is None:
            r.append(f"fonte ufficiale fuori elenco: {f.get('url')}")
    for s in draft.get("fontiSpecialistiche") or []:
        src = source_for(s.get("url"), fonti)
        if src is None or src.get("categoria") != "specialistica":
            r.append(f"fonte specialistica non approvata: {s.get('url')}")
        testata = (s.get("testata") or "").strip()
        if not testata:
            r.append("approfondimento specialistico senza testata indicata")
        elif testata.lower() not in corpo.lower():
            r.append(f"interpretazione di '{testata}' non attribuita nel testo")
    for url in LINK_RE.findall(corpo):
        if source_for(url, fonti) is None:
            r.append(f"link nel testo verso sito non approvato: {url}")

    # --- verifiche dei dati essenziali ---
    scheda = draft.get("scheda") or {}
    controlli = scheda.get("controlli") or []
    essenziali = [c for c in controlli if c.get("essenziale")]
    if not essenziali:
        r.append("nessun dato essenziale registrato nella scheda di verifica")
    for c in essenziali:
        if c.get("esito") != "verificato":
            r.append(f"dato essenziale da verificare: {c.get('dato')}")
        elif (source_for(c.get("fonte"), fonti) or {}).get("categoria") != "ufficiale":
            r.append(f"dato essenziale verificato senza fonte ufficiale: {c.get('dato')}")
    for d in scheda.get("dubbi") or []:
        if d.get("bloccante"):
            r.append("dubbio bloccante aperto: " + str(d.get("testo")))
    return r


def is_publishable(draft, fonti):
    return not check(draft, fonti)

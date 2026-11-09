"""Smistamento delle notizie della scansione e scelta del tema per l'articolo."""
from .domains import source_for
from .dedup import classify


def triage(n, fonti):
    """'verificata' se almeno un documento ufficiale approvato è stato aperto,
    altrimenti 'da_verificare' (va indicato quale documento reperire)."""
    for f in n.get("fontiUfficiali") or []:
        if f.get("aperta") and (source_for(f.get("url"), fonti) or {}).get("categoria") == "ufficiale":
            return "verificata"
    return "da_verificare"


def build_briefing(notizie, history, fonti):
    """Divide le notizie della scansione in: verificate (nuove o sviluppi),
    segnalazioni da verificare, doppioni scartati. Ordina per impatto e urgenza."""
    verificate, segnalazioni, doppioni = [], [], []
    for n in notizie:
        tipo, cambi, prev = classify(n, history)
        n = dict(n, classificazione=tipo, cambiamenti=cambi)
        if tipo == "duplicato":
            doppioni.append(n)
            continue
        if triage(n, fonti) == "verificata":
            verificate.append(n)
        else:
            n.setdefault("documentoDaReperire", "documento ufficiale non individuato")
            segnalazioni.append(n)
    key = lambda x: (-(x.get("impatto") or 0), -(x.get("urgenza") or 0))
    return {"verificate": sorted(verificate, key=key),
            "segnalazioni": sorted(segnalazioni, key=key),
            "doppioni": doppioni,
            "nessunaNovita": not verificate and not segnalazioni}


def choose_for_article(verificate, limit=1):
    """Al massimo `limit` temi: solo notizie verificate che meritano un articolo.
    Nei giorni senza temi validi restituisce [] (solo briefing)."""
    ok = [n for n in verificate if n.get("meritaArticolo") and n.get("classificazione") != "duplicato"]
    return ok[: max(0, int(limit))]

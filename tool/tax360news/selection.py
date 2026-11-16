"""Smistamento delle notizie della scansione e scelta del tema per l'articolo."""
from .domains import source_for
from .dedup import classify


def triage(n, fonti):
    """'verificata' se almeno un documento ufficiale approvato è stato aperto;
    'da_stampa' se manca il documento ufficiale ma almeno una testata
    specialistica approvata è stata letta (può diventare articolo con base
    "stampa"); altrimenti 'da_verificare' (va indicato quale documento reperire)."""
    for f in n.get("fontiUfficiali") or []:
        if f.get("aperta") and (source_for(f.get("url"), fonti) or {}).get("categoria") == "ufficiale":
            return "verificata"
    for s in n.get("fontiSpecialistiche") or []:
        if s.get("letta") and (source_for(s.get("url"), fonti) or {}).get("categoria") == "specialistica":
            return "da_stampa"
    return "da_verificare"


def build_briefing(notizie, history, fonti):
    """Divide le notizie della scansione in: verificate (nuove o sviluppi),
    segnalazioni da verificare, doppioni scartati. Ordina per impatto e urgenza."""
    verificate, segnalazioni, doppioni, da_stampa = [], [], [], []
    for n in notizie:
        tipo, cambi, prev = classify(n, history)
        n = dict(n, classificazione=tipo, cambiamenti=cambi)
        if tipo == "duplicato":
            doppioni.append(n)
            continue
        t = triage(n, fonti)
        if t == "verificata":
            verificate.append(n)
        else:
            n.setdefault("documentoDaReperire", "documento ufficiale non individuato")
            segnalazioni.append(n)
            if t == "da_stampa":
                da_stampa.append(n)
    key = lambda x: (-(x.get("impatto") or 0), -(x.get("urgenza") or 0))
    return {"verificate": sorted(verificate, key=key),
            "segnalazioni": sorted(segnalazioni, key=key),
            "doppioni": doppioni,
            "daStampa": sorted(da_stampa, key=key),
            "nessunaNovita": not verificate and not segnalazioni}


def choose_for_article(verificate, limit=1, da_stampa=()):
    """Al massimo `limit` temi che meritano un articolo: prima le notizie verificate
    sui documenti ufficiali, poi quelle basate sulla stampa specializzata letta
    (articolo con base "stampa"). Senza temi validi restituisce [] (solo briefing)."""
    ok = lambda n: n.get("meritaArticolo") and n.get("classificazione") != "duplicato"
    out = [dict(n, baseArticolo="ufficiale") for n in verificate if ok(n)]
    out += [dict(n, baseArticolo="stampa") for n in da_stampa if ok(n)]
    return out[: max(0, int(limit))]

"""Domini ammessi: una pagina è utilizzabile solo se il suo dominio FINALE
(dopo eventuali reindirizzamenti) appartiene all'elenco delle fonti attive."""
from urllib.parse import urlsplit


def host_of(url):
    """Host normalizzato (minuscolo, senza 'www.' e senza porta). None se l'URL non è http(s)."""
    try:
        parts = urlsplit(str(url).strip())
    except ValueError:
        return None
    if parts.scheme not in ("http", "https"):
        return None
    host = (parts.hostname or "").lower().rstrip(".")
    if not host:
        return None
    return host[4:] if host.startswith("www.") else host


def _matches(host, domain):
    d = domain.lower().strip().rstrip(".")
    if d.startswith("www."):
        d = d[4:]
    return host == d or host.endswith("." + d)


def source_for(url, fonti):
    """Restituisce la fonte attiva (dict) a cui appartiene l'URL, oppure None.

    `fonti` è l'elenco gestito nella Scrivania: dict con almeno
    {"dominio": "...", "categoria": "ufficiale"|"specialistica", "attiva": bool}.
    In caso di più corrispondenze vince il dominio più specifico."""
    host = host_of(url)
    if not host:
        return None
    best = None
    for f in fonti:
        if not f.get("attiva", True):
            continue
        if _matches(host, f["dominio"]):
            if best is None or len(f["dominio"]) > len(best["dominio"]):
                best = f
    return best


def is_allowed(url, fonti, categoria=None):
    f = source_for(url, fonti)
    return f is not None and (categoria is None or f.get("categoria") == categoria)


def check_final_url(chain, fonti):
    """`chain` = URL richiesto seguito da ogni reindirizzamento ricevuto.
    Conta solo l'ultimo: se esce dall'elenco, la pagina va scartata.
    Ritorna (ammesso: bool, fonte|None, url_finale)."""
    if isinstance(chain, str):
        chain = [chain]
    final = chain[-1] if chain else None
    f = source_for(final, fonti) if final else None
    return (f is not None, f, final)

"""Copertura della scansione: completa solo se tutte le fonti attive hanno risposto."""


def report(tentativi, fonti):
    """`tentativi`: [{"dominio": ..., "esito": "ok"|"errore"|"bloccata", "nota": ...}].
    Una fonte attiva senza alcun tentativo conta come 'non interrogata'."""
    attive = [f for f in fonti if f.get("attiva", True)]
    per_dom = {}
    for t in tentativi:
        d = t["dominio"].lower()
        # basta un tentativo riuscito per considerare la fonte raggiunta
        if per_dom.get(d, {}).get("esito") != "ok":
            per_dom[d] = t
    indisponibili, non_interrogate, ok = [], [], []
    for f in attive:
        t = per_dom.get(f["dominio"].lower())
        if t is None:
            non_interrogate.append(f["dominio"])
        elif t.get("esito") == "ok":
            ok.append(f["dominio"])
        else:
            indisponibili.append({"dominio": f["dominio"], "nome": f.get("nome"),
                                  "categoria": f.get("categoria"), "motivo": t.get("nota") or t.get("esito")})
    if not attive or not ok:
        esito = "assente"
    elif indisponibili or non_interrogate:
        esito = "parziale"
    else:
        esito = "completa"
    return {"esito": esito, "raggiunte": ok, "indisponibili": indisponibili, "nonInterrogate": non_interrogate}

"""Prove ripetibili dei 7 criteri di accettazione del brief TAX360.

Eseguire con:  cd tool && python -m pytest -q
I dati sono di esempio (costruiti per la prova): le verifiche sulle fonti reali
sono registrate a parte nell'esito della prima scansione."""
import copy
import json
import os
import shutil

import pytest

from tax360news import coverage, dedup, domains, gate, publish, selection

HERE = os.path.dirname(__file__)
FONTI = json.load(open(os.path.join(HERE, "..", "fonti_iniziali.json"), encoding="utf-8"))
GU = "https://www.gazzettaufficiale.it/eli/id/2026/05/22/26A02590/sg"


def bozza_valida(**over):
    d = {
        "categoria": "Normativa",
        "titolo": "Decreto fiscale: le novità sui versamenti per le imprese",
        "titoloSeo": "Decreto fiscale 2026: novità sui versamenti",
        "slug": "decreto-fiscale-2026-versamenti",
        "metaDescription": "Cosa cambia per i versamenti delle imprese con il decreto fiscale 2026: destinatari, decorrenza e cosa fare.",
        "sintesi": "Il decreto fiscale modifica i versamenti: ecco chi è interessato e da quando.",
        "statoAtto": "in_vigore",
        "date": {"pubblicazione": "2026-05-22", "entrataInVigore": "2026-05-23", "decorrenza": "2026-07-01", "scadenze": []},
        "corpo": "Il decreto è stato pubblicato in Gazzetta Ufficiale.\n\n## Cosa cambia\n\nTesto di prova con [link al testo]("
                 + GU + ").\n\nSecondo FISCOeTASSE la norma riguarda anche le società di persone.",
        "fontiUfficiali": [{"titolo": "DL 38/2026", "ente": "Gazzetta Ufficiale", "url": GU, "aperta": True}],
        "fontiSpecialistiche": [{"testata": "FISCOeTASSE", "titolo": "Approfondimento",
                                 "url": "https://www.fiscoetasse.com/normativa-prassi/13564-x.html"}],
        "scheda": {"controlli": [{"dato": "decorrenza", "valore": "1/7/2026", "fonte": GU,
                                  "riferimento": "art. 2, c. 1", "esito": "verificato", "essenziale": True}],
                   "dubbi": []},
    }
    d.update(over)
    return d


# 1 ─ Escludere un sito non autorizzato, anche in caso di reindirizzamento
def test_1_sito_non_autorizzato_e_reindirizzamenti():
    assert domains.is_allowed("https://www.agenziaentrate.gov.it/portale/x", FONTI)
    assert domains.is_allowed("https://def.finanze.gov.it/x", FONTI)                     # sottodominio
    assert not domains.is_allowed("https://www.blogfisco-esempio.it/news", FONTI)        # fuori elenco
    assert not domains.is_allowed("https://agenziaentrate.gov.it.truffa.com/x", FONTI)   # dominio sosia
    assert not domains.is_allowed("https://agenziaentrate.gov.it@truffa.com/x", FONTI)   # trucco credenziali
    assert not domains.is_allowed("javascript:alert(1)", FONTI)
    ok, _, _ = domains.check_final_url(["https://www.fiscoetasse.com/a", "https://www.altrosito.it/b"], FONTI)
    assert not ok                                                                        # redirect verso fuori elenco
    ok, f, _ = domains.check_final_url(["https://bit.ly/abc", GU], FONTI)
    assert ok and f["categoria"] == "ufficiale"                                          # conta il dominio finale
    # un link fuori elenco nel testo blocca la pubblicazione
    d = bozza_valida(corpo=bozza_valida()["corpo"] + "\n\nVedi [qui](https://www.blogfisco-esempio.it/x).")
    assert any("sito non approvato" in m for m in gate.check(d, FONTI))


# 2 ─ Presentare una proposta come tale e distinguere pubblicazione, entrata in vigore, decorrenza
def test_2_proposta_e_date_distinte():
    prop = bozza_valida(statoAtto="proposta", titolo="Nuova flat tax incrementale per i professionisti",
                        corpo="La misura cambierà le aliquote.\n\nLa norma è in vigore dal 2027.",
                        date={"pubblicazione": "2026-11-05", "entrataInVigore": None, "decorrenza": None},
                        fontiSpecialistiche=[])
    motivi = gate.check(prop, FONTI)
    assert any("ancora in proposta" in m for m in motivi)
    assert any("descritta come in vigore" in m for m in motivi)
    ok = bozza_valida(statoAtto="proposta", fontiSpecialistiche=[],
                      titolo="Legge di bilancio 2027: la proposta sulla flat tax incrementale",
                      corpo="Il disegno di legge di bilancio, ora in esame al Senato, prevede una nuova flat tax.\n\nSe approvata, si applicherebbe dal 2027.",
                      date={"pubblicazione": "2026-10-28", "entrataInVigore": None, "decorrenza": None})
    assert gate.check(ok, FONTI) == []
    senza_campi = bozza_valida(date={"pubblicazione": "2026-05-22"})
    assert any("entrataInVigore" in m for m in gate.check(senza_campi, FONTI))
    assert any("decorrenza" in m for m in gate.check(senza_campi, FONTI))


# 3 ─ Citare un approfondimento specialistico con attribuzione; segnalare l'assenza del riscontro ufficiale
def test_3_attribuzione_e_riscontro_ufficiale_mancante():
    non_attribuita = bozza_valida(corpo="Il decreto è stato pubblicato.\n\nLa norma riguarda anche le società di persone.")
    assert any("non attribuita" in m for m in gate.check(non_attribuita, FONTI))
    solo_stampa = {"titolo": "Nuovo chiarimento sul bollo", "ente": "Agenzia delle Entrate",
                   "fontiUfficiali": [{"url": "https://www.agenziaentrate.gov.it/portale/x", "aperta": False}],
                   "fontiSpecialistiche": [{"testata": "Eutekne", "url": "https://www.eutekne.info/x"}],
                   "documentoDaReperire": "Risposta a interpello sul bollo (testo integrale AdE)"}
    assert selection.triage(solo_stampa, FONTI) == "da_verificare"
    b = selection.build_briefing([solo_stampa], [], FONTI)
    assert b["segnalazioni"] and not b["verificate"]
    assert b["segnalazioni"][0]["documentoDaReperire"].startswith("Risposta a interpello")
    d = bozza_valida(fontiUfficiali=[{"url": "https://www.agenziaentrate.gov.it/portale/x", "aperta": False}])
    assert any("nessun documento ufficiale consultato" in m for m in gate.check(d, FONTI))


# 4 ─ Indicare una copertura parziale quando una fonte non è raggiungibile
def test_4_copertura_parziale():
    fonti = [f for f in FONTI if f["id"] in ("gu", "ade", "fiscoetasse")]
    r = coverage.report([{"dominio": "gazzettaufficiale.it", "esito": "ok"},
                         {"dominio": "agenziaentrate.gov.it", "esito": "bloccata", "nota": "il sito rifiuta la lettura"},
                         {"dominio": "fiscoetasse.com", "esito": "ok"}], fonti)
    assert r["esito"] == "parziale"
    assert r["indisponibili"][0]["dominio"] == "agenziaentrate.gov.it"
    r = coverage.report([{"dominio": "gazzettaufficiale.it", "esito": "ok"}], fonti)
    assert r["esito"] == "parziale" and set(r["nonInterrogate"]) == {"agenziaentrate.gov.it", "fiscoetasse.com"}
    tutte = [{"dominio": f["dominio"], "esito": "ok"} for f in fonti]
    assert coverage.report(tutte, fonti)["esito"] == "completa"


# 5 ─ Riconoscere una notizia duplicata e riproporla solo con uno sviluppo sostanziale
def test_5_duplicati_e_sviluppi():
    old = {"ente": "Agenzia delle Entrate", "identificativo": "Circolare n. 12/E del 2026", "statoAtto": "prassi",
           "fontiUfficiali": [{"url": "https://www.agenziaentrate.gov.it/portale/c12"}]}
    same = {"ente": "Agenzia delle Entrate", "identificativo": "circolare n.12/E del 2026", "statoAtto": "prassi",
            "fontiUfficiali": [{"url": "https://agenziaentrate.gov.it/portale/c12/"}]}
    assert dedup.classify(same, [old])[0] == "duplicato"
    ddl = {"ente": "Senato", "identificativo": "DDL 1500", "statoAtto": "proposta",
           "fontiUfficiali": [{"url": "https://www.senato.it/ddl1500"}]}
    legge = dict(ddl, statoAtto="pubblicato", fontiUfficiali=ddl["fontiUfficiali"] + [{"url": GU}],
                 date={"entrataInVigore": "2027-01-01"})
    tipo, cambi, _ = dedup.classify(legge, [ddl])
    assert tipo == "sviluppo"
    assert any("stato dell'atto" in c for c in cambi) and any("nuovo documento ufficiale" in c for c in cambi)
    b = selection.build_briefing([same], [old], FONTI)
    assert b["doppioni"] and not b["verificate"] and not b["segnalazioni"]


# 6 ─ Bloccare l'approvazione quando manca la verifica di un dato fiscale essenziale
def test_6_blocco_dato_essenziale_non_verificato(tmp_path):
    d = bozza_valida()
    d["scheda"]["controlli"].append({"dato": "aliquota", "valore": "15%", "esito": "da_verificare", "essenziale": True})
    assert any("dato essenziale da verificare: aliquota" in m for m in gate.check(d, FONTI))
    d2 = bozza_valida()
    d2["scheda"]["controlli"][0]["fonte"] = "https://www.fiscoetasse.com/x"   # verificato solo sulla stampa
    assert any("senza fonte ufficiale" in m for m in gate.check(d2, FONTI))
    site = _site_copy(tmp_path)
    with pytest.raises(publish.PublishBlocked):
        publish.publish(d, site, FONTI)
    assert not os.path.exists(os.path.join(site, "news", d["slug"] + ".html"))


# 7 ─ Produrre il briefing senza articolo nei giorni senza novità rilevanti
def test_7_giorno_senza_articolo():
    b = selection.build_briefing([], [], FONTI)
    assert b["nessunaNovita"] is True
    assert selection.choose_for_article(b["verificate"], 1) == []
    minore = {"titolo": "Aggiornato un software di compilazione", "meritaArticolo": False, "impatto": 1,
              "fontiUfficiali": [{"url": GU, "aperta": True}]}
    b = selection.build_briefing([minore], [], FONTI)
    assert b["verificate"] and selection.choose_for_article(b["verificate"], 1) == []


# ─ Pubblicazione: pagina, indice e ritiro
def _site_copy(tmp_path):
    src = os.path.join(HERE, "..", "..", "site")
    dst = str(tmp_path / "site")
    shutil.copytree(src, dst)
    publish.write_index(dst, [])
    return dst


def test_pubblicazione_e_ritiro(tmp_path):
    site = _site_copy(tmp_path)
    d = bozza_valida()
    r = publish.publish(d, site, FONTI, today="2026-11-10")
    page = open(r["file"], encoding="utf-8").read()
    assert "<title>Decreto fiscale 2026: novità sui versamenti | TAX360</title>" in page
    assert 'href="../assets/style.css"' in page and 'rel="canonical"' in page
    assert "Entrata in vigore" in page and "1 luglio 2026" in page
    items, _ = publish.read_index(site)
    assert items[0]["slug"] == d["slug"] and items[0]["url"] == "news/" + d["slug"] + ".html"
    r2 = publish.publish(copy.deepcopy(d), site, FONTI, today="2026-11-12")      # stessa bozza: aggiorna, non duplica
    assert r2["aggiornato"] and len(publish.read_index(site)[0]) == 1
    assert "Aggiornato il 12 novembre 2026" in open(r2["file"], encoding="utf-8").read()
    publish.unpublish(d["slug"], site)
    assert publish.read_index(site)[0] == [] and not os.path.exists(r["file"])


def test_markdown_non_esegue_html():
    out = publish.md_to_html("Testo <script>alert(1)</script> e [x](javascript:alert(1))")
    assert "<script>" not in out and "javascript:" not in out

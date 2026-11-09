# TAX360 — sito e redazione News Fiscali

- `site/` — il sito tax360.it, pubblicato da Netlify ad ogni modifica di questo archivio.
- `tool/` — regole del sistema redazionale (domini ammessi, doppioni, blocco della pubblicazione
  senza verifica, copertura, generazione delle pagine articolo) e prove ripetibili (`cd tool && python -m pytest -q`).
- `tool/ISTRUZIONI_MOTORE.md` — procedimento seguito ogni mattina dall'attività programmata.
- `scrivania/redazione.html` — sorgente della Scrivania redazionale (pagina privata su claude.ai).

Gli articoli vengono pubblicati SOLO tramite `python -m tax360news publish`, che rifiuta
qualunque bozza con un dato fiscale essenziale non verificato su un documento ufficiale.

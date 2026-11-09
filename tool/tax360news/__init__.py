"""TAX360 — regole deterministiche del sistema redazionale News Fiscali.

Il lavoro di ricerca e scrittura lo svolge l'attività programmata (Claude);
questo pacchetto contiene le regole che NON devono dipendere dal giudizio del
modello e che sono coperte da prove ripetibili (tool/tests):

- domains   : solo domini approvati, anche dopo i reindirizzamenti
- dedup     : riconoscere doppioni e sviluppi sostanziali
- gate      : bloccare la pubblicazione se un dato essenziale non è verificato
- selection : smistare notizie (briefing / da verificare / candidate articolo)
- coverage  : dichiarare la copertura parziale quando una fonte non risponde
- publish   : generare la pagina articolo e aggiornare l'indice news del sito
"""

CATEGORIE = ("Normativa", "Agevolazioni", "Scadenze", "Approfondimenti")
STATI_ATTO = ("proposta", "pubblicato", "in_vigore", "in_attesa_attuazione", "prassi", "giurisprudenza")
STATI_BOZZA = ("da_verificare", "in_revisione", "approvato", "pubblicato", "da_ritirare", "ritirato")

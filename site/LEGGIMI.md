# TAX360 — Guida al sito

Sito vetrina di TAX360 Professional Advisory. Questa guida spiega come pubblicarlo online e come aggiornarne i contenuti.

---

## 1. Struttura dei file

```
tax360-site/
├── index.html          → Home
├── chisiamo.html       → Chi siamo (ex Lo Studio) + Founding Partner
├── enrico-assunto.html → Profilo Dott. Enrico Assunto
├── davide-spiniello.html → Profilo Dott. Davide Spiniello
├── servizi.html        → Servizi
├── contatti.html       → Contatti (recapiti + mini-form)
├── prenota.html        → Prenota consulenza (form)
├── news.html           → News fiscali
├── scadenziario.html   → Scadenziario fiscale 2026
├── _redirects          → reindirizza i vecchi link /studio verso /chisiamo (non eliminarlo)
└── assets/
    ├── style.css         → tutta la grafica (colori, font, layout)
    ├── main.js           → menu laterale, header, animazioni
    ├── logo-light.png    → logo per sfondi chiari
    ├── logo-dark.png     → logo per sfondi scuri
    ├── scadenze-2026.js  → dati dello scadenziario
    └── news.js           → dati delle news
```

**Importante:** i file `.html` e la cartella `assets/` devono restare sempre insieme. Se si separano, il sito perde tutta la grafica.

---

## 2. Mettere il sito online

Il modo più semplice e gratuito è Netlify:

1. Vai su netlify.com e registrati (gratis)
2. Trascina l'intera cartella `tax360-site` nella finestra "Deploy"
3. In pochi secondi il sito è online con un indirizzo provvisorio
4. Dalle impostazioni del dominio, collega `www.tax360.it` seguendo le istruzioni di Netlify

In alternativa: Vercel, GitHub Pages, oppure un hosting tradizionale (Aruba, SiteGround) caricando i file via FTP.

---

## 3. Form Prenotazione e Contatti — GIÀ CONFIGURATO

I due form (Prenota consulenza e mini-form Contatti) sono collegati a Formspree con l'endpoint dello studio.

**Prima messa online:** la prima volta che qualcuno invia un form, Formspree manda un'email di conferma all'indirizzo dello studio. Cliccare il link per attivare la ricezione.

Da quel momento, ogni richiesta arriva via email. Il piano gratuito gestisce 50 invii/mese.

Per cambiare l'indirizzo email di destinazione o vedere gli invii: accedere al pannello su formspree.io.

---

## 4. Aggiungere una NEWS

1. Aprire il file `assets/news.js`
2. Copiare il blocco di esempio (commentato in cima al file) dentro l'elenco `NEWS`, mettendo le news più recenti per prime
3. Compilare i campi: data, categoria, titolo, sintesi, e (facoltativi) fonte e link
4. Salvare e ricaricare il sito online

Categorie disponibili: Normativa, Agevolazioni, Scadenze, Approfondimenti.

Finché non ci sono news, la pagina mostra automaticamente un messaggio "Nessuna news al momento".

---

## 5. Aggiornare lo SCADENZIARIO

I dati sono nel file `assets/scadenze-2026.js`, organizzati mese per mese e facili da modificare.

Ogni voce ha: giorno, testo dell'adempimento, e categoria (per il colore).

Per l'anno nuovo: duplicare il file, rinominarlo (es. `scadenze-2027.js`) e aggiornare i dati e il riferimento dentro `scadenziario.html`.

I dati attuali coprono le **principali** scadenze 2026. Si consiglia una revisione professionale per integrare adempimenti specifici della clientela.

---

## 6. Cose ancora da completare

- **Cookie policy**: la mappa Google in Contatti si carica solo dopo il clic del visitatore; citarla comunque nella cookie policy.
- **Logo vettoriale**: i loghi attuali derivano da un PNG. Se si recupera il file vettoriale originale (SVG/AI/EPS), sostituire i due file in `assets/` per qualità ottimale a ogni dimensione.

---

## 7. Modifiche grafiche

Tutti i colori e gli stili sono centralizzati in `assets/style.css`, nella sezione `:root` in cima al file. Modificando lì un colore, il cambiamento si applica a tutto il sito.

Palette attuale:
- Navy: #1e3a5f
- Oro: #b8973e
- Grigio: #9a9a9a
- Carta (sfondo): #fbfaf7

"""Riga di comando usata dall'attività programmata.

  python -m tax360news url     <fonti.json> <url> [<url-redirect> ...]
  python -m tax360news briefing <fonti.json> <notizie.json> <storico.json> [limite]
  python -m tax360news gate     <fonti.json> <bozza.json>
  python -m tax360news coverage <fonti.json> <tentativi.json>
  python -m tax360news publish  <fonti.json> <bozza.json> <cartella-site>
  python -m tax360news unpublish <slug> <cartella-site>
  python -m tax360news key      <notizia.json>        (id stabile della notizia)

Ogni comando stampa JSON su stdout; codice di uscita 0 = ok, 2 = bloccato/rifiutato."""
import json
import sys

from . import coverage, domains, gate, publish, selection


def _load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    cmd, a = argv[0], argv[1:]
    out, code = None, 0
    if cmd == "url":
        ok, f, final = domains.check_final_url(a[1:], _load(a[0]))
        out = {"ammesso": ok, "urlFinale": final, "fonte": f}
        code = 0 if ok else 2
    elif cmd == "briefing":
        b = selection.build_briefing(_load(a[1]), _load(a[2]), _load(a[0]))
        lim = int(a[3]) if len(a) > 3 else 1
        b["candidateArticolo"] = selection.choose_for_article(b["verificate"], lim)
        out = b
    elif cmd == "gate":
        motivi = gate.check(_load(a[1]), _load(a[0]))
        out = {"pubblicabile": not motivi, "motivi": motivi}
        code = 0 if not motivi else 2
    elif cmd == "coverage":
        out = coverage.report(_load(a[1]), _load(a[0]))
    elif cmd == "publish":
        try:
            out = publish.publish(_load(a[1]), a[2], _load(a[0]))
        except publish.PublishBlocked as e:
            out, code = {"pubblicato": False, "motivi": str(e).split("; ")}, 2
    elif cmd == "unpublish":
        out = publish.unpublish(a[0], a[1])
    elif cmd == "key":
        import hashlib
        from . import dedup
        k = dedup.event_key(_load(a[0]))
        out = {"chiave": k, "id": "n-" + hashlib.sha1(k.encode("utf-8")).hexdigest()[:14]}
    else:
        print(__doc__)
        return 1
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

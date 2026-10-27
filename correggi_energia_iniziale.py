#!/usr/bin/env python3
"""
Corregge energia_iniziale_wh delle commesse sovrascritta da riconnessioni OPC UA.

Fino al fix di ottobre 2026, ad ogni riconnessione al PLC la prima lettura restituiva
tutti i tag a 0; la lettura successiva (CRX=N, CTX=0) veniva scambiata per un nuovo
avvio e l'energia iniziale riscritta col valore del momento, perdendo il consumo
già accumulato. Il valore vero è nei log CSV giornalieri: il contatore alla prima
riga con CRX=N (preferibilmente con CTX=0).

Uso:
    python correggi_energia_iniziale.py                 # solo anteprima
    python correggi_energia_iniziale.py --applica       # backup del DB + correzione
"""

import argparse
import csv
import datetime
import glob
import os
import sqlite3

from config import DATABASE_PATH, RAW_TO_KWH


def leggi_csv(cartella):
    righe = []
    for path in glob.glob(os.path.join(cartella, "data_*.log")):
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                try:
                    # La 'Z' dei log è ora locale, non UTC: va solo tolta
                    ts = datetime.datetime.fromisoformat(r["timestamp"].rstrip("Z"))
                    righe.append((ts, int(float(r["Commessa RX"])), int(float(r["Commessa TX"])),
                                  int(float(r["Potenza consumata TX"]))))
                except (KeyError, TypeError, ValueError):
                    continue
    righe.sort()
    return righe


def inizio_da_csv(righe, commessa):
    """Contatore energia al primo avvio della commessa nei log, o None."""
    candidate = [r for r in righe if r[1] == commessa and r[3] > 0]
    preferite = [r for r in candidate if r[2] == 0]
    scelta = (preferite or candidate or [None])[0]
    return (scelta[3], scelta[0]) if scelta else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=DATABASE_PATH)
    ap.add_argument("--csv-dir", default=".")
    ap.add_argument("--da-commessa", type=int, default=1000000)
    ap.add_argument("--applica", action="store_true")
    args = ap.parse_args()

    righe = leggi_csv(args.csv_dir)
    conn = sqlite3.connect(args.db)
    records = conn.execute('''
        SELECT rowid, commessa_tx, energia_iniziale_wh, energia_finale_wh, energia_consumata_wh, stato_lavorazione
        FROM telemetria WHERE commessa_tx >= ? ORDER BY commessa_tx
    ''', (args.da_commessa,)).fetchall()

    conteggio = {}
    for r in records:
        conteggio[r[1]] = conteggio.get(r[1], 0) + 1
    ultima = max(conteggio) if conteggio else None

    correzioni, finale_prec = [], None
    print(f"{'commessa':>9} {'stato':15} {'iniz_DB':>8} {'iniz_CSV':>8} {'finale':>8} {'kWh_prima':>9} {'kWh_dopo':>8}  note")
    for rowid, comm, iniz, fin, cons, stato in records:
        nota, nuova = "", None
        trovato = inizio_da_csv(righe, comm)
        if conteggio[comm] > 1:
            nota = "più record per la stessa commessa: ignorata"
        elif stato == "in_lavorazione" and comm != ultima:
            nota = "ORFANA: in lavorazione ma superata da commesse successive, non toccata"
        elif stato not in ("completata", "in_lavorazione"):
            nota = f"stato {stato}: non toccata"
        elif not trovato:
            nota = "nessun avvio nei CSV"
        elif trovato[0] >= iniz:
            nota = "ok"
        elif stato == "completata" and trovato[0] > fin:
            nota = "CSV oltre il finale: non toccata"
        elif finale_prec is not None and trovato[0] < finale_prec:
            nota = f"CSV prima del finale della precedente ({finale_prec}): non toccata"
        else:
            nuova = trovato[0]
            nota = f"DA CORREGGERE (avvio {trovato[1]:%Y-%m-%d %H:%M})"

        dopo = (fin - nuova if stato == "completata" else 0) if nuova is not None else cons
        print(f"{comm:>9} {stato:15} {iniz:>8} {(trovato[0] if trovato else '-'):>8} {fin:>8} "
              f"{cons / RAW_TO_KWH:>9.2f} {dopo / RAW_TO_KWH:>8.2f}  {nota}")
        if nuova is not None:
            correzioni.append((rowid, comm, stato, nuova, fin, iniz))
        if stato == "completata" and fin:
            finale_prec = fin

    recuperati = sum(c[5] - c[3] for c in correzioni)
    print(f"\nCommesse da correggere: {len(correzioni)}  —  energia recuperata: {recuperati / RAW_TO_KWH:.2f} kWh")

    if not args.applica:
        print("Anteprima: nessuna modifica. Rilanciare con --applica per scrivere.")
        return
    if not correzioni:
        return

    backup = f"{args.db}.bak-{datetime.datetime.now():%Y%m%d-%H%M%S}"
    dest = sqlite3.connect(backup)
    conn.backup(dest)
    dest.close()
    print(f"Backup: {backup}")

    with conn:
        for rowid, comm, stato, nuova, fin, _ in correzioni:
            if stato == "completata":
                conn.execute('UPDATE telemetria SET energia_iniziale_wh = ?, energia_consumata_wh = ? WHERE rowid = ?',
                             (nuova, fin - nuova, rowid))
            else:
                conn.execute('UPDATE telemetria SET energia_iniziale_wh = ? WHERE rowid = ?', (nuova, rowid))
    print(f"Corrette {len(correzioni)} commesse.")


if __name__ == "__main__":
    main()

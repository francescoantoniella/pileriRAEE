#!/bin/sh
# Comprime i log CSV giornalieri dei giorni passati (quello di oggi è ancora in scrittura).
# Report e script di correzione leggono anche i .log.gz.
# Installato come /etc/cron.daily/opc_logger_csv (gira come root, prima dell'inizio turno).
cd /home/pi/opc_logger || exit 1
oggi="data_$(date +%F).log"
for f in data_*.log; do
    [ -f "$f" ] && [ "$f" != "$oggi" ] && gzip -9 "$f"
done
exit 0

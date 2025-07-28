#!/bin/bash

echo "🧹 Pulizia ambiente virtuale per OPC Logger"
echo "=============================================="

echo "📦 Disinstallazione pacchetti non necessari..."
pip uninstall -y aiofiles aiohappyeyeballs aiohttp aiosignal aiosqlite async-timeout asyncua attrs cffi charset-normalizer cryptography frozenlist idna lxml multidict opcua pillow propcache pycparser pyOpenSSL python-dateutil pytz six sortedcontainers typing_extensions wait-for2 yarl

echo "✅ Installazione dipendenze essenziali..."
pip install -r requirements.txt

echo "🎉 Installazione completata!"
echo ""
echo "Dipendenze installate:"
pip list | grep -E "(bottle|reportlab)"

echo ""
echo "Per installare anche il supporto OPC UA, esegui:"
echo "pip install -r requirements-opcua.txt" 
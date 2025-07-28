#!/bin/bash

echo "🧹 Pulizia Directory OPC Logger"
echo "================================"

echo "📁 File da rimuovere:"
echo "  - __pycache__/ (file Python compilati)"
echo "  - test_standalone.py (file di test obsoleto)"
echo "  - opcua_reader_sim.py (simulatore obsoleto)"
echo "  - record.json (dati di test)"
echo "  - static/ (directory vuota)"

echo ""
echo "🗑️  Rimozione file..."

# Rimuovi __pycache__
if [ -d "__pycache__" ]; then
    rm -rf __pycache__
    echo "✅ Rimosso __pycache__/"
fi

# Rimuovi file di test obsoleti
if [ -f "test_standalone.py" ]; then
    rm test_standalone.py
    echo "✅ Rimosso test_standalone.py"
fi

if [ -f "opcua_reader_sim.py" ]; then
    rm opcua_reader_sim.py
    echo "✅ Rimosso opcua_reader_sim.py"
fi

# Rimuovi dati di test
if [ -f "record.json" ]; then
    rm record.json
    echo "✅ Rimosso record.json"
fi

# Rimuovi directory static vuota
if [ -d "static" ] && [ -z "$(ls -A static)" ]; then
    rmdir static
    echo "✅ Rimosso static/ (vuota)"
fi

echo ""
echo "📋 Contenuto finale della directory:"
ls -la

echo ""
echo "🎉 Pulizia completata!"
echo ""
echo "File essenziali mantenuti:"
echo "  ✅ server.py - Server principale"
echo "  ✅ db.py - Database"
echo "  ✅ config.py - Configurazione"
echo "  ✅ data_provider.py - Provider dati"
echo "  ✅ opcua_reader.py - Reader OPC UA"
echo "  ✅ templates/ - Template HTML"
echo "  ✅ requirements*.txt - Dipendenze"
echo "  ✅ README.md - Documentazione"
echo "  ✅ test_opcua.py - Test OPC UA"
echo "  ✅ clean_install.sh - Script pulizia"
echo "  ✅ telemetria.db - Database SQLite" 
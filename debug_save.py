"""
debug_save.py — Prueba cada capa del pipeline de guardado de forma aislada.
Ejecuta con: python debug_save.py
"""
import sys, os, json, requests

BASE_URL = "http://127.0.0.1:8000"
TEST_WORD = "debug_test_word_xyz"

def sep(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print('='*55)

# ─── 1. Servidor disponible ──────────────────────────────
sep("1. Verificando servidor Django")
try:
    r = requests.get(f"{BASE_URL}/", timeout=3)
    print(f"  ✓ Servidor responde: HTTP {r.status_code}")
except Exception as e:
    print(f"  ✗ Servidor NO responde: {e}")
    print("  → Arranca con: python manage.py runserver")
    sys.exit(1)

# ─── 2. Endpoint /save/ con JSON mínimo ──────────────────
sep("2. POST /save/ — payload mínimo")
payload = {'word': TEST_WORD, 'translation': 'palabra de prueba debug'}
try:
    r = requests.post(f"{BASE_URL}/save/", json=payload, timeout=5)
    print(f"  HTTP {r.status_code}")
    print(f"  Body: {r.text[:200]}")
    data = r.json()
    if data.get('status') in ('ok', 'duplicate'):
        print(f"  ✓ Backend OK: status='{data['status']}'")
    else:
        print(f"  ✗ Respuesta inesperada: {data}")
except Exception as e:
    print(f"  ✗ Error HTTP: {e}")

# ─── 3. Endpoint /save/ con payload completo ─────────────
sep("3. POST /save/ — payload completo (como el cliente envía)")
full_payload = {
    'word': TEST_WORD + "_full",
    'translation': 'prueba completa',
    'definition': 'definición de prueba',
    'phonetic': '/test/',
    'source_lang': 'en',
    'target_lang': 'es'
}
try:
    r = requests.post(f"{BASE_URL}/save/", json=full_payload, timeout=5)
    print(f"  HTTP {r.status_code}  →  {r.json()}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# ─── 4. api_client.save_flashcard() ─────────────────────
sep("4. VocabAPIClient.save_flashcard()")
sys.path.insert(0, 'desktop_client')
try:
    from api_client import VocabAPIClient
    api = VocabAPIClient()
    result = api.save_flashcard({
        'word': TEST_WORD + "_api",
        'translation': 'test api client',
        'source_lang': 'en',
        'target_lang': 'es'
    })
    print(f"  Resultado: {result}")
    if isinstance(result, dict) and result.get('status') in ('ok', 'duplicate'):
        print(f"  ✓ api_client OK")
    else:
        print(f"  ✗ Resultado inesperado — revisa api_client.py")
except Exception as e:
    print(f"  ✗ Error importando/usando api_client: {e}")

# ─── 5. Overlay signal (sin Qt event loop) ───────────────
sep("5. pyqtSignal save_requested — conexión directa")
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
    app = QApplication.instance() or QApplication(sys.argv)

    from overlay_ui import TranslationTooltip
    tooltip = TranslationTooltip()

    received = []
    tooltip.save_requested.connect(lambda d: received.append(d))

    # Simular exactamente lo que hace _on_save()
    tooltip._current_word = "signal_test"
    tooltip._word_data = {'word': 'signal_test', 'translation': 'test señal'}
    tooltip._on_save()   # ← debería emitir save_requested

    # Procesar events para que la señal llegue
    app.processEvents()

    if received:
        print(f"  ✓ save_requested emitida OK: {received[0]}")
    else:
        print(f"  ✗ save_requested NO llegó — revisa _on_save() en overlay_ui.py")

except Exception as e:
    print(f"  ✗ Error en test de señal Qt: {e}")
    import traceback; traceback.print_exc()

# ─── 6. Threading → QTimer marshal ──────────────────────
sep("6. threading.Thread + QTimer.singleShot(0) marshal")
try:
    import threading
    from PyQt6.QtCore import QTimer as QT

    results_from_thread = []

    def pretend_save():
        result = {'status': 'ok', 'message': 'mock save'}
        QT.singleShot(0, lambda r=result: results_from_thread.append(r))

    t = threading.Thread(target=pretend_save, daemon=True)
    t.start()
    t.join()
    # Give Qt event loop a tick
    for _ in range(10):
        app.processEvents()
        if results_from_thread:
            break
        import time; time.sleep(0.05)

    if results_from_thread:
        print(f"  ✓ Thread→Qt marshal OK: {results_from_thread[0]}")
    else:
        print(f"  ✗ Marshal FALLÓ — el callback nunca llegó al hilo principal")
        print(f"    Causa: QTimer.singleShot necesita event loop activo")

except Exception as e:
    print(f"  ✗ Error: {e}")

# ─── Resumen ─────────────────────────────────────────────
sep("RESUMEN")
print("  Si 1-4 son ✓ pero 5-6 fallan → el bug está en threading/señales Qt")
print("  Si 1-3 son ✓ pero 4 falla    → el bug está en api_client.py")
print("  Si 1-2 fallan                → el bug está en el servidor Django o CSRF")
print()

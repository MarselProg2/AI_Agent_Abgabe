import sys
import os
import asyncio
import json
from google.genai import types

# 1. Pfad Setup: 2 Ebenen hoch gehen (../../)
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(root_dir)

# 2. Importiere deinen ECHTEN Runner
try:
    from projekt_bosch.agent import runner
    print("✅ Modul 'projekt_bosch.agent' erfolgreich geladen.")
except ImportError as e:
    print(f"❌ FEHLER: Konnte 'projekt_bosch' nicht importieren. Pfad: {root_dir}")
    print(f"Detail: {e}")
    sys.exit(1)

async def run_single_test(test_case):
    """Führt einen einzelnen Testfall aus."""
    user_input = test_case['user_input']
    print(f"\n🔹 Test: {test_case['test_case_id']}")
    print(f"   Input: '{user_input}'")

    # --- WICHTIGE KORREKTUR HIER ---
    # Wir lesen den korrekten App-Namen direkt aus dem Runner aus.
    # In deiner agent.py ist das "root_agent".
    correct_app_name = getattr(runner, "app_name", "root_agent")

    # Session starten mit dem KORREKTEN App-Namen
    session = await runner.session_service.create_session(
        user_id='eval_bot', 
        app_name=correct_app_name
    )

    content = types.Content(role='user', parts=[types.Part(text=user_input)])

    # Agent ausführen
    print("   ⏳ Agent arbeitet (Google Search & DB)...")
    try:
        events = runner.run_async(
            user_id='eval_bot',
            session_id=session.id,
            new_message=content
        )
    except Exception as e:
        print(f"   ❌ START-FEHLER: {e}")
        return False

    final_text = ""
    found_text = False
    
    # Antwort Stream verarbeiten
    try:
        async for event in events:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    text = part.text
                    # Filterung: Wir wollen nur den finalen Markdown-Text, kein JSON
                    if text and not text.strip().startswith("{") and "search_metadata" not in text:
                        final_text = text
                        found_text = True
    except Exception as e:
        print(f"   ❌ CRITICAL ERROR während der Ausführung: {e}")
        return False

    if not found_text:
        print("   ⚠️  Warnung: Keine saubere Textantwort erhalten (nur JSON/Trace?).")
        # Optional: Gib den letzten Stand aus, falls vorhanden
        if final_text:
            print(f"   (Letzter Stand: {final_text[:300]}...)")
    
    # Überprüfung (Simple String Matching)
    expected_keywords = test_case.get('expected_output_contains', [])
    passed = True
    missing = []

    for keyword in expected_keywords:
        if keyword.lower() not in final_text.lower():
            passed = False
            missing.append(keyword)

    # Ergebnis Ausgabe
    print(f"   📝 Antwort-Vorschau: {final_text.replace(chr(10), ' ')[:300]}...")
    
    if passed:
        print("   ✅ STATUS: PASS")
    else:
        print("   ❌ STATUS: FAIL")
        print(f"      Fehlende Keywords: {missing}")

    return passed

async def main():
    print("🚀 Starte Manuellen Evaluierungs-Loop (Direct Runner Mode)")
    print("---------------------------------------------------------")
    
    # Lade die Testfälle
    json_path = os.path.join(os.path.dirname(__file__), "scenarios_test.json")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            test_cases = json.load(f)
    except FileNotFoundError:
        print(f"❌ Konnte Testdatei nicht finden: {json_path}")
        return

    # Loop durch alle Tests
    passed_count = 0
    for case in test_cases:
        if await run_single_test(case):
            passed_count += 1
            
    print("\n=========================================================")
    print(f"📊 GESAMTERGEBNIS: {passed_count}/{len(test_cases)} Tests bestanden.")
    print("=========================================================")

if __name__ == "__main__":
    asyncio.run(main())

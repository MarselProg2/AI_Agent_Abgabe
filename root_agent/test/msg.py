import sys
import os
import asyncio
import json
from google.genai import types
from dotenv import load_dotenv
import sys

# Windows Fix: Force UTF-8 output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# 1. Pfad Setup: 2 Ebenen hoch gehen (../../)
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(root_dir)

# 2. Importiere deinen ECHTEN Runner
try:
    from root_agent.agent import root_agent
    from google.adk import Runner
    from google.adk.sessions import InMemorySessionService
    from google.adk.apps import App
    
    # Wrap agent in App
    app = App(root_agent=root_agent, name="social_media_analytics_app")

    # Instantiate the runner with the app and session service
    runner = Runner(app=app, session_service=InMemorySessionService())
    print("[OK] Modul 'root_agent' erfolgreich geladen.")
except ImportError as e:
    print(f"[FAIL] FEHLER: Konnte 'root_agent' nicht importieren. Pfad: {root_dir}")
    print(f"Detail: {e}")
    sys.exit(1)

async def run_single_test(test_case):
    """Führt einen einzelnen Testfall aus."""
    user_input = test_case['user_input']
    print(f"\n[TEST] Test: {test_case['test_case_id']}")
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

    parts = [types.Part(text=user_input)]
    
    # Check for video file
    video_file = test_case.get('video_file')
    if video_file:
        video_path = os.path.join(os.path.dirname(__file__), video_file)
        # Fallback: check root dir if not found in test dir
        if not os.path.exists(video_path):
             video_path = os.path.join(root_dir, video_file)
             
        if os.path.exists(video_path):
            print(f"   [INFO] Loading video: {video_file}")
            try:
                with open(video_path, "rb") as f:
                    video_data = f.read()
                parts.append(types.Part.from_bytes(data=video_data, mime_type="video/mp4"))
            except Exception as e:
                print(f"   [FAIL] Could not load video: {e}")
        else:
            print(f"   [WARN] Video file not found: {video_file}")

    content = types.Content(role='user', parts=parts)

    # Agent ausführen
    print("   [WAIT] Agent arbeitet (Google Search )...")
    try:
        events = runner.run_async(
            user_id='eval_bot',
            session_id=session.id,
            new_message=content
        )
    except Exception as e:
        print(f"   [FAIL] START-FEHLER: {e}")
        return False

    all_texts = []  # Sammle ALLE Text-Parts aus ALLEN Events
    
    # Antwort Stream verarbeiten
    try:
        async for event in events:
            # Agent-Name loggen (falls vorhanden)
            agent_name = getattr(event, 'author', '')
            if event.content and event.content.parts:
                for part in event.content.parts:
                    text = part.text
                    if text:
                        # Prefix mit Agent-Name fuer bessere Zuordnung
                        if agent_name:
                            all_texts.append(f"[{agent_name}]: {text}")
                        else:
                            all_texts.append(text)
    except Exception as e:
        print(f"   [FAIL] CRITICAL ERROR während der Ausführung: {e}")
        return False

    # Alles zusammenfuegen
    final_text = "\n".join(all_texts)
    
    if not final_text.strip():
        print("   [WARN] Warnung: Keine Textantwort erhalten.")
    
    # Überprüfung (Simple String Matching)
    expected_keywords = test_case.get('expected_output_contains', [])
    passed = True
    missing = []

    for keyword in expected_keywords:
        if keyword.lower() not in final_text.lower():
            passed = False
            missing.append(keyword)

    # Ergebnis Ausgabe
    print(f"   [INFO] Antwort-Vorschau: {final_text.replace(chr(10), ' ')[:300]}...")
    
    if passed:
        print("   [OK] STATUS: PASS")
    else:
        print("   [FAIL] STATUS: FAIL")
        print(f"      Fehlende Keywords: {missing}")

    return passed

async def main():
    print("[START] Starte Manuellen Evaluierungs-Loop (Direct Runner Mode)")
    print("---------------------------------------------------------")
    
    # Lade die Testfälle
    # Lade die Testfälle
    json_path = os.path.join(os.path.dirname(__file__), "scenarios_debug.json")
    if not os.path.exists(json_path):
        json_path = os.path.join(os.path.dirname(__file__), "scenarios_test.json")
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            test_cases = json.load(f)
            print(f"[INFO] Loaded scenarios from: {os.path.basename(json_path)}")
    except FileNotFoundError:
        print(f"[FAIL] Konnte Testdatei nicht finden: {json_path}")
        return

    # Loop durch alle Tests
    passed_count = 0
    for case in test_cases:
        if await run_single_test(case):
            passed_count += 1
            
    print("\n=========================================================")
    print(f"[RESULT] GESAMTERGEBNIS: {passed_count}/{len(test_cases)} Tests bestanden.")
    print("=========================================================")

if __name__ == "__main__":
    asyncio.run(main())

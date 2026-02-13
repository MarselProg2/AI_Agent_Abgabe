import sys
import os
import asyncio
import json
from google.genai import types

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for API Key
if not os.getenv("GOOGLE_API_KEY"):
    print("[WARN] GOOGLE_API_KEY not found in environment variables or .env file.")
    print("       Please create a .env file with GOOGLE_API_KEY=your_api_key_here")

# 1. Path Setup: Go up 2 levels (../../)
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(root_dir)

# 2. Import your REAL Runner
try:
    from root_agent.agent import root_agent
    from google.adk import Runner
    # Check if InMemorySessionService is exposed at top level, otherwise import from subpackage
    try:
        from google.adk.sessions.in_memory_session_service import InMemorySessionService
    except ImportError:
         print("[WARN] Could not import InMemorySessionService from subpackage, trying top level...")
         from google.adk import InMemorySessionService # Fallback attempt
         
    print("[OK] Module 'root_agent' successfully loaded.")
except ImportError as e:
    print(f"[ERROR] Import Error. Path: {root_dir}")
    print(f"Detail: {e}")
    sys.exit(1)

# Initialize Runner
# Using InMemorySessionService for testing
session_service = InMemorySessionService()

# FIXED: Added app_name="root_agent" as required by Runner constructor when not providing an App instance
runner = Runner(agent=root_agent, app_name="root_agent", session_service=session_service)

async def run_single_test(test_case):
    """Executes a single test case."""
    user_input = test_case['user_input']
    test_id = test_case['test_case_id']
    expected = test_case.get('expected_check', {})

    print(f"\n[TEST]: {test_id}")
    print(f"   Input: '{user_input[:50]}...'")

    # Start Session
    try:
        session = await runner.session_service.create_session(
             app_name="root_agent",
             user_id='eval_bot'
        )
    except Exception as e:
         print(f"   [ERROR] Session Creation Failed: {e}")
         import traceback
         traceback.print_exc()
         return False

    context = user_input
    
    # Run Agent
    print("   [WAIT] Agent working (Video Analysis -> Strategy -> Creation -> Evaluation)...")
    try:
        # Run async
        content = types.Content(role="user", parts=[types.Part(text=context)])
        
        # Collect response from async generator
        response_text = ""
        final_payload = None
        
        async for event in runner.run_async(
            user_id='eval_bot',
            session_id=session.id,
            new_message=content
        ):
            # Accumulate text or check for final payload in event content
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        text = part.text.strip()
                        # print(f"   [DEBUG] Chunk: {text[:50]}...")
                        if text.startswith("{") and text.endswith("}"):
                             try:
                                 # Potentially valid JSON
                                 # We want the LAST valid JSON, or the one that has our target keys
                                 payload = json.loads(text)
                                 if "creative_output" in payload or "evaluation_result" in payload:
                                     final_payload = payload
                             except:
                                 pass
    except Exception as e:
        print(f"   [ERROR] Run Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    if not final_payload:
        print("   [WARN] No structured JSON response received in event stream.")
        return False

    # --- SMART GOAL VALIDATION ---
    print("   [CHECK] Validating SMART Goals...")
    passed = True
    
    evaluation = final_payload.get('evaluation_result')
    creative = final_payload.get('creative_output')
    
    if not creative:
         print("   [FAIL] No Creative Output generated.")
         passed = False
    else:
        # SMART Goal: Caption Length < 280
        caption = creative.get('caption', '')
        if len(caption) > 280:
             print(f"   [FAIL] Caption too long ({len(caption)} chars > 280).")
             passed = False
        else:
             print(f"   [PASS] Caption length ok ({len(caption)}).")
             
        # SMART Goal: Hashtags >= 5
        hashtags = creative.get('hashtags', [])
        if len(hashtags) < expected.get('min_hashtags', 5):
             print(f"   [FAIL] Too few hashtags ({len(hashtags)} < {expected.get('min_hashtags', 5)}).")
             passed = False
        else:
             print(f"   [PASS] Hashtag count ok ({len(hashtags)}).")

    # SMART Goal: Evaluator Score
    if evaluation:
        score = evaluation.get('overall_rating')
        if score:
            print(f"   [PASS] Content Evaluated (Score: {score}/10).")
            if score < 7:
                 print("   [WARN] Score < 7, but loop exited.")
        else:
             print("   [WARN] Evaluation record found but no score.")
    else:
         print("   [INFO] Note: No explicit 'evaluation_result' block in final output.")

    if passed:
        print("   [SUCCESS] ALL SMART GOALS MET")
    else:
        print("   [FAIL] SMART GOALS FAILED")

    return passed

async def main():
    print(">>> Starting InsightBench Evaluation (SMART Goals Check)")
    print("---------------------------------------------------------")
    
    json_path = os.path.join(os.path.dirname(__file__), "scenarios_test.json")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            test_cases = json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] Could not find test file: {json_path}")
        return

    passed_count = 0
    for case in test_cases:
        if await run_single_test(case):
            passed_count += 1
            
    print("\n=========================================================")
    print(f"TOTAL RESULT: {passed_count}/{len(test_cases)} Tests passed.")
    print("=========================================================")

if __name__ == "__main__":
    asyncio.run(main())
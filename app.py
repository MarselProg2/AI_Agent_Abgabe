import streamlit as st
import os
import json
import requests
import base64
from typing import Optional, Dict, Any
import uuid

try:
    import sseclient
except ImportError:
    sseclient = None

# --- Constants ---
# ADK Web Server uses SSE streaming at /run_sse
ADK_BASE_URL = "http://localhost:8000"

# --- Page Configuration ---
st.set_page_config(
    page_title="Social Media AI Booster",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS for Aesthetics ---
st.markdown("""
<style>
    .big-font {
        font-size:30px !important;
        font-weight: bold;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar: Configuration & Tools ---
with st.sidebar:
    # st.markdown("## ⚙️ Configuration")
    
    # # API Configuration
    # api_url = st.text_input("ADK Server URL", value=DEFAULT_API_URL, help="The URL of your running 'adk api_server'")
    
    # st.markdown("---")
    
    # Story 5: Engagement Calculator Inputs
    st.markdown("## 📈 Engagement Data")
    with st.expander("Input Stats", expanded=True):
        col_inp1, col_inp2 = st.columns(2)
        with col_inp1:
            likes = st.number_input("Likes", min_value=0, value=150)
            comments = st.number_input("Comments", min_value=0, value=45)
        with col_inp2:
            shares = st.number_input("Shares (3x)", min_value=0, value=10)
            saves = st.number_input("Saves (3x)", min_value=0, value=5)
            
        reach = st.number_input("Reach", min_value=1, value=1200)
        st.caption("Enter stats to let the agent calculate viral potential.")

# --- Main Area ---
st.title("🚀 Social Media AI Booster")
st.markdown("### Transform your video into viral content with Multi-Agent AI.")

# File Uploader (Visual only for now, unless we send path/content)
# File Uploader
uploaded_file = st.file_uploader("Upload Video Content", type=['mp4', 'mov'])

if uploaded_file:
    # Story: File Details
    file_details = {
        "Filename": uploaded_file.name,
        "FileType": uploaded_file.type,
        "FileSize": f"{uploaded_file.size / (1024 * 1024):.2f} MB"
    }
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Filename", file_details["Filename"])
    col2.metric("Size", file_details["FileSize"])
    col3.metric("Type", file_details["FileType"])
    
    st.divider()

# Helper to process SSE response stream
def process_sse_stream(response):
    """
    Parses the SSE stream from /run_sse endpoint.
    Collects all text parts from all events and returns the combined output.
    """
    all_texts = []
    last_author = ""
    
    for line in response.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        
        data_str = line[6:]  # Remove 'data: ' prefix
        if data_str.strip() == "[DONE]":
            break
            
        try:
            event = json.loads(data_str)
        except json.JSONDecodeError:
            continue
            
        # Extract author
        author = event.get("author", "")
        if author:
            last_author = author
            
        # Extract text from content.parts
        content = event.get("content", {})
        if not content:
            continue
        parts = content.get("parts", [])
        for part in parts:
            text = part.get("text", "")
            if text:
                all_texts.append({"author": last_author, "text": text})
    
    return all_texts


def build_structured_result(text_entries):
    """
    Groups SSE text entries by agent author.
    Returns a dict: { agent_name: combined_text, ... }
    This lets us display Creator output when Evaluator approved.
    """
    agent_outputs = {}
    
    for entry in text_entries:
        author = entry.get("author", "unknown")
        text = entry.get("text", "")
        if author not in agent_outputs:
            agent_outputs[author] = []
        agent_outputs[author].append(text)
    
    # Merge text per agent (keep last entry as the "final" output for that agent)
    result = {}
    for agent, texts in agent_outputs.items():
        # Try to parse all texts into JSON, keep last valid JSON as structured
        last_json = None
        for t in texts:
            try:
                parsed = json.loads(t.strip())
                if isinstance(parsed, dict):
                    last_json = parsed
            except (json.JSONDecodeError, AttributeError):
                pass
        
        result[agent] = {
            "full_text": "\n".join(texts),
            "structured": last_json
        }
    
    return result

# State Management
if "agent_result" not in st.session_state:
    st.session_state.agent_result = None

if uploaded_file:
    # Button to trigger agents
    if st.button("✨ Analyze & Boost", type="primary"):
        # Story 8: Spinner/Progress -> st.status
        with st.status("🚀 Processing Video...", expanded=True) as status:
            
            try:
                # Prepare Payload
                status.write("📝 Preparing data payload...")
                if "session_id" not in st.session_state:
                    st.session_state.session_id = str(uuid.uuid4())
                
                settings_app_name = "root_agent" 
                settings_user_id = "user"
                
                # --- Create Session ---
                create_session_url = f"{ADK_BASE_URL}/apps/{settings_app_name}/users/{settings_user_id}/sessions"
                
                # Use a new session for each analysis
                session_id = str(uuid.uuid4())
                st.session_state.session_id = session_id
                
                status.write(f"🔧 Creating session...")
                creation_payload = {"session_id": session_id}
                creation_response = requests.post(create_session_url, json=creation_payload, timeout=10)
                
                if creation_response.status_code not in [200, 201]:
                     status.warning(f"Session creation warning: {creation_response.status_code} - {creation_response.text}")
                else:
                     status.write("✅ Session registered.")

                # --- Build message parts ---
                status.write(f"📡 Sending to {settings_app_name} via SSE streaming...")
                
                user_text = (
                    f"Analyze the video content of the uploaded file: {uploaded_file.name}. "
                    f"Engagement Stats provided by user: Likes={likes}, Comments={comments}, "
                    f"Shares={shares}, Saves={saves}, Reach={reach}."
                )
                
                message_parts = [{"text": user_text}]
                
                # Upload actual video bytes as inline_data
                uploaded_file.seek(0)
                video_bytes = uploaded_file.read()
                video_b64 = base64.b64encode(video_bytes).decode("utf-8")
                message_parts.append({
                    "inline_data": {
                        "mime_type": uploaded_file.type or "video/mp4",
                        "data": video_b64
                    }
                })

                # --- Use /run_sse endpoint (SSE streaming) ---
                adk_run_url = f"{ADK_BASE_URL}/run_sse"
                
                payload = {
                    "app_name": settings_app_name, 
                    "user_id": settings_user_id,
                    "session_id": session_id,
                    "new_message": {
                        "role": "user",
                        "parts": message_parts
                    }
                }
                
                status.write("⏳ Agent pipeline is running (this may take 1-2 minutes)...")
                response = requests.post(adk_run_url, json=payload, stream=True, timeout=300)
                
                if response.status_code == 200:
                    # Parse SSE stream
                    text_entries = process_sse_stream(response)
                    
                    if text_entries:
                        status.write(f"✅ Received {len(text_entries)} responses from agents!")
                        result = build_structured_result(text_entries)
                        
                        # Also store raw entries for debug
                        st.session_state.agent_result = result
                        st.session_state.agent_raw = text_entries
                        
                        status.update(label="Analysis Complete!", state="complete", expanded=False)
                        st.toast("Analysis Complete!", icon="✅")
                    else:
                        status.update(label="No Response", state="error", expanded=True)
                        st.error("The agent pipeline returned no text output.")
                else:
                    status.update(label="API Error", state="error", expanded=True)
                    st.error(f"API Error: {response.status_code} - {response.text}")
                
            except requests.exceptions.ConnectionError:
                status.update(label="Connection Failed", state="error", expanded=True)
                st.error(f"Could not connect to ADK Server at `{ADK_BASE_URL}`. \n\nMake sure you are running: `uv run adk web`")
            except Exception as e:
                status.update(label="Error", state="error", expanded=True)
                st.error(f"An error occurred: {str(e)}")

# --- UI Display Logic ---
def display_agent_result(result: Any):
    """
    Renders the multi-agent pipeline result.
    result is a dict: { agent_name: { full_text, structured }, ... }
    """
    st.markdown("---")

    # --- Handle the grouped-by-agent dict ---
    if isinstance(result, dict) and any(k.endswith("_agent") or k == "unknown" for k in result.keys()):
        
        # Extract each agent's output
        video_data = result.get("video_analyst_agent", {})
        insight_data = result.get("insight_extractor_agent", {})
        creator_data = result.get("creator_agent", {})
        evaluator_data = result.get("evaluator_agent", {})
        
        creator_text = creator_data.get("full_text", "")
        evaluator_text = evaluator_data.get("full_text", "")
        video_json = video_data.get("structured")
        insight_json = insight_data.get("structured")
        
        # --- Check if Evaluator approved ---
        is_approved = False
        eval_rating = "?"
        if "APPROVED" in evaluator_text.upper():
            is_approved = True
        # Try to extract rating
        import re
        rating_match = re.search(r"Rating:\s*(\d+)/10", evaluator_text)
        if rating_match:
            eval_rating = rating_match.group(1)
        
        # ========== HEADER: Approval Status ==========
        if is_approved:
            st.success(f"✅ Content APPROVED by Evaluator Agent — Rating: {eval_rating}/10")
        else:
            st.warning(f"⚠️ Content NEEDS REVISION — Rating: {eval_rating}/10")
        
        # ========== TABS ==========
        tab_post, tab_eval, tab_analysis, tab_raw = st.tabs([
            "🎨 Empfehlung (Creator)", 
            "📋 Evaluation", 
            "🔬 Video-Analyse",
            "🔍 Debug"
        ])
        
        # --- TAB 1: Creator Output (Empfehlungsschreiben) ---
        with tab_post:
            if creator_text:
                st.subheader("� Creator Agent – Empfehlung")
                
                # Parse caption from Creator's markdown output
                caption = ""
                hashtags_section = ""
                strategy_section = ""
                trend_section = ""
                
                sections = creator_text.split("##")
                for section in sections:
                    section_lower = section.strip().lower()
                    if section_lower.startswith("caption"):
                        caption = section.split("\n", 1)[-1].strip() if "\n" in section else ""
                    elif section_lower.startswith("strategic hashtag"):
                        hashtags_section = section.split("\n", 1)[-1].strip() if "\n" in section else ""
                    elif section_lower.startswith("strategic justification"):
                        strategy_section = section.split("\n", 1)[-1].strip() if "\n" in section else ""
                    elif section_lower.startswith("trend"):
                        trend_section = section.split("\n", 1)[-1].strip() if "\n" in section else ""
                
                # Display Caption prominently
                if caption:
                    st.markdown("### 💬 Caption")
                    st.info(caption)
                
                col1, col2 = st.columns(2)
                
                # Display Hashtags
                with col1:
                    if hashtags_section:
                        st.markdown("### 🏷️ Hashtags & Strategie")
                        st.markdown(hashtags_section)
                
                # Display Trend Research
                with col2:
                    if trend_section:
                        st.markdown("### 📈 Trend Research")
                        st.markdown(trend_section)
                
                # Display Strategic Justification
                if strategy_section:
                    st.markdown("### 🧠 Strategische Begründung")
                    st.markdown(strategy_section)
                
                # Fallback: show full text if parsing didn't find sections
                if not caption and not hashtags_section:
                    st.markdown(creator_text)
            else:
                st.warning("Kein Creator Agent Output vorhanden.")
        
        # --- TAB 2: Evaluator Output ---
        with tab_eval:
            if evaluator_text:
                st.subheader("📋 Evaluator Agent – Bewertung")
                
                if is_approved:
                    st.success(f"**STATUS: APPROVED** — Rating: {eval_rating}/10")
                else:
                    st.error(f"**STATUS: NEEDS REVISION** — Rating: {eval_rating}/10")
                
                st.markdown(evaluator_text)
            else:
                st.warning("Kein Evaluator Output vorhanden.")
        
        # --- TAB 3: Video Analysis + Insights ---
        with tab_analysis:
            col_vid, col_ins = st.columns(2)
            
            with col_vid:
                st.subheader("🎬 Video Analyst")
                if video_json:
                    schema = video_json.get("schema_extraction", {})
                    st.metric("Hook Type", schema.get("hook_type", "N/A"))
                    st.metric("Scene Length", schema.get("scene_length", "N/A"))
                    st.metric("Visual Frequency", schema.get("visual_frequency", "N/A"))
                    st.markdown(f"**Unique Elements:** {schema.get('unique_visual_elements', 'N/A')}")
                    
                    root_qs = video_json.get("root_questions", [])
                    if root_qs:
                        st.markdown("**Root Questions:**")
                        for i, q in enumerate(root_qs, 1):
                            st.markdown(f"{i}. {q}")
                elif video_data.get("full_text"):
                    st.markdown(video_data["full_text"][:1000])
                else:
                    st.info("Keine Video-Analyse verfügbar.")
            
            with col_ins:
                st.subheader("� Insight Extractor")
                if insight_json:
                    st.metric("Most Engaging", insight_json.get("most_engaging_element", "N/A"))
                    st.markdown(f"**Hook Strategy:** {insight_json.get('hook_strategy', 'N/A')}")
                    st.markdown(f"**Psychological Angle:** {insight_json.get('psychological_angle', 'N/A')}")
                    st.markdown(f"**Prescriptive Summary:** {insight_json.get('prescriptive_summary', 'N/A')}")
                elif insight_data.get("full_text"):
                    st.markdown(insight_data["full_text"][:1000])
                else:
                    st.info("Keine Insights verfügbar.")
        
        # --- TAB 4: Debug Raw ---
        with tab_raw:
            st.json(result)
        
        return
    
    # ========== FALLBACK for old-style results ==========
    st.subheader("🤖 Agent Response")
    if isinstance(result, dict):
        st.json(result)
    elif isinstance(result, str):
        st.markdown(result)
    else:
        st.json(result)

# Display Results
if st.session_state.agent_result:
    display_agent_result(st.session_state.agent_result)
    
elif not uploaded_file:
    st.info("👆 Please upload a video file to begin.")

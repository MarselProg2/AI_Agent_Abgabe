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
    Tries to parse the collected text entries into a structured result
    for display in the UI.
    """
    # Combine all texts
    combined = "\n".join([e["text"] for e in text_entries])
    
    # Try to find a JSON object in the last entries (usually the final output)
    for entry in reversed(text_entries):
        text = entry["text"].strip()
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                parsed["_author"] = entry["author"]
                return parsed
        except (json.JSONDecodeError, AttributeError):
            continue
    
    # Fallback: return combined text
    return combined

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
    Renders the agent result in a beautiful, structured way.
    Handles both structured JSON (from Creator Agent) and raw strings (Chain of Thought).
    """
    st.markdown("---")
    st.subheader("🎉 Agent Output")

    # CASE A: Structured JSON (Creator Agent)
    if isinstance(result, dict) and "caption" in result:
        tab_creator, tab_raw = st.tabs(["🎨 The Post", "🔍 Debug Data"])
        
        with tab_creator:
            st.markdown("### 📝 Generated Caption")
            st.info(result.get("caption", "No caption generated."))
            
            col_meta1, col_meta2 = st.columns(2)
            
            # Engagement / Analysis
            with col_meta1:
                # Try to find analysis data loosely
                analysis = result.get("engagement_analysis") or result.get("video_analysis", {}).get("engagement_analysis")
                if analysis:
                    st.markdown("#### 📊 Analysis")
                    score = analysis.get("rate", 0)
                    verdict = analysis.get("assessment", "N/A")
                    st.metric("Viral Score", f"{score}/10", delta=verdict)
            
            # Hashtags
            with col_meta2:
                if "hashtags" in result:
                    st.markdown("#### 🏷️ Hashtags")
                    tags = result["hashtags"]
                    if isinstance(tags, list):
                        st.write(", ".join([f"`#{t}`" for t in tags]))
                    else:
                        st.markdown(str(tags))

            # Posting Times (if available)
            if "posting_times" in result:
                st.markdown("#### ⏰ Best Posting Times")
                times = result["posting_times"]
                if isinstance(times, list):
                    cols = st.columns(len(times)) if len(times) <= 4 else st.columns(4)
                    for idx, slot in enumerate(times):
                        if isinstance(slot, dict):
                            with cols[idx % 4]:
                                st.markdown(f"**{slot.get('time', 'N/A')}**")
                                st.caption(slot.get('reason', ''))
                else:
                    st.info(str(times))

        with tab_raw:
            st.json(result)

    # CASE B: String Output (Likely with <thinking_process>)
    elif isinstance(result, str):
        # 1. Extract Thinking Process
        thinking_content = ""
        final_content = result
        
        if "<thinking_process>" in result:
            parts = result.split("</thinking_process>")
            if len(parts) > 1:
                think_part = parts[0].split("<thinking_process>")[-1]
                thinking_content = think_part.strip()
                final_content = parts[1].strip()
            else:
                # Tag opened but maybe not closed properly, or just one block
                thinking_content = result.replace("<thinking_process>", "").strip()
                final_content = "" # Nothing else?

        # Display Thinking Process in Expander
        if thinking_content:
            with st.expander("🧠 View Agent Thought Process (Click to expand)", expanded=False):
                st.markdown(thinking_content)

        # Display Final Content
        if final_content:
            st.markdown("### 🤖 Agent Response")
            st.markdown(final_content)
        elif not thinking_content:
            # Fallback if parsing failed strangely
            st.warning("Raw Output:")
            st.text(result)

    # CASE C: Fallback (Other Dicts/Lists)
    else:
        st.subheader("📄 Result Data")
        st.json(result)

# Display Results
if st.session_state.agent_result:
    display_agent_result(st.session_state.agent_result)
    
    # Show raw agent responses in debug
    if "agent_raw" in st.session_state and st.session_state.agent_raw:
        with st.expander("🔍 Raw Agent Responses (Debug)", expanded=False):
            for entry in st.session_state.agent_raw:
                author = entry.get("author", "unknown")
                text = entry.get("text", "")
                st.markdown(f"**[{author}]:**")
                # Try to pretty-print JSON
                try:
                    parsed = json.loads(text)
                    st.json(parsed)
                except (json.JSONDecodeError, TypeError):
                    st.text(text[:500])
                st.markdown("---")
            
elif not uploaded_file:
    st.info("👆 Please upload a video file to begin.")

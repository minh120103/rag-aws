# frontend.py
import streamlit as st
import requests
import uuid
from datetime import datetime
import json
import os
import pickle

st.set_page_config(page_title="🎬 RAG Movie Assistant", page_icon="🎥", layout="wide")

# Custom CSS for better styling
st.markdown("""
<style>
.session-info {
    background-color: #f0f2f6;
    padding: 10px;
    border-radius: 5px;
    margin: 10px 0;
}
.chat-message {
    padding: 10px;
    margin: 5px 0;
    border-radius: 10px;
    color: #2c3e50;
}
.user-message {
    background-color: #f8f9fa;
    border-left: 4px solid #007bff;
    color: #212529;
}
.assistant-message {
    background-color: #f1f3f4;
    border-left: 4px solid #6f42c1;
    color: #212529;
}
</style>
""", unsafe_allow_html=True)

st.title("🎬 Ask the Movie Assistant")

# Create data directory for persistence
DATA_DIR = "chat_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.pkl")

def load_sessions():
    """Load sessions from file"""
    try:
        if os.path.exists(SESSIONS_FILE):
            with open(SESSIONS_FILE, 'rb') as f:
                return pickle.load(f)
        return {}
    except Exception as e:
        st.error(f"Error loading sessions: {e}")
        return {}

def save_sessions(sessions):
    """Save sessions to file"""
    try:
        with open(SESSIONS_FILE, 'wb') as f:
            pickle.dump(sessions, f)
    except Exception as e:
        st.error(f"Error saving sessions: {e}")

def save_current_session():
    """Save current session to persistent storage"""
    if st.session_state.chat_history:
        sessions = load_sessions()
        sessions[st.session_state.thread_id] = {
            "chat_history": st.session_state.chat_history.copy(),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message_count": len(st.session_state.chat_history)
        }
        save_sessions(sessions)

def get_most_recent_session():
    """Get the most recent session with chat history"""
    sessions = load_sessions()
    if not sessions:
        return None, None
    
    # Filter sessions with chat history and sort by creation time
    sessions_with_history = {
        sid: data for sid, data in sessions.items() 
        if data.get('chat_history') and len(data['chat_history']) > 0
    }
    
    if not sessions_with_history:
        return None, None
    
    # Sort by created_at timestamp (most recent first)
    most_recent_id = max(sessions_with_history.keys(), 
                        key=lambda x: sessions_with_history[x]['created_at'])
    
    return most_recent_id, sessions_with_history[most_recent_id]

# Initialize session state with auto-load
if "thread_id" not in st.session_state:
    # Try to load the most recent session
    recent_id, recent_data = get_most_recent_session()
    
    if recent_id and recent_data:
        st.session_state.thread_id = recent_id
        st.session_state.chat_history = recent_data['chat_history'].copy()
        st.info(f"🔄 Loaded most recent session ({recent_data['message_count']} messages)")
    else:
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.chat_history = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "all_sessions" not in st.session_state:
    st.session_state.all_sessions = load_sessions()

# Sidebar for session management
with st.sidebar:
    st.header("🗂️ Session Management")
    
    # Current session info
    st.subheader("Current Session")
    st.text(f"ID: {st.session_state.thread_id[:8]}...")
    if st.session_state.chat_history:
        st.text(f"Messages: {len(st.session_state.chat_history)}")
    
    # New session button
    if st.button("🆕 New Session"):
        # Save current session before creating new one
        save_current_session()
        st.session_state.all_sessions = load_sessions()
        
        # Create new session
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.chat_history = []
        st.rerun()
    
    st.divider()
    
    # Previous sessions
    st.subheader("📚 Previous Sessions")
    # Reload sessions from file to get latest data
    current_sessions = load_sessions()
    
    if current_sessions:
        # Sort sessions by creation time (most recent first)
        sorted_sessions = sorted(current_sessions.items(), 
                               key=lambda x: x[1]['created_at'], reverse=True)
        
        for session_id, session_data in sorted_sessions:
            if session_id != st.session_state.thread_id:  # Don't show current session
                is_recent = session_id == get_most_recent_session()[0]
                title_prefix = "🔥 " if is_recent else ""
                
                with st.expander(f"{title_prefix}Session {session_id[:8]}... ({session_data['message_count']} msgs)"):
                    st.text(f"Created: {session_data['created_at']}")
                    if st.button(f"Load Session", key=f"load_{session_id}"):
                        # Save current session first
                        save_current_session()
                        
                        # Load selected session
                        st.session_state.thread_id = session_id
                        st.session_state.chat_history = session_data['chat_history'].copy()
                        st.session_state.all_sessions = load_sessions()
                        st.rerun()
    else:
        st.info("No previous sessions")

# Main chat interface
st.subheader("💬 Chat Interface")

# Input form
with st.form("chat_form"):
    question = st.text_area("Enter your question:", height=100, placeholder="Ask me about movies...")
    submitted = st.form_submit_button("🚀 Ask", use_container_width=True)

if submitted:
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("🤔 Thinking..."):
            try:
                response = requests.post(
                    "http://localhost:8000/api/chat",
                    json={
                        "thread_id": st.session_state.thread_id,
                        "question": question.strip()
                    },
                    timeout=300
                )
                
                if response.status_code == 200:
                    result = response.json()
                    answer = result["answer"]
                    route = result.get("route", "unknown")
                    
                    # Add to chat history
                    st.session_state.chat_history.append((question.strip(), answer))
                    
                    # Save to persistent storage immediately
                    save_current_session()
                    
                    # Show route info
                    route_colors = {
                        "sql": "🗃️",
                        "vector": "🔍", 
                        "general": "💭",
                        "error": "❌"
                    }
                    st.success(f"Response generated via {route_colors.get(route, '❓')} {route} route")
                    
                    st.rerun()
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.Timeout:
                st.error("Request timed out. Please try again.")
            except Exception as e:
                st.error(f"Request failed: {e}")

# Chat history display
if st.session_state.chat_history:
    st.subheader("📝 Conversation History")
    
    # Option to show/hide full history
    show_full_history = st.checkbox("Show full history", value=True)
    
    if show_full_history:
        display_history = st.session_state.chat_history
    else:
        display_history = st.session_state.chat_history[-5:]  # Show last 5 only
    
    # Display messages
    for i, (q, a) in enumerate(reversed(display_history)):
        st.markdown(f"""
        <div class="chat-message user-message">
        <strong>🧑 You:</strong> {q}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="chat-message assistant-message">
        <strong>🤖 Assistant:</strong> {a}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
    
    # Export option
    if st.button("📤 Export Chat History"):
        export_data = {
            "thread_id": st.session_state.thread_id,
            "exported_at": datetime.now().isoformat(),
            "chat_history": st.session_state.chat_history
        }
        
        st.download_button(
            label="💾 Download as JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"chat_history_{st.session_state.thread_id[:8]}.json",
            mime="application/json"
        )

else:
    st.info("👋 Start a conversation by asking a question above!")

# Health check in footer
with st.expander("🏥 System Health"):
    if st.button("Check Backend Health"):
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                st.success("✅ Backend is healthy!")
                st.json(health_data)
            else:
                st.error("❌ Backend health check failed")
        except Exception as e:
            st.error(f"❌ Cannot connect to backend: {e}")

# Auto-save on app close (save current session when page is refreshed/closed)
if st.session_state.chat_history:
    save_current_session()
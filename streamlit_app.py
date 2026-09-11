"""
RULER — Banking Regulatory RAG Platform
Production-Grade Streamlit UI for Retrieval-Augmented Generation (RAG)

Features:
- Interactive Q&A with grounded answers from retrieved documents
- Source attribution with chunk details and character-span verification
- Citation inspection with highlighted source text
- Token usage tracking and session management
- Error handling and fallback states
- Beautiful, responsive UI with professional design
"""

import streamlit as st
import requests
import json
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import sys
import os

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"
API_TIMEOUT = 30

# ============================================================================
# PAGE CONFIGURATION & STYLING
# ============================================================================

st.set_page_config(
    page_title="Ruler - Banking Regulatory RAG",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Main container and layout */
    .main {
        padding: 0rem 1rem;
    }
    
    /* Chat message styling */
    .chat-message-container {
        display: flex;
        flex-direction: column;
        margin-bottom: 1.5rem;
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
    }
    
    .chat-message-user {
        background-color: #e3f2fd;
        border-left: 4px solid #1976d2;
    }
    
    .chat-message-assistant {
        background-color: #f5f5f5;
        border-left: 4px solid #388e3c;
    }
    
    .chat-message-header {
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .chat-message-user .chat-message-header {
        color: #1976d2;
    }
    
    .chat-message-assistant .chat-message-header {
        color: #388e3c;
    }
    
    /* Citation styling */
    .citation {
        display: inline-block;
        background-color: #fff3e0;
        color: #e65100;
        padding: 0.1rem 0.4rem;
        border-radius: 0.25rem;
        font-weight: 600;
        font-size: 0.85em;
        margin: 0 0.2rem;
        cursor: pointer;
        border: 1px solid #ffb74d;
    }
    
    .citation:hover {
        background-color: #ffe0b2;
    }
    
    /* Source cards */
    .source-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    
    .source-card:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.12);
        border-color: #bbdefb;
    }
    
    .source-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    .source-badge {
        background-color: #e3f2fd;
        color: #1565c0;
        padding: 0.25rem 0.75rem;
        border-radius: 0.25rem;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .source-metadata {
        font-size: 0.85rem;
        color: #666;
        margin-top: 0.5rem;
    }
    
    .source-metadata-item {
        display: inline-block;
        margin-right: 1rem;
    }
    
    .source-text {
        background-color: #fafafa;
        border-left: 3px solid #ffb74d;
        padding: 0.75rem;
        margin-top: 0.75rem;
        font-size: 0.9rem;
        line-height: 1.6;
        font-family: "Monaco", "Menlo", "Ubuntu Mono", monospace;
        border-radius: 0.25rem;
    }
    
    /* Loading and error states */
    .loading-spinner {
        text-align: center;
        padding: 1rem;
    }
    
    .error-message {
        background-color: #ffebee;
        border-left: 4px solid #d32f2f;
        padding: 1rem;
        border-radius: 0.5rem;
        color: #c62828;
        margin: 1rem 0;
    }
    
    .warning-message {
        background-color: #fff3e0;
        border-left: 4px solid #f57c00;
        padding: 1rem;
        border-radius: 0.5rem;
        color: #e65100;
        margin: 1rem 0;
    }
    
    .success-message {
        background-color: #e8f5e9;
        border-left: 4px solid #2e7d32;
        padding: 1rem;
        border-radius: 0.5rem;
        color: #1b5e20;
        margin: 1rem 0;
    }
    
    /* Status indicators */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .status-online {
        background-color: #e8f5e9;
        color: #2e7d32;
    }
    
    .status-offline {
        background-color: #ffebee;
        color: #d32f2f;
    }
    
    .status-warning {
        background-color: #fff3e0;
        color: #f57c00;
    }
    
    /* Token counter */
    .token-info {
        background-color: #f5f5f5;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-size: 0.85rem;
        color: #666;
        margin-top: 0.5rem;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f5f5f5;
        border: 1px solid #e0e0e0;
    }
    
    /* Help text and tips */
    .help-box {
        background-color: #e3f2fd;
        border-left: 3px solid #1976d2;
        padding: 0.75rem;
        border-radius: 0.25rem;
        font-size: 0.9rem;
        color: #1565c0;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """Initialize session state variables."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "total_tokens_used" not in st.session_state:
        st.session_state.total_tokens_used = 0
    
    if "api_status" not in st.session_state:
        st.session_state.api_status = {"status": "unknown", "model_name": "loading..."}
    
    if "expanded_sources" not in st.session_state:
        st.session_state.expanded_sources = {}
    
    if "last_error" not in st.session_state:
        st.session_state.last_error = None
    
    if "show_debug" not in st.session_state:
        st.session_state.show_debug = False

initialize_session_state()

# ============================================================================
# API INTERACTION FUNCTIONS
# ============================================================================

def check_api_status() -> Tuple[bool, Dict]:
    """Check if the backend API is available and get status."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/status",
            timeout=5
        )
        if response.status_code == 200:
            status = response.json()
            st.session_state.api_status = status
            return True, status
        else:
            return False, {"error": f"API returned status {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return False, {"error": "Cannot connect to API server"}
    except requests.exceptions.Timeout:
        return False, {"error": "API server timeout"}
    except Exception as e:
        return False, {"error": str(e)}


def query_rag_api(question: str, use_mock: bool = False) -> Tuple[bool, Dict, Optional[str]]:
    """
    Send a question to the RAG backend API and get a grounded answer.
    
    Returns:
        Tuple of (success: bool, response_data: dict, error_message: str or None)
    """
    try:
        payload = {
            "user_message": question,
            "system_role": "Banking Regulatory Compliance Assistant",
            "required_fields": ["answer", "source", "confidence"],
            "temperature": 0.2,
            "use_mock": use_mock
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/chat",
            json=payload,
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                # Update token usage
                usage = data.get("token_usage", {})
                total_tokens = usage.get("total_tokens", 0)
                st.session_state.total_tokens_used += total_tokens
                
                return True, data, None
            else:
                return False, {}, "API returned unsuccessful response"
        else:
            return False, {}, f"API error: {response.status_code}"
    
    except requests.exceptions.Timeout:
        return False, {}, "API request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return False, {}, "Cannot connect to the backend API. Is the server running?"
    except json.JSONDecodeError:
        return False, {}, "Invalid API response format"
    except Exception as e:
        return False, {}, f"Unexpected error: {str(e)}"


# ============================================================================
# UI HELPER FUNCTIONS
# ============================================================================

def format_citation_text(text: str, citations: List[Dict]) -> str:
    """Format answer text with interactive citation markers."""
    # Parse and format citations in the text
    formatted_text = text
    for i, citation in enumerate(citations, start=1):
        marker = f"[{i}]"
        if marker not in formatted_text:
            # If citation marker not in text, add it at a reasonable position
            pass
    return formatted_text


def render_source_card(source: Dict, citation_index: int):
    """Render a single source card with metadata and highlighted text."""
    with st.container():
        col1, col2 = st.columns([0.85, 0.15])
        
        with col1:
            # Source header with badge and filename
            st.markdown(f"""
            <div class="source-header">
                <span class="source-badge">📄 Source [{citation_index}]</span>
                <strong>{source.get('filename', 'Unknown')}</strong>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Toggle for detailed metadata
            expand_key = f"source_{citation_index}"
            if st.button(f"Details", key=f"btn_{expand_key}", use_container_width=True):
                st.session_state.expanded_sources[expand_key] = not st.session_state.expanded_sources.get(expand_key, False)
        
        # Source metadata (Document ID, Section, Page, etc.)
        metadata_parts = []
        
        if source.get("doc_id"):
            metadata_parts.append(f"📋 **Doc ID:** `{source['doc_id']}`")
        
        if source.get("section"):
            metadata_parts.append(f"🏷️ **Section:** {source['section']}")
        
        if source.get("page_number"):
            metadata_parts.append(f"📄 **Page:** {source['page_number']}")
        
        if source.get("chunk_id"):
            metadata_parts.append(f"🔗 **Chunk ID:** `{source['chunk_id']}`")
        
        if metadata_parts:
            st.markdown("""
            <div class="source-metadata">
            """ + " | ".join(metadata_parts) + """
            </div>
            """, unsafe_allow_html=True)
        
        # Highlighted source text
        source_text = source.get("raw_text", "No text available")
        if len(source_text) > 500:
            source_text = source_text[:500] + "..."
        
        st.markdown(f"""
        <div class="source-text">
        {source_text}
        </div>
        """, unsafe_allow_html=True)
        
        # Expanded detailed metadata
        expand_key = f"source_{citation_index}"
        if st.session_state.expanded_sources.get(expand_key, False):
            st.markdown("---")
            
            # Detailed metadata in columns
            meta_col1, meta_col2 = st.columns(2)
            
            with meta_col1:
                st.markdown("**Metadata Details**")
                if source.get("start_char") is not None:
                    st.text(f"Character Span: {source['start_char']}-{source['end_char']}")
                if source.get("chunk_index") is not None:
                    st.text(f"Chunk Index: {source['chunk_index']}")
                if source.get("source_path"):
                    st.text(f"Path: {source['source_path']}")
            
            with meta_col2:
                st.markdown("**Full Text Preview**")
                with st.expander("Show full source text"):
                    st.code(source.get("raw_text", "No text available"))


def render_chat_message(message: Dict):
    """Render a single chat message in the conversation."""
    role = message.get("role", "user").lower()
    content = message.get("content", "")
    timestamp = message.get("timestamp", "")
    
    if role == "user":
        st.markdown(f"""
        <div class="chat-message-container chat-message-user">
            <div class="chat-message-header">👤 You</div>
            <div>{content}</div>
            {f'<div class="token-info">📅 {timestamp}</div>' if timestamp else ''}
        </div>
        """, unsafe_allow_html=True)
    
    elif role == "assistant":
        citations = message.get("citations", [])
        is_grounded = message.get("is_grounded", False)
        confidence = message.get("confidence", "medium")
        token_usage = message.get("token_usage", {})
        
        # Status indicator
        grounding_status = "✅ Grounded" if is_grounded else "⚠️ No Sources"
        grounding_color = "#2e7d32" if is_grounded else "#f57c00"
        
        st.markdown(f"""
        <div class="chat-message-container chat-message-assistant">
            <div class="chat-message-header">🤖 Regulatory Assistant</div>
            <div style="margin-bottom: 0.5rem; color: {grounding_color}; font-weight: 600;">
                {grounding_status}
            </div>
            <div style="margin-bottom: 1rem; line-height: 1.6;">{content}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Token usage info
        if token_usage:
            st.markdown(f"""
            <div class="token-info">
                ⚡ Tokens - Prompt: {token_usage.get('prompt_tokens', 0)} | 
                Completion: {token_usage.get('completion_tokens', 0)} | 
                Total: {token_usage.get('total_tokens', 0)}
            </div>
            """, unsafe_allow_html=True)
        
        # Display sources if citations exist
        if citations:
            st.markdown("---")
            st.markdown("### 📚 Retrieved Sources")
            
            for idx, citation in enumerate(citations, start=1):
                with st.container():
                    render_source_card(citation, idx)
                    if idx < len(citations):
                        st.markdown("")
        elif message.get("citation_status") == "NO_RETRIEVED_SOURCES":
            st.warning("⚠️ No relevant sources were found for this query. The answer may be less grounded.")
        
        if timestamp:
            st.markdown(f'<div class="token-info">📅 {timestamp}</div>', unsafe_allow_html=True)


# ============================================================================
# MAIN UI COMPONENTS
# ============================================================================

def render_header():
    """Render the main header with branding and status."""
    col1, col2, col3 = st.columns([0.4, 0.3, 0.3])
    
    with col1:
        st.markdown("# ⚖️ RULER")
        st.markdown("Banking Regulatory RAG Platform")
    
    with col3:
        # API Status indicator
        is_online, status = check_api_status()
        
        if is_online:
            status_class = "status-online"
            status_text = "🟢 API Online"
        else:
            status_class = "status-offline"
            status_text = "🔴 API Offline"
        
        st.markdown(f"""
        <div style="text-align: right;">
            <div class="status-badge {status_class}">{status_text}</div>
            <div style="font-size: 0.85rem; color: #666; margin-top: 0.5rem;">
                <strong>Model:</strong> {status.get('model_name', 'Unknown')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")


def render_sidebar():
    """Render the sidebar with controls and information."""
    with st.sidebar:
        st.markdown("### 🎛️ Controls")
        
        # Session info
        st.markdown("**Session Information**")
        st.metric("Total Tokens Used", st.session_state.total_tokens_used)
        st.metric("Messages in Chat", len(st.session_state.chat_history))
        
        st.markdown("---")
        
        # Clear chat history
        if st.button("🔄 Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.total_tokens_used = 0
            st.rerun()
        
        # Debug mode toggle
        st.markdown("---")
        st.markdown("### 🔧 Settings")
        st.session_state.show_debug = st.checkbox("Show Debug Information", value=False)
        
        st.markdown("---")
        
        # About section
        st.markdown("### ℹ️ About")
        st.markdown("""
        **Ruler** is a production-grade Retrieval-Augmented Generation (RAG) platform 
        designed for banking regulatory compliance.
        
        ✨ **Features:**
        - Grounded answers with source attribution
        - Citation verification with character spans
        - Real-time token usage tracking
        - Professional UI with error handling
        
        📖 **Documentation:**
        - [Backend API Docs](#) (coming soon)
        - [User Guide](#) (coming soon)
        """)


def render_chat_interface():
    """Render the main chat interface."""
    st.markdown("### 💬 Ask a Regulatory Question")
    
    # Example questions
    example_questions = [
        "What are the AML (Anti-Money Laundering) requirements?",
        "Explain Basel IV Liquidity requirements",
        "What are the payment threshold regulations?",
        "What compliance thresholds apply to my institution?",
    ]
    
    with st.expander("📌 Example Questions", expanded=False):
        for example in example_questions:
            if st.button(f"💡 {example}", use_container_width=True, key=f"example_{example[:20]}"):
                st.session_state.current_question = example
                st.rerun()
    
    st.markdown("---")
    
    # Chat input area
    col1, col2 = st.columns([0.9, 0.1])
    
    with col1:
        user_question = st.text_input(
            "Your question:",
            placeholder="Ask about regulatory requirements, compliance, thresholds, etc.",
            label_visibility="collapsed"
        )
    
    with col2:
        submit_button = st.button("📤 Send", use_container_width=True)
    
    # Process user input
    if submit_button and user_question:
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_question,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Call API with loading state
        with st.spinner("🔄 Retrieving documents and generating answer..."):
            time.sleep(0.5)  # Brief delay for UX
            success, response_data, error_msg = query_rag_api(user_question)
        
        if success:
            # Extract response data
            parsed_object = response_data.get("parsed_object", {})
            answer = parsed_object.get("answer", "No answer generated")
            citations = parsed_object.get("citations", [])
            is_grounded = parsed_object.get("is_grounded", False)
            confidence = parsed_object.get("confidence", "medium")
            token_usage = response_data.get("token_usage", {})
            
            # Add assistant message to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer,
                "citations": citations,
                "is_grounded": is_grounded,
                "confidence": confidence,
                "token_usage": token_usage,
                "citation_status": parsed_object.get("citation_status", ""),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            st.success("✅ Response generated successfully!")
            st.rerun()
        else:
            st.error(f"❌ Error: {error_msg}")
            st.session_state.last_error = error_msg
            # Remove the user message if API call failed
            st.session_state.chat_history.pop()


def render_chat_history():
    """Render the complete chat history."""
    if not st.session_state.chat_history:
        st.info("💬 No messages yet. Ask a question to get started!")
        return
    
    for message in st.session_state.chat_history:
        render_chat_message(message)
        st.markdown("")


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point."""
    # Render header
    render_header()
    
    # Render sidebar
    render_sidebar()
    
    # Main content area
    render_chat_interface()
    
    st.markdown("---")
    
    # Chat history section
    if st.session_state.chat_history:
        st.markdown("### 📋 Conversation History")
        render_chat_history()
    
    # Debug information (if enabled)
    if st.session_state.show_debug:
        st.markdown("---")
        with st.expander("🐛 Debug Information"):
            st.write("**Session State:**")
            st.json({
                "chat_history_length": len(st.session_state.chat_history),
                "total_tokens": st.session_state.total_tokens_used,
                "api_status": st.session_state.api_status,
            })
            
            if st.session_state.last_error:
                st.error(f"Last Error: {st.session_state.last_error}")


if __name__ == "__main__":
    main()

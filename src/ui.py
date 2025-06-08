import streamlit as st
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List
from pathlib import Path

from src.cocktail_dev_agent import AGENTS
from agents import Runner

# Create chat history directory
CHAT_HISTORY_DIR = Path("chat_history")
CHAT_HISTORY_DIR.mkdir(exist_ok=True)

def load_chat_history(session_id: str) -> List[Dict]:
    """Load chat history from file"""
    history_file = CHAT_HISTORY_DIR / f"{session_id}.json"
    if history_file.exists():
        with open(history_file, 'r') as f:
            return json.load(f)
    return []

def save_chat_history(session_id: str, history: List[Dict]):
    """Save chat history to file"""
    history_file = CHAT_HISTORY_DIR / f"{session_id}.json"
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)

def get_session_id() -> str:
    """Generate or retrieve session ID"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    return st.session_state.session_id

async def run_agent_async(agent, prompt: str, context: Dict = None):
    """Run agent asynchronously"""
    result = await Runner.run(
        agent,
        input=prompt,
        context=context or {}
    )
    return result.final_output

def main():
    st.set_page_config(
        page_title="Cocktail Development Assistant",
        page_icon="🍸",
        layout="wide"
    )
    
    st.title("🍸 Cocktail Development Assistant")
    
    # Initialize session state
    if 'selected_agent' not in st.session_state:
        st.session_state.selected_agent = None
    if 'chat_active' not in st.session_state:
        st.session_state.chat_active = False
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Sidebar for agent selection
    with st.sidebar:
        st.header("Agent Selection")
        
        # Agent descriptions
        agent_descriptions = {
            "main": "🎯 Main orchestrator for cocktail development conversations",
            "wine": "🍷 Specialized agent for wine selection and pairing",
            "cocktail_spec_finder": "🔍 Finds cocktail specifications from the web",
            "flavor_affinity": "🌿 Discovers flavor affinities and combinations",
            "cocktail_spec_analyzer": "📊 Analyzes cocktail specifications and provides feedback",
            "cocktail_naming": "✨ Creates creative names for cocktails",
            "bottle_inventory": "📋 Manages and searches bottle inventory",
            "instagram_post": "📱 Searches historical Instagram posts",
            "bottle_researcher": "🔬 Researches and updates bottle information"
        }
        
        # Display agent options
        for agent_key, description in agent_descriptions.items():
            if st.button(description, key=f"btn_{agent_key}", use_container_width=True):
                if st.session_state.chat_active:
                    st.warning("Please end the current chat before selecting a new agent.")
                else:
                    st.session_state.selected_agent = agent_key
                    st.session_state.chat_active = True
                    st.session_state.chat_history = []
                    st.rerun()
        
        st.divider()
        
        # Chat controls
        if st.session_state.chat_active:
            st.success(f"Active: {AGENTS[st.session_state.selected_agent].name}")
            if st.button("🛑 End Chat", use_container_width=True):
                # Save chat history before ending
                if st.session_state.chat_history:
                    session_id = get_session_id()
                    save_chat_history(session_id, st.session_state.chat_history)
                    st.info(f"Chat saved as {session_id}")
                
                st.session_state.chat_active = False
                st.session_state.selected_agent = None
                st.session_state.chat_history = []
                st.rerun()
        
        st.divider()
        
        # Chat history management
        st.subheader("💾 Chat History")
        history_files = list(CHAT_HISTORY_DIR.glob("*.json"))
        if history_files:
            selected_history = st.selectbox(
                "Load previous chat:",
                [""] + [f.stem for f in sorted(history_files, reverse=True)],
                key="history_selector"
            )
            
            if selected_history and st.button("📂 Load Chat"):
                loaded_history = load_chat_history(selected_history)
                st.session_state.chat_history = loaded_history
                st.success(f"Loaded chat: {selected_history}")
                st.rerun()
        else:
            st.info("No saved chats yet")
    
    # Main chat interface
    if not st.session_state.chat_active:
        st.info("👈 Select an agent from the sidebar to start chatting!")
        
        # Show available agents
        st.subheader("Available Agents")
        cols = st.columns(3)
        for i, (agent_key, description) in enumerate(agent_descriptions.items()):
            with cols[i % 3]:
                st.markdown(f"**{description}**")
    
    else:
        current_agent = AGENTS[st.session_state.selected_agent]
        st.subheader(f"Chatting with: {current_agent.name}")
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.write(message["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(message["content"])
        
        # Chat input
        if prompt := st.chat_input("What would you like to discuss?"):
            # Add user message
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            # Display user message immediately
            with st.chat_message("user"):
                st.write(prompt)
            
            # Get AI response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        # Create context from recent history
                        context = {"preferences": {}}
                        conversation_prompt = "\n".join(
                            f"{msg['role']}: {msg['content']}" 
                            for msg in st.session_state.chat_history[-6:]
                        )
                        
                        # Run agent asynchronously
                        response = asyncio.run(
                            run_agent_async(current_agent, conversation_prompt, context)
                        )
                        
                        st.write(response)
                        
                        # Add assistant response to history
                        st.session_state.chat_history.append({
                            "role": "assistant", 
                            "content": response
                        })
                        
                    except Exception as e:
                        error_msg = f"Error: {str(e)}"
                        st.error(error_msg)
                        st.session_state.chat_history.append({
                            "role": "assistant", 
                            "content": error_msg
                        })

if __name__ == "__main__":
    main()
import streamlit as st
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from src.cocktail_dev_agent import AGENTS
from agents import Runner
from src.simple_prompt_optimizer import SimplePromptOptimizer, OptimizationRequest

# Create chat history directory
CHAT_HISTORY_DIR = Path("chat_history")
CHAT_HISTORY_DIR.mkdir(exist_ok=True)

# Initialize prompt optimizer
optimizer = SimplePromptOptimizer()

def load_chat_data(session_id: str) -> Dict:
    """Load complete chat data including metadata"""
    chat_file = CHAT_HISTORY_DIR / f"{session_id}.json"
    if chat_file.exists():
        with open(chat_file, 'r') as f:
            data = json.load(f)
            # Ensure backward compatibility
            if isinstance(data, list):
                return {
                    "metadata": {
                        "name": session_id,
                        "created": session_id,
                        "agent": "unknown",
                        "rating": None,
                        "notes": ""
                    },
                    "messages": data
                }
            return data
    return {"metadata": {}, "messages": []}

def save_chat_data(session_id: str, messages: List[Dict], metadata: Dict):
    """Save complete chat data with metadata"""
    chat_file = CHAT_HISTORY_DIR / f"{session_id}.json"
    data = {
        "metadata": metadata,
        "messages": messages
    }
    with open(chat_file, 'w') as f:
        json.dump(data, f, indent=2)

def delete_chat(session_id: str):
    """Delete a chat file"""
    chat_file = CHAT_HISTORY_DIR / f"{session_id}.json"
    if chat_file.exists():
        chat_file.unlink()

def get_all_chats() -> List[Dict]:
    """Get all chat files with metadata"""
    chats = []
    for chat_file in CHAT_HISTORY_DIR.glob("*.json"):
        try:
            data = load_chat_data(chat_file.stem)
            metadata = data.get("metadata", {})
            chats.append({
                "id": chat_file.stem,
                "name": metadata.get("name", chat_file.stem),
                "created": metadata.get("created", chat_file.stem),
                "agent": metadata.get("agent", "unknown"),
                "rating": metadata.get("rating"),
                "notes": metadata.get("notes", ""),
                "message_count": len(data.get("messages", []))
            })
        except Exception:
            continue
    return sorted(chats, key=lambda x: x["created"], reverse=True)

def generate_unique_session_id() -> str:
    """Generate a unique session ID with microsecond precision"""
    import uuid
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_suffix = str(uuid.uuid4())[:8]  # Short unique identifier
    return f"{timestamp}_{unique_suffix}"

def get_session_id() -> str:
    """Generate or retrieve session ID for current chat"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = generate_unique_session_id()
    return st.session_state.session_id

def reset_session_id():
    """Reset session ID for new chat"""
    if 'session_id' in st.session_state:
        del st.session_state.session_id

def show_chat_management():
    """Show chat management interface"""
    st.subheader("💾 Chat Management")
    
    chats = get_all_chats()
    if not chats:
        st.info("No saved chats yet")
        return
    
    # Chat list with management options
    for chat in chats:
        with st.expander(f"🗨️ {chat['name']} ({chat['agent']}) - {chat['message_count']} messages"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Chat metadata display and editing
                current_name = st.text_input(
                    "Chat Name:", 
                    value=chat['name'], 
                    key=f"name_{chat['id']}"
                )
                
                current_rating = st.selectbox(
                    "Rating:", 
                    options=[None, 1, 2, 3, 4, 5],
                    index=0 if chat['rating'] is None else chat['rating'],
                    key=f"rating_{chat['id']}"
                )
                
                current_notes = st.text_area(
                    "Notes:", 
                    value=chat['notes'], 
                    key=f"notes_{chat['id']}",
                    height=100
                )
                
                # Display chat info
                st.caption(f"Created: {chat['created']} | Agent: {chat['agent']}")
                if chat['rating']:
                    st.caption(f"Rating: {chat['rating']}/5")
            
            with col2:
                st.write("**Actions:**")
                
                # Update metadata button
                if st.button("💾 Update", key=f"update_{chat['id']}"):
                    chat_data = load_chat_data(chat['id'])
                    metadata = chat_data.get("metadata", {})
                    metadata.update({
                        "name": current_name,
                        "rating": current_rating,
                        "notes": current_notes,
                        "created": metadata.get("created", chat['id']),
                        "agent": metadata.get("agent", chat['agent'])
                    })
                    save_chat_data(chat['id'], chat_data.get("messages", []), metadata)
                    st.success("Updated!")
                    st.rerun()
                
                # Load chat button
                if st.button("📂 Load", key=f"load_{chat['id']}"):
                    chat_data = load_chat_data(chat['id'])
                    st.session_state.chat_history = chat_data.get("messages", [])
                    st.session_state.current_chat_id = chat['id']
                    st.success(f"Loaded: {chat['name']}")
                    st.rerun()
                
                # Delete chat button
                if st.button("🗑️ Delete", key=f"delete_{chat['id']}", type="secondary"):
                    if st.session_state.get(f"confirm_delete_{chat['id']}", False):
                        delete_chat(chat['id'])
                        st.success("Deleted!")
                        st.rerun()
                    else:
                        st.session_state[f"confirm_delete_{chat['id']}"] = True
                        st.warning("Click again to confirm deletion")

def show_prompt_management():
    """Show simplified prompt management interface"""
    st.subheader("🔧 Prompt Management")
    
    # Agent selection for prompt management
    agent_names = list(AGENTS.keys())
    selected_agent = st.selectbox("Select Agent:", agent_names, key="prompt_mgmt_agent")
    
    if selected_agent:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"📊 Performance for {selected_agent}")
            
            # Get performance summary
            performance = optimizer.get_agent_performance_summary(selected_agent)
            
            if performance["sessions"] > 0:
                # Display metrics
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Total Sessions", performance["sessions"])
                with col_b:
                    if performance["rated_sessions"] > 0:
                        st.metric("Average Rating", f"{performance['average_rating']:.1f}/5")
                    else:
                        st.metric("Average Rating", "No ratings")
                with col_c:
                    st.metric("Low Rated", performance["low_rated_count"])
                
                # Show optimization recommendation
                if performance["needs_optimization"]:
                    st.warning(f"⚠️ Agent performance below 3.5/5 - optimization recommended")
                else:
                    st.success(f"✅ Agent performing well (avg: {performance['average_rating']:.1f}/5)")
            else:
                st.info("No sessions found for this agent yet")
        
        with col2:
            st.subheader("🚀 Optimization")
            
            # Check for optimization candidates
            candidates = optimizer.list_optimization_candidates()
            agent_candidate = next((c for c in candidates if c["agent_name"] == selected_agent), None)
            
            if agent_candidate:
                st.warning("This agent could benefit from optimization")
                
                low_sessions = optimizer.get_low_rated_sessions(selected_agent)
                if low_sessions:
                    st.write(f"**Low-rated sessions ({len(low_sessions)}):**")
                    for session in low_sessions:
                        with st.expander(f"⭐ {session['rating']}/5 - {session['name'][:30]}..."):
                            st.write(f"**Notes:** {session['notes']}")
                            st.write(f"**Messages:** {len(session['messages'])}")
                    
                    # Quick optimization button
                    if st.button("🔧 Auto-Optimize", key=f"auto_opt_{selected_agent}"):
                        request = OptimizationRequest(
                            agent_name=selected_agent,
                            target_sessions=[s["session_id"] for s in low_sessions[:3]],  # Max 3 sessions
                            optimization_goals=agent_candidate["suggested_goals"]
                        )
                        
                        with st.spinner("Optimizing prompt..."):
                            try:
                                new_file = asyncio.run(optimizer.optimize_prompt(request))
                                st.success(f"✅ Created new version: {new_file}")
                                st.info("💡 Commit the new file to git and update your agent to use it")
                            except Exception as e:
                                st.error(f"Optimization failed: {e}")
            else:
                st.success("No optimization needed - performance looks good!")
        
        # Manual optimization section
        st.divider()
        st.subheader("🎯 Manual Optimization")
        
        with st.form(f"manual_optimization_{selected_agent}"):
            st.write("Create a custom optimization request:")
            
            # Get all sessions for this agent
            all_sessions = []
            for chat_file in Path("chat_history").glob("*.json"):
                try:
                    with open(chat_file, 'r') as f:
                        data = json.load(f)
                    metadata = data.get("metadata", {})
                    if metadata.get("agent") == selected_agent:
                        all_sessions.append({
                            "id": chat_file.stem,
                            "name": metadata.get("name", ""),
                            "rating": metadata.get("rating"),
                            "notes": metadata.get("notes", "")
                        })
                except Exception:
                    continue
            
            if all_sessions:
                # Filter to problematic sessions
                problematic_sessions = [s for s in all_sessions if s["rating"] and s["rating"] <= 3]
                
                if problematic_sessions:
                    session_options = {
                        f"{s['name'][:40]}... (Rating: {s['rating']}/5)": s['id'] 
                        for s in problematic_sessions
                    }
                    
                    selected_sessions = st.multiselect(
                        "Select sessions to analyze:",
                        options=list(session_options.keys()),
                        help="Choose sessions with issues you want to address"
                    )
                    
                    optimization_goals = st.multiselect(
                        "Optimization goals:",
                        ["improve tool usage efficiency", "improve task completion", 
                         "improve response clarity", "better brand alignment",
                         "improve output formatting", "better error handling"],
                        help="What aspects should be improved?"
                    )
                    
                    optimization_notes = st.text_area(
                        "Additional notes:",
                        help="Specific instructions for the optimization"
                    )
                    
                    if st.form_submit_button("🚀 Run Optimization"):
                        if selected_sessions and optimization_goals:
                            session_ids = [session_options[name] for name in selected_sessions]
                            
                            request = OptimizationRequest(
                                agent_name=selected_agent,
                                target_sessions=session_ids,
                                optimization_goals=optimization_goals,
                                notes=optimization_notes
                            )
                            
                            with st.spinner("Running optimization..."):
                                try:
                                    new_file = asyncio.run(optimizer.optimize_prompt(request))
                                    st.success(f"✅ Created new version: {new_file}")
                                    st.info("💡 Commit the new file to git and update your agent to use it")
                                except Exception as e:
                                    st.error(f"Optimization failed: {e}")
                        else:
                            st.error("Please select sessions and optimization goals")
                else:
                    st.info("No problematic sessions (rating ≤3) found for manual optimization")
            else:
                st.info("No sessions found for this agent")

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
    if 'current_chat_id' not in st.session_state:
        st.session_state.current_chat_id = None
    if 'chat_name' not in st.session_state:
        st.session_state.chat_name = ""
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["💬 Chat", "📋 Manage Chats", "🔧 Prompt Management"])
    
    with tab2:
        show_chat_management()
    
    with tab3:
        show_prompt_management()
    
    with tab1:
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
                        st.session_state.current_chat_id = None
                        st.session_state.chat_name = ""
                        reset_session_id()  # Ensure new unique session ID
                        st.rerun()
            
            st.divider()
            
            # Chat controls and metadata
            if st.session_state.chat_active:
                st.success(f"Active: {AGENTS[st.session_state.selected_agent].name}")
                
                # Chat naming
                new_chat_name = st.text_input(
                    "Chat Name:", 
                    value=st.session_state.chat_name,
                    placeholder="Enter a descriptive name..."
                )
                if new_chat_name != st.session_state.chat_name:
                    st.session_state.chat_name = new_chat_name
                
                if st.button("🛑 End Chat", use_container_width=True):
                    # Save chat with metadata
                    if st.session_state.chat_history:
                        session_id = st.session_state.current_chat_id or get_session_id()
                        chat_name = st.session_state.chat_name or f"Chat with {AGENTS[st.session_state.selected_agent].name}"
                        
                        metadata = {
                            "name": chat_name,
                            "created": session_id,
                            "agent": st.session_state.selected_agent,
                            "rating": None,
                            "notes": ""
                        }
                        
                        save_chat_data(session_id, st.session_state.chat_history, metadata)
                        st.info(f"Chat saved: {chat_name}")
                    
                    st.session_state.chat_active = False
                    st.session_state.selected_agent = None
                    st.session_state.chat_history = []
                    st.session_state.current_chat_id = None
                    st.session_state.chat_name = ""
                    reset_session_id()  # Reset for next chat
                    st.rerun()
            
            st.divider()
            
            # Quick load recent chats
            st.subheader("🕒 Recent Chats")
            recent_chats = get_all_chats()[:5]  # Show last 5 chats
            if recent_chats:
                for chat in recent_chats:
                    rating_display = "⭐" * (chat['rating'] or 0) if chat['rating'] else ""
                    if st.button(
                        f"{chat['name'][:25]}... {rating_display}", 
                        key=f"quick_load_{chat['id']}",
                        use_container_width=True,
                        help=f"Agent: {chat['agent']} | Messages: {chat['message_count']}"
                    ):
                        chat_data = load_chat_data(chat['id'])
                        st.session_state.chat_history = chat_data.get("messages", [])
                        st.session_state.current_chat_id = chat['id']
                        st.session_state.chat_name = chat['name']
                        st.success(f"Loaded: {chat['name']}")
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
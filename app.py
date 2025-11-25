import streamlit as st
import google.generativeai as genai
import json
import graphviz
from datetime import datetime

# --- 1. CONFIGURATION & SETUP ---

st.set_page_config(
    page_title="SEYAL: AI Action Companion", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern aesthetic
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary: #6366f1;
        --secondary: #8b5cf6;
        --accent: #ec4899;
        --success: #10b981;
        --warning: #f59e0b;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }
    
    .main-header h1 {
        color: white;
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
    
    /* Card styling */
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
        border: 1px solid rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 12px rgba(0, 0, 0, 0.1);
    }
    
    /* Milestone styling */
    .milestone {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        padding: 1rem 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #667eea;
        margin: 0.75rem 0;
        font-weight: 500;
    }
    
    /* Task checkbox styling */
    .stMarkdown ul {
        list-style: none;
        padding-left: 0;
    }
    
    .stMarkdown li {
        background: #f8fafc;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        border-left: 3px solid #10b981;
        transition: all 0.2s;
    }
    
    .stMarkdown li:hover {
        background: #f1f5f9;
        transform: translateX(5px);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: white;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 600;
        border: 2px solid transparent;
        transition: all 0.2s;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border-color: transparent;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Input field styling */
    .stTextArea textarea, .stTextInput input {
        border-radius: 10px;
        border: 2px solid #e5e7eb;
        transition: all 0.2s;
    }
    
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    
    .badge-success {
        background: #10b98120;
        color: #10b981;
    }
    
    .badge-info {
        background: #3b82f620;
        color: #3b82f6;
    }
    
    .badge-warning {
        background: #f59e0b20;
        color: #f59e0b;
    }
    
    /* Animation for loading */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .loading {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1e293b;
        margin: 1.5rem 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: #f8fafc;
        border-radius: 10px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Secure API Key Retrieval
# Priority: 1. Streamlit Secrets, 2. Environment Variable, 3. User Input
import os

api_key = None

# Try Streamlit secrets first (for Streamlit Cloud)
try:
    api_key = st.secrets.get("GEMINI_API_KEY")
except:
    pass

# Fallback to environment variable
if not api_key:
    api_key = os.getenv("GEMINI_API_KEY")

# Last resort: ask user to input
if not api_key:
    st.sidebar.markdown("### 🔑 API Configuration")
    api_key = st.sidebar.text_input("Enter Google Gemini API Key", type="password", help="Get your key from https://aistudio.google.com/app/apikey")
    
if not api_key:
    st.warning("⚠️ Please provide a Google Gemini API Key to run the agents.")
    st.info("💡 **How to get started:**\n1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)\n2. Generate a free API key\n3. Enter it in the sidebar")
    st.stop()

genai.configure(api_key=api_key)


# --- 2. ADVANCED MEMORY SYSTEM (Context Compaction) ---

def summarize_old_logs_llm(logs_to_compact):
    """Helper function to summarize old logs using a lightweight Gemini model."""
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    log_text = json.dumps(logs_to_compact, indent=2)
    prompt = f"""
    Analyze these past daily logs. Summarize the user's progress, wins, and mood patterns 
    into a single, narrative paragraph (max 3 sentences). Keep critical details.
    Logs to Summarize: {log_text}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Summary generation failed due to API error: {e}"

class SeyalMemoryBank:
    """Manages state using st.session_state and implements Context Compaction."""
    def __init__(self):
        if "roadmap" not in st.session_state:
            st.session_state["roadmap"] = []
        if "logs" not in st.session_state:
            st.session_state["logs"] = []
        if "long_term_summary" not in st.session_state:
            st.session_state["long_term_summary"] = "User started SEYAL journey."
        if "tasks" not in st.session_state:
            st.session_state["tasks"] = "No tasks generated yet. Please generate a plan first."

    def update_roadmap(self, milestones: list):
        """Saves the high-level milestones to memory."""
        st.session_state["roadmap"] = milestones
        return "✅ Roadmap saved to memory."

    def log_daily_update(self, update_text: str, mood: str):
        """Logs a new daily entry and triggers compaction if necessary."""
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "update": update_text,
            "mood": mood
        }
        st.session_state["logs"].append(entry)
        
        if len(st.session_state["logs"]) > 5:
            self._run_compaction()
            return "Daily update logged & Memory Compacted (Old logs summarized)."
        
        return "Daily update logged."

    def _run_compaction(self):
        """Moves oldest logs into long-term summary."""
        logs_to_keep = 3
        logs_to_compact = st.session_state["logs"][:-logs_to_keep]
        recent_logs = st.session_state["logs"][-logs_to_keep:]
        
        with st.spinner("💾 Compacting Memory to save context..."):
            new_summary = summarize_old_logs_llm(logs_to_compact)
            st.session_state["long_term_summary"] += f"\n\n[Period Summary ({datetime.now().strftime('%Y-%m-%d')})]: {new_summary}"
            st.session_state["logs"] = recent_logs
            st.toast("Old memories compressed into Long-Term Storage.")

    def retrieve_history_tool(self):
        """Returns the 'Smart Context' for Reflection."""
        return json.dumps({
            "current_plan": st.session_state["roadmap"],
            "long_term_history": st.session_state["long_term_summary"],
            "recent_daily_logs": st.session_state["logs"]
        })

memory = SeyalMemoryBank()


# --- 3. AGENTS (The Brains) ---

@st.cache_resource
def get_planner_agent():
    system_instruction = """
    You are the SEYAL Planner. Goal: Break a user's objective into 4 clear, sequential milestones.
    Action: You MUST use the `update_roadmap` tool to save them.
    Response: A brief, encouraging confirmation.
    """
    return genai.GenerativeModel(
        model_name='gemini-2.0-flash-exp',
        tools=[memory.update_roadmap], 
        system_instruction=system_instruction
    )

@st.cache_resource
def get_task_agent():
    system_instruction = """
    You are the SEYAL Task Manager. Goal: Take the current plan and generate ONE day's worth of micro-tasks (3-4 items)
    for the next milestone. Format: Use Markdown Checkboxes (e.g., - [ ] Task).
    """
    return genai.GenerativeModel(
        model_name='gemini-2.0-flash-exp',
        system_instruction=system_instruction
    )

@st.cache_resource
def get_reflector_agent():
    system_instruction = """
    You are the SEYAL Insight Agent. Goal: Analyze user progress.
    Action: Call `retrieve_history_tool` to see past context.
    Output: A Weekly Report with 1. 🏆 Wins, 2. ⚠️ Patterns Detected, 3. 🚀 Next Focus.
    """
    return genai.GenerativeModel(
        model_name='gemini-2.0-flash-exp',
        tools=[memory.retrieve_history_tool],
        system_instruction=system_instruction
    )


# --- 4. UI LAYOUT ---

# Custom Header
st.markdown("""
<div class="main-header">
    <h1>⚡ SEYAL: AI Action Companion</h1>
    <p>Sequential Multi-Agent System with Context Compaction • Your Personal Achievement Partner</p>
</div>
""", unsafe_allow_html=True)

# Stats Row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Milestones</div>
        <div class="metric-value">{len(st.session_state['roadmap'])}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Logged Days</div>
        <div class="metric-value">{len(st.session_state['logs'])}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    recent_mood = st.session_state['logs'][-1]['mood'] if st.session_state['logs'] else 'N/A'
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Latest Mood</div>
        <div class="metric-value" style="font-size: 1.8rem;">{recent_mood}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    is_active = len(st.session_state['roadmap']) > 0
    status_text = "Active" if is_active else "Inactive"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Status</div>
        <div class="metric-value" style="font-size: 1.8rem;">{'🟢' if is_active else '🔴'}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Architecture Visualization
with st.expander("🛠️ System Architecture (Click to View)"):
    graph = graphviz.Digraph(comment='SEYAL Agent Architecture', graph_attr={'rankdir': 'LR', 'bgcolor': 'transparent'})
    graph.attr('node', style='filled', fontname='Arial', fontsize='12')
    
    graph.node('A', 'User', shape='circle', fillcolor='#fbbf24', fontcolor='white')
    graph.node('B', 'Planner', shape='box', fillcolor='#667eea', fontcolor='white')
    graph.node('C', 'Tasker', shape='box', fillcolor='#8b5cf6', fontcolor='white')
    graph.node('D', 'Reflector', shape='box', fillcolor='#ec4899', fontcolor='white')
    graph.node('E', 'Memory\n(Compaction)', shape='cylinder', fillcolor='#10b981', fontcolor='white')
    
    graph.edge('A', 'B', 'Goal', color='#667eea')
    graph.edge('B', 'E', 'Save Roadmap', color='#10b981')
    graph.edge('E', 'C', 'Context', color='#8b5cf6')
    graph.edge('C', 'A', 'Daily Tasks', color='#fbbf24')
    graph.edge('A', 'E', 'Log Progress', color='#10b981')
    graph.edge('E', 'D', 'Retrieve History', color='#ec4899')
    graph.edge('D', 'A', 'Insights', color='#fbbf24')
    
    st.graphviz_chart(graph)

# Main Interface Tabs
tab1, tab2, tab3 = st.tabs(["🗺️  PLAN", "⚡  ACTION", "🧠  REFLECT"])

# --- TAB 1: PLANNER ---
with tab1:
    st.markdown('<div class="section-header">🎯 Define Your Ambitious Goal</div>', unsafe_allow_html=True)
    
    user_goal = st.text_area(
        "What do you want to achieve?", 
        placeholder="E.g., Learn Python and deploy a data science project in 4 weeks.\nE.g., Build a personal brand and get 1000 followers in 2 months.",
        height=120
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✨ Generate Roadmap", use_container_width=True):
            if not user_goal:
                st.error("Please enter a goal.")
            else:
                with st.spinner("🧠 Planner Agent is strategizing..."):
                    try:
                        planner = get_planner_agent()
                        chat = planner.start_chat(enable_automatic_function_calling=True) 
                        response = chat.send_message(f"My goal is: {user_goal}")
                        st.success("✅ Roadmap created successfully!")
                        st.info(response.text)
                    except Exception as e:
                        st.error(f"Error during planning: {e}")

    # Display Current Roadmap
    if st.session_state["roadmap"]:
        st.markdown('<div class="section-header">📍 Your Journey Milestones</div>', unsafe_allow_html=True)
        for i, m in enumerate(st.session_state["roadmap"]):
            st.markdown(f'<div class="milestone">🎯 <strong>Milestone {i+1}:</strong> {m}</div>', unsafe_allow_html=True)
    else:
        st.info("👆 Create your first roadmap to get started on your journey!")

# --- TAB 2: ACTION ---
with tab2:
    col1, col2 = st.columns([1, 1])
    
    # Left: Task Generation
    with col1:
        st.markdown('<div class="section-header">📋 Today\'s Action Items</div>', unsafe_allow_html=True)
        
        if st.button("🚀 Generate Today's Tasks", use_container_width=True):
            if not st.session_state["roadmap"]:
                st.warning("⚠️ Please create a roadmap first in the PLAN tab!")
            else:
                with st.spinner("⚙️ Task Agent is breaking down your plan..."):
                    task_agent = get_task_agent()
                    context = f"Current Plan: {st.session_state['roadmap']}. Long-Term Summary: {st.session_state['long_term_summary']}"
                    response = task_agent.generate_content(f"{context}. Generate detailed, executable tasks for today based on the next milestone in the plan.")
                    st.session_state["tasks"] = response.text
        
        st.markdown(st.session_state["tasks"])

    # Right: Logging
    with col2:
        st.markdown('<div class="section-header">📝 Daily Progress Logger</div>', unsafe_allow_html=True)
        
        log_input = st.text_area(
            "What did you accomplish today?", 
            placeholder="Share your wins, challenges, and learnings...",
            height=150,
            key="log_input"
        )
        
        mood_input = st.select_slider(
            "How are you feeling?", 
            ["😩 Drained", "😐 Bored", "😊 Neutral", "😄 Good", "🔥 Energetic"]
        )
        
        if st.button("💾 Save Progress", use_container_width=True):
            if not log_input:
                st.warning("Please enter your daily progress.")
            else:
                msg = memory.log_daily_update(log_input, mood_input)
                st.success(msg)
                st.balloons()

# --- TAB 3: REFLECT ---
with tab3:
    st.markdown('<div class="section-header">📊 Progress Insights & Analysis</div>', unsafe_allow_html=True)
    
    st.info("💡 The Reflector Agent analyzes your journey using long-term memory patterns to provide personalized insights.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔍 Generate Insights Report", use_container_width=True):
            if len(st.session_state["logs"]) == 0 and "User started" in st.session_state["long_term_summary"]:
                st.warning("📅 Not enough data yet. Log a few days of actions before reflecting!")
            else:
                with st.spinner("🧠 Reflector Agent is analyzing your journey..."):
                    reflector = get_reflector_agent()
                    chat = reflector.start_chat(enable_automatic_function_calling=True)
                    response = chat.send_message("Generate my SEYAL Report now.")
                    st.markdown(response.text)

# --- DEBUG VIEW ---
with st.expander("🔍 System Internals (Memory State & Observability)"):
    st.markdown("### 💾 Current Memory State")
    
    tab_debug1, tab_debug2, tab_debug3 = st.tabs(["Roadmap", "Recent Logs", "Long-Term Summary"])
    
    with tab_debug1:
        st.json(st.session_state["roadmap"])
    
    with tab_debug2:
        st.json(st.session_state["logs"])
    
    with tab_debug3:
        st.text_area("Compacted Memory", st.session_state["long_term_summary"], height=200, disabled=True)

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: #94a3b8; padding: 2rem;'>
    <p>Built with ⚡ by SEYAL • Powered by Google Gemini</p>
</div>
""", unsafe_allow_html=True)

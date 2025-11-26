import streamlit as st
import google.generativeai as genai
import json
from datetime import datetime

# --- 1. CONFIGURATION & SETUP ---

st.set_page_config(page_title="SEYAL: AI Action Companion", page_icon="⚡", layout="wide")

# Secure API Key Retrieval
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    # Allows input via sidebar if secrets.toml is missing
    api_key = st.sidebar.text_input("Enter Google Gemini API Key", type="password")
    
if not api_key:
    st.warning("⚠️ Please provide a Google Gemini API Key to run the agents.")
    st.stop()

# Initialize the Gemini Client
genai.configure(api_key=api_key)


# --- 2. ADVANCED MEMORY SYSTEM (Context Compaction) ---

def summarize_old_logs_llm(logs_to_compact):
    """
    Helper function to summarize old logs using a lightweight Gemini model.
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
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
    """
    Manages state using st.session_state and implements Context Compaction.
    """
    def __init__(self):
        # Initialize state components
        if "roadmap" not in st.session_state:
            st.session_state["roadmap"] = []
        if "logs" not in st.session_state:
            st.session_state["logs"] = [] # Detailed recent logs
        if "long_term_summary" not in st.session_state:
            st.session_state["long_term_summary"] = "User started SEYAL journey."
        if "tasks" not in st.session_state:
            st.session_state["tasks"] = "No tasks generated yet. Please generate a plan first."

    # --- Tool: Update Roadmap (Used by Planner Agent) ---
    def update_roadmap(self, milestones: list):
        """Saves the high-level milestones to memory (Function Calling Tool)."""
        st.session_state["roadmap"] = milestones
        return "✅ Roadmap saved to memory."

    # --- Tool: Log Daily Update (Called directly from UI) ---
    def log_daily_update(self, update_text: str, mood: str):
        """Logs a new daily entry and triggers compaction if necessary."""
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "update": update_text,
            "mood": mood
        }
        st.session_state["logs"].append(entry)
        
        # --- CONTEXT COMPACTION TRIGGER ---
        # If logs exceed 5 entries, we compact the oldest ones
        if len(st.session_state["logs"]) > 5:
            self._run_compaction()
            return "Daily update logged & Memory Compacted (Old logs summarized)."
        
        return "Daily update logged."

    def _run_compaction(self):
        """Moves oldest logs into long-term summary."""
        logs_to_keep = 3 # Keep only last 3 days in detail
        logs_to_compact = st.session_state["logs"][:-logs_to_keep]
        recent_logs = st.session_state["logs"][-logs_to_keep:]
        
        with st.spinner("💾 Compacting Memory to save context..."):
            new_summary = summarize_old_logs_llm(logs_to_compact)
            
            # Update Long Term State
            st.session_state["long_term_summary"] += f"\n\n[Period Summary ({datetime.now().strftime('%Y-%m-%d')})]: {new_summary}"
            st.session_state["logs"] = recent_logs
            st.toast("Old memories compressed into Long-Term Storage.")

    # --- Tool: Retrieve History (Used by Reflection Agent) ---
    def retrieve_history_tool(self):
        """Returns the 'Smart Context' for Reflection (Function Calling Tool)."""
        return json.dumps({
            "current_plan": st.session_state["roadmap"],
            "long_term_history": st.session_state["long_term_summary"],
            "recent_daily_logs": st.session_state["logs"]
        })

memory = SeyalMemoryBank()


# --- 3. AGENTS (The Brains) ---

# Use st.cache_resource to avoid re-initializing the model on every Streamlit rerun
@st.cache_resource
def get_planner_agent():
    system_instruction = """
    You are the SEYAL Planner. Goal: Break a user's objective into 4 clear, sequential milestones.
    Action: You MUST use the `update_roadmap` tool to save them.
    Response: A brief, encouraging confirmation.
    """
    return genai.GenerativeModel(
        model_name='gemini-2.5-flash',
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
        model_name='gemini-2.5-flash',
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
        model_name='gemini-2.5-pro',
        tools=[memory.retrieve_history_tool],
        system_instruction=system_instruction
    )


# --- 4. UI LAYOUT ---

st.title("⚡ SEYAL: The Action Agent")
st.caption("Sequential Multi-Agent System with Context Compaction")

# Main Interface Tabs
tab1, tab2, tab3 = st.tabs(["🗺️ 1. PLAN", "⚡ 2. ACTION", "🧠 3. REFLECT"])

# --- TAB 1: PLANNER ---
with tab1:
    st.subheader("Define Your Goal")
    user_goal = st.text_area("What ambitious goal do you want to achieve?", 
                            placeholder="E.g., Learn Python and deploy a data science project in 4 weeks.")
    
    if st.button("Generate Roadmap"):
        if not user_goal:
            st.error("Please enter a goal.")
        else:
            with st.spinner("Planner Agent is strategizing and saving milestones..."):
                try:
                    planner = get_planner_agent()
                    chat = planner.start_chat(enable_automatic_function_calling=True) 
                    response = chat.send_message(f"My goal is: {user_goal}")
                    st.success("Roadmap created!")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"Error during planning: {e}")

    # Display Current Roadmap
    if st.session_state["roadmap"]:
        st.markdown("### 📍 Current Milestones")
        for i, m in enumerate(st.session_state["roadmap"]):
            st.info(f"**Milestone {i+1}:** {m}")

# --- TAB 2: ACTION ---
with tab2:
    col1, col2 = st.columns([1, 1])
    
    # Left: Task Generation
    with col1:
        st.markdown("### 📋 Daily Tasks")
        if st.button("Get Today's Tasks"):
            with st.spinner("Task Agent is breaking down the plan..."):
                task_agent = get_task_agent()
                context = f"Current Plan: {st.session_state['roadmap']}. Long-Term Summary: {st.session_state['long_term_summary']}"
                response = task_agent.generate_content(f"{context}. Generate detailed, executable tasks for today based on the next milestone in the plan.")
                st.session_state["tasks"] = response.text
        
        st.markdown(st.session_state["tasks"])

    # Right: Logging
    with col2:
        st.markdown("### 📝 Log Progress")
        log_input = st.text_area("What did you complete and what challenges did you face?", key="log_input")
        mood_input = st.select_slider("Mood", ["Drained", "Bored", "Neutral", "Good", "Energetic"])
        
        if st.button("Log Update"):
            if not log_input:
                st.warning("Please enter your daily progress.")
            else:
                msg = memory.log_daily_update(log_input, mood_input)
                st.success(msg)
                st.session_state.log_input = "" # Clear input

# --- TAB 3: REFLECT ---
with tab3:
    st.subheader("Weekly Insights")
    st.info("The Reflector Agent uses your **long-term summary** to find valuable patterns.")
    
    if st.button("Analyze My Progress"):
        if len(st.session_state["logs"]) == 0 and "User started" in st.session_state["long_term_summary"]:
            st.warning("Not enough data yet. Log a few days of actions before reflecting!")
        else:
            with st.spinner("Reflector Agent is analyzing memory and generating report..."):
                reflector = get_reflector_agent()
                chat = reflector.start_chat(enable_automatic_function_calling=True)
                response = chat.send_message("Generate my SEYAL Report now.")
                st.markdown(response.text)

# --- DEBUG VIEW (Optional but useful for judges) ---
with st.expander("🔍 Internals (Memory State and Observability)"):
    st.json({
        "Roadmap": st.session_state["roadmap"],
        "Recent Detailed Logs (Last 3-5 days)": st.session_state["logs"],
        "Long Term Memory Summary (Compacted History)": st.session_state["long_term_summary"]
    })

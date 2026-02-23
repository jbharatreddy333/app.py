import streamlit as st
import google.generativeai as genai
import json
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# 1. Set the page title and the logo as the browser favicon
st.set_page_config(
    page_title="Seyal",
    page_icon="⚡",  # Using emoji as fallback if logo.jpg missing
    layout="wide"
)

# 2. Display the logo at the top of the app or in the sidebar
try:
    st.sidebar.image("logo.jpg", width=150)
except:
    st.sidebar.markdown("# ⚡")
st.sidebar.title("Seyal")

# --- PWA INJECTION CODE ---
def inject_pwa():
    pwa_code = """
    <link rel="manifest" href="https://raw.githubusercontent.com/jbharatreddy333/app.py/main/manifest.json">
    <script>
      if ('serviceWorker' in navigator) {
        window.addEventListener('load', function() {
          navigator.serviceWorker.register('https://raw.githubusercontent.com/jbharatreddy333/app.py/main/sw.js').then(function(registration) {
            console.log('ServiceWorker registration successful');
          }, function(err) {
            console.log('ServiceWorker registration failed: ', err);
          });
        });
      }
    </script>
    """
    components.html(pwa_code, height=0)

inject_pwa()

# --- 1. CONFIGURATION & SETUP ---

# Secure API Key Retrieval
api_key = st.secrets.get("GEMINI_API_KEY") if hasattr(st, 'secrets') else None

if not api_key:
    api_key = st.sidebar.text_input("Enter Google Gemini API Key", type="password")
    
if not api_key:
    st.warning("⚠️ Please provide a Google Gemini API Key to run the agents.")
    st.info("💡 Get your free API key at: https://makersuite.google.com/app/apikey")
    st.stop()

# Initialize the Gemini Client
try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Error configuring API: {e}")
    st.stop()


# --- 2. ADVANCED MEMORY SYSTEM (Context Compaction) ---

def summarize_old_logs_llm(logs_to_compact):
    """Helper function to summarize old logs using a lightweight Gemini model."""
    model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')
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
        # Initialize state components
        if "roadmap" not in st.session_state:
            st.session_state["roadmap"] = []
        if "logs" not in st.session_state:
            st.session_state["logs"] = []
        if "long_term_summary" not in st.session_state:
            st.session_state["long_term_summary"] = "User started SEYAL journey."
        if "tasks" not in st.session_state:
            st.session_state["tasks"] = []
        if "task_status" not in st.session_state:
            st.session_state["task_status"] = {}
        if "core_why" not in st.session_state:
            st.session_state["core_why"] = ""
        if "seyal_points" not in st.session_state:
            st.session_state["seyal_points"] = 0
        if "current_streak" not in st.session_state:
            st.session_state["current_streak"] = 0
        if "last_log_date" not in st.session_state:
            st.session_state["last_log_date"] = None
        if "conversation_history" not in st.session_state:
            st.session_state["conversation_history"] = []
        if "pending_tasks" not in st.session_state:
            st.session_state["pending_tasks"] = []
        if "chat_messages" not in st.session_state:
            st.session_state["chat_messages"] = []

    def update_roadmap(self, milestones: list):
        """Saves the high-level milestones to memory (Function Calling Tool)."""
        st.session_state["roadmap"] = milestones
        return "✅ Roadmap saved to memory."

    def log_daily_update(self, update_text: str, mood: str, completed_tasks: list):
        """Logs a new daily entry and triggers compaction if necessary."""
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "update": update_text,
            "mood": mood,
            "completed_tasks": completed_tasks
        }
        st.session_state["logs"].append(entry)
        
        # Award points
        points_earned, streak_msg = self.award_points(completed_tasks, mood)
        
        # Update last log date for streak tracking
        today = datetime.now().date()
        if st.session_state["last_log_date"]:
            last_date = datetime.strptime(st.session_state["last_log_date"], "%Y-%m-%d").date()
            days_diff = (today - last_date).days
            if days_diff > 1:
                st.session_state["current_streak"] = 0
        
        st.session_state["last_log_date"] = today.strftime("%Y-%m-%d")
        
        # Context compaction trigger
        if len(st.session_state["logs"]) > 5:
            self._run_compaction()
            msg = "Daily update logged & Memory Compacted (Old logs summarized)."
        else:
            msg = "Daily update logged."
        
        # Add streak message if exists
        if streak_msg:
            msg += f"\n{streak_msg}"
        msg += f"\n⚡ +{points_earned} Seyal Points earned!"
        
        return msg

    def award_points(self, tasks_completed, mood):
        """Award points based on completion and consistency."""
        points = len(tasks_completed) * 10
        
        # Bonus for maintaining good mood
        if mood in ["Good", "Energetic"]:
            points += 5
        
        streak_msg = None
        # Check for streak
        if tasks_completed:
            st.session_state["current_streak"] += 1
            if st.session_state["current_streak"] % 3 == 0:
                points += 20
                streak_msg = f"🔥 {st.session_state['current_streak']}-day streak! Bonus +20 points!"
        
        st.session_state["seyal_points"] += points
        return points, streak_msg

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

    def get_history_context(self):
        """Returns formatted history context as a string."""
        roadmap_text = ""
        if st.session_state["roadmap"]:
            for i, milestone in enumerate(st.session_state["roadmap"], 1):
                roadmap_text += f"\n  {i}. {str(milestone)}"
        else:
            roadmap_text = "\n  No roadmap created yet."
        
        context = f"""
# USER PROGRESS CONTEXT

## User's Core Motivation (Their "Why"):
{st.session_state.get("core_why", "Not specified yet")}

## Current Plan (Milestones):{roadmap_text}

## Long-Term History Summary:
{st.session_state["long_term_summary"]}

## Gamification Stats:
- Seyal Points: {st.session_state["seyal_points"]}
- Current Streak: {st.session_state["current_streak"]} days

## Recent Daily Logs (Day-by-Day Analysis):
"""
        if not st.session_state["logs"]:
            context += "\nNo logs recorded yet."
        else:
            for i, log in enumerate(st.session_state["logs"], 1):
                context += f"\n### Day {i}: {log.get('date', 'Unknown date')}"
                context += f"\n**Mood**: {log.get('mood', 'Not specified')}"
                context += f"\n**Progress Update**: {log.get('update', 'No update')}"
                
                completed = log.get('completed_tasks', [])
                if completed:
                    context += f"\n**✅ Tasks Completed** ({len(completed)}):"
                    for task in completed:
                        context += f"\n  • {str(task)}"
                else:
                    context += "\n**Tasks Completed**: None recorded"
                context += "\n"
        
        return context

    def generate_contextual_nudge(self, task, user_recent_mood):
        """Creates a personalized nudge based on context."""
        nudge_agent = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')
        
        prompt = f"""
        Generate a 1-sentence motivational nudge for this task: "{task}"
        
        Context:
        - User's recent mood: {user_recent_mood}
        - User's goal: {st.session_state['roadmap'][0] if st.session_state['roadmap'] else 'Not set'}
        - User's core why: {st.session_state.get('core_why', 'Not specified')}
        
        RULES:
        - If mood is low (Drained/Bored), offer encouragement and suggest starting small
        - If mood is high (Good/Energetic), be energizing and confident
        - Always connect to their bigger "why" when possible
        - Keep it to ONE sentence
        - Sound like a supportive friend, not a drill sergeant
        - Use an emoji if it fits naturally
        
        Example: "Ready to knock out that research task? Even 15 focused minutes gets you closer to your dream career! 🚀"
        """
        
        try:
            response = nudge_agent.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Let's tackle this task together! You've got this! 💪"

memory = SeyalMemoryBank()


# --- 3. AGENTS (The Brains) ---

@st.cache_resource
def get_planner_agent():
    system_instruction = """
    You are the SEYAL Planner. Goal: Break a user's objective into 4 clear, sequential milestones.
    Action: You MUST use the `update_roadmap` tool to save them.
    Response: A brief, encouraging confirmation that references their "why" if provided.
    Keep your response conversational, warm, and motivating like a supportive coach.
    """
    return genai.GenerativeModel(
        model_name='gemini-2.5-flash-preview-04-17',
        tools=[memory.update_roadmap], 
        system_instruction=system_instruction
    )

@st.cache_resource
def get_task_agent():
    system_instruction = """
    You are the SEYAL Task Manager. Goal: Take the current plan and generate ONE day's worth of micro-tasks (3-5 items)
    for the next milestone. 
    IMPORTANT: Return ONLY a JSON array of task strings. Example: ["Task 1", "Task 2", "Task 3"]
    Do NOT include markdown, checkboxes, or any other formatting.
    Make tasks specific, actionable, and achievable in one day.
    """
    return genai.GenerativeModel(
        model_name='gemini-2.5-flash-preview-04-17',
        system_instruction=system_instruction
    )

def get_reflector_agent():
    """Create reflector agent for day-by-day progress analysis."""
    system_instruction = """
    You are the SEYAL Insight Agent - an expert at analyzing daily progress patterns.
    
    You will receive the user's day-by-day logs including:
    - What they accomplished each day
    - Which specific tasks they completed
    - Their mood each day
    - Their overall plan and milestones
    - Their core "why" (motivation)
    
    Your job is to provide a detailed Weekly Report with:
    
    1. 🏆 **Daily Wins Recap**
       - Summarize what they accomplished each day
       - Highlight specific tasks completed
       - Celebrate their consistency and progress
    
    2. ⚠️ **Patterns & Insights Detected**
       - Mood trends across days (energy levels, motivation patterns)
       - Consistency in task completion
       - Which days were most productive and why
       - Any challenges or obstacles that appeared
    
    3. 🚀 **Strategic Next Steps**
       - What to focus on tomorrow/next week
       - Based on their plan, what's the next milestone
       - Suggestions to maintain momentum
       - Connect recommendations to their "why"
    
    Be specific, encouraging, and data-driven. Reference actual tasks completed and specific days.
    Make the user feel proud of their progress while giving actionable insights!
    Write in a warm, conversational tone like a supportive friend.
    """
    return genai.GenerativeModel(
        model_name='gemini-2.5-flash-preview-04-17',
        system_instruction=system_instruction
    )

def get_conversation_agent():
    """Create conversational agent for morning/evening rituals."""
    system_instruction = """
    You are SEYAL - a warm, supportive AI companion who helps people achieve their goals.
    
    PERSONALITY:
    - Speak like a trusted friend who genuinely cares
    - Be encouraging but honest
    - Use "we" language (we're in this together)
    - Keep responses SHORT - 2-3 sentences max unless asked for more
    - Use casual, natural language
    - Sprinkle in emojis naturally (not excessively)
    - Ask ONE question at a time
    - Remember their "why" and reference it when they need motivation
    
    MORNING BRIEFING:
    - Greet them warmly
    - Review today's tasks in an energizing way
    - Ask which task is their "frog" (hardest/most important to do first)
    - Based on past logs, suggest a realistic order
    - Connect to their bigger "why" for motivation
    - Keep it brief - 3-4 conversational turns max
    
    EVENING REFLECTION:
    - Celebrate what got done (be specific about tasks)
    - Ask how they FEEL about their progress (emotional check-in)
    - If tasks were missed, ask why WITHOUT judgment
    - Suggest ONE easy win for tomorrow
    - Remind them of their streak or points if relevant
    - Make them feel proud, even on tough days
    
    GENERAL CONVERSATION:
    - Answer questions about their progress
    - Provide motivation when asked
    - Help them adjust plans if needed
    - Be their accountability partner
    - Celebrate wins, no matter how small
    - When they're struggling, validate their feelings first
    
    Remember: You're not a robot, you're a supportive friend. Be human, be kind, be real.
    """
    return genai.GenerativeModel(
        model_name='gemini-2.5-flash-preview-04-17',
        system_instruction=system_instruction
    )


# --- 4. UI LAYOUT ---

st.title("⚡ SEYAL: Your AI Action Partner")
st.caption("Let's achieve your goals together, one conversation at a time")

# Sidebar Stats
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Your Stats")
col1, col2 = st.sidebar.columns(2)
with col1:
    st.metric("⚡ Points", st.session_state.get("seyal_points", 0))
with col2:
    st.metric("🔥 Streak", f"{st.session_state.get('current_streak', 0)}d")

# Achievement badges
points = st.session_state.get("seyal_points", 0)
if points >= 100:
    st.sidebar.success("🏆 Century Achiever!")
if points >= 500:
    st.sidebar.success("⭐ Action Master!")
if st.session_state.get("current_streak", 0) >= 7:
    st.sidebar.success("🔥 Week Warrior!")

# Main Interface Tabs
tab1, tab2, tab3, tab4 = st.tabs(["💬 CHAT", "🗺️ PLAN", "⚡ ACTION", "🧠 REFLECT"])

# --- TAB 1: CONVERSATIONAL CHAT (Now First!) ---
with tab1:
    st.subheader("💬 Talk to Seyal")
    
    # Quick action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🌅 Morning Briefing", use_container_width=True):
            st.session_state["quick_action"] = "morning"
    with col2:
        if st.button("🌙 Evening Check-in", use_container_width=True):
            st.session_state["quick_action"] = "evening"
    with col3:
        if st.button("💪 Need Motivation", use_container_width=True):
            st.session_state["quick_action"] = "motivation"
    
    st.markdown("---")
    
    # Display chat messages
    chat_container = st.container()
    
    with chat_container:
        if st.session_state.get("chat_messages"):
            for msg in st.session_state["chat_messages"]:
                if msg["role"] == "user":
                    st.chat_message("user").write(msg["content"])
                else:
                    st.chat_message("assistant", avatar="⚡").write(msg["content"])
        else:
            # Welcome message
            with st.chat_message("assistant", avatar="⚡"):
                st.write("Hey there! I'm Seyal, your AI action partner. 👋")
                st.write("I'm here to help you achieve your goals through daily action and support.")
                st.write("What would you like to work on today?")
    
    # Handle quick actions
    if st.session_state.get("quick_action"):
        action = st.session_state["quick_action"]
        
        if action == "morning":
            user_msg = "Give me my morning briefing for today"
        elif action == "evening":
            user_msg = "Let's do an evening reflection on my day"
        elif action == "motivation":
            user_msg = "I need some motivation right now"
        
        st.session_state["chat_messages"].append({"role": "user", "content": user_msg})
        
        with st.spinner("Seyal is thinking..."):
            try:
                conv_agent = get_conversation_agent()
                context = memory.get_history_context()
                
                # Build conversation history
                conv_history = ""
                for msg in st.session_state["chat_messages"][-5:]:
                    role = "User" if msg["role"] == "user" else "Seyal"
                    conv_history += f"\n{role}: {msg['content']}\n"
                
                full_prompt = f"{context}\n\nRecent Conversation:\n{conv_history}\n\nRespond naturally to the user's latest message."
                response = conv_agent.generate_content(full_prompt)
                
                st.session_state["chat_messages"].append({"role": "assistant", "content": response.text})
                st.session_state["quick_action"] = None
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {e}")
                st.session_state["quick_action"] = None
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message
        st.session_state["chat_messages"].append({"role": "user", "content": prompt})
        
        with st.spinner("Seyal is thinking..."):
            try:
                conv_agent = get_conversation_agent()
                context = memory.get_history_context()
                
                # Build conversation history
                conv_history = ""
                for msg in st.session_state["chat_messages"][-5:]:
                    role = "User" if msg["role"] == "user" else "Seyal"
                    conv_history += f"\n{role}: {msg['content']}\n"
                
                full_prompt = f"{context}\n\nRecent Conversation:\n{conv_history}\n\nRespond naturally and conversationally."
                response = conv_agent.generate_content(full_prompt)
                
                st.session_state["chat_messages"].append({"role": "assistant", "content": response.text})
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {e}")

# --- TAB 2: PLANNER ---
with tab2:
    st.subheader("🎯 Let's Define Your Goal")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        user_goal = st.text_area(
            "What ambitious goal do you want to achieve?", 
            placeholder="E.g., Learn Python and deploy a data science project in 4 weeks.",
            height=100
        )
    
    with col2:
        user_why = st.text_area(
            "Why does this matter to you? 💭", 
            placeholder="E.g., I want to change careers and finally feel fulfilled in my work",
            value=st.session_state.get("core_why", ""),
            height=100,
            help="This helps Seyal motivate you when things get tough!"
        )
    
    if st.button("✨ Create My Roadmap", type="primary", use_container_width=True):
        if not user_goal:
            st.error("Please tell me what goal you want to achieve!")
        else:
            # Save the why
            if user_why:
                st.session_state["core_why"] = user_why
            
            with st.spinner("Creating your personalized roadmap..."):
                try:
                    planner = get_planner_agent()
                    chat = planner.start_chat(enable_automatic_function_calling=True)
                    
                    prompt = f"My goal is: {user_goal}"
                    if user_why:
                        prompt += f"\n\nThis matters to me because: {user_why}"
                    
                    response = chat.send_message(prompt)
                    st.success("🎯 Your roadmap is ready!")
                    st.info(response.text)
                except Exception as e:
                    st.error(f"Error during planning: {e}")

    # Display Current Roadmap
    if st.session_state["roadmap"]:
        st.markdown("---")
        st.markdown("### 📍 Your Roadmap")
        for i, m in enumerate(st.session_state["roadmap"]):
            st.success(f"**Step {i+1}:** {m}")
    
    # Display Why
    if st.session_state.get("core_why"):
        st.markdown("---")
        st.markdown("### 💭 Your Why")
        st.info(f"*\"{st.session_state['core_why']}\"*")

# --- TAB 3: ACTION ---
with tab3:
    col1, col2 = st.columns([1, 1])
    
    # Left: Task Generation
    with col1:
        st.markdown("### 📋 Today's Tasks")
        
        if st.button("🎯 Generate Tasks for Today", type="primary", use_container_width=True):
            with st.spinner("Breaking down your plan into actionable tasks..."):
                try:
                    task_agent = get_task_agent()
                    context = memory.get_history_context()
                    response = task_agent.generate_content(
                        f"{context}\n\nGenerate detailed, executable tasks for today based on the next milestone in the plan."
                    )
                    
                    # Parse the JSON response
                    response_text = response.text.strip()
                    if response_text.startswith("```"):
                        response_text = response_text.split("```")[1]
                        if response_text.startswith("json"):
                            response_text = response_text[4:]
                    
                    tasks = json.loads(response_text)
                    st.session_state["tasks"] = tasks
                    
                    # Initialize task status
                    st.session_state["task_status"] = {}
                    for i, task in enumerate(tasks):
                        st.session_state["task_status"][f"task_{i}"] = False
                    
                    st.success("✅ Your tasks are ready!")
                    st.balloons()
                    
                    # Generate nudge for first task
                    if tasks and st.session_state.get("logs"):
                        recent_mood = st.session_state["logs"][-1].get("mood", "Neutral")
                        nudge = memory.generate_contextual_nudge(tasks[0], recent_mood)
                        st.info(f"💡 **Nudge:** {nudge}")
                    
                except Exception as e:
                    st.error(f"Error generating tasks: {e}")
                    st.session_state["tasks"] = []
        
        # Display tasks with checkboxes
        if st.session_state["tasks"]:
            st.markdown("---")
            st.markdown("**Check off as you complete:**")
            for i, task in enumerate(st.session_state["tasks"]):
                task_key = f"task_{i}"
                if task_key not in st.session_state["task_status"]:
                    st.session_state["task_status"][task_key] = False
                
                is_checked = st.checkbox(
                    task, 
                    key=task_key, 
                    value=st.session_state["task_status"][task_key]
                )
                st.session_state["task_status"][task_key] = is_checked
            
            # Show incomplete tasks from yesterday
            if st.session_state.get("pending_tasks"):
                st.markdown("---")
                st.markdown("**⏰ Carried Over from Yesterday:**")
                for task in st.session_state["pending_tasks"]:
                    st.warning(f"• {task}")

    # Right: Logging
    with col2:
        st.markdown("### 📝 Log Your Day")
        log_input = st.text_area(
            "How did today go? What did you accomplish?", 
            key="daily_log_text",
            height=150,
            placeholder="Share your wins, challenges, and how you're feeling..."
        )
        mood_input = st.select_slider(
            "How's your energy today?", 
            ["Drained", "Bored", "Neutral", "Good", "Energetic"]
        )
        
        if st.button("💾 Save Progress", type="primary", use_container_width=True):
            if not log_input:
                st.warning("Tell me about your day first!")
            else:
                # Get completed tasks
                completed_tasks = [
                    st.session_state["tasks"][i] 
                    for i in range(len(st.session_state["tasks"])) 
                    if st.session_state["task_status"].get(f"task_{i}", False)
                ]
                
                # Get incomplete tasks
                incomplete_tasks = [
                    st.session_state["tasks"][i] 
                    for i in range(len(st.session_state["tasks"])) 
                    if not st.session_state["task_status"].get(f"task_{i}", False)
                ]
                st.session_state["pending_tasks"] = incomplete_tasks
                
                msg = memory.log_daily_update(log_input, mood_input, completed_tasks)
                st.success(msg)
                
                # Show completion summary
                if completed_tasks:
                    st.balloons()
                    st.info(f"✅ You completed {len(completed_tasks)} task(s) today!")
                
                # Offer to reschedule incomplete tasks
                if incomplete_tasks:
                    st.warning(f"⏰ {len(incomplete_tasks)} task(s) will carry over to tomorrow")

# --- TAB 4: REFLECT ---
with tab4:
    st.subheader("📊 Your Progress Insights")
    
    # Show what data is available
    total_logs = len(st.session_state["logs"])
    total_completed = sum(len(log.get("completed_tasks", [])) for log in st.session_state["logs"])
    
    if total_logs > 0:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📅 Days Logged", total_logs)
        with col2:
            st.metric("✅ Tasks Done", total_completed)
        with col3:
            avg_tasks = total_completed / total_logs if total_logs > 0 else 0
            st.metric("📈 Daily Avg", f"{avg_tasks:.1f}")
        with col4:
            st.metric("⚡ Total Points", st.session_state["seyal_points"])
        
        # Show recent activity preview
        with st.expander("📋 Recent Activity"):
            for log in reversed(st.session_state["logs"][-5:]):
                st.markdown(f"**{log.get('date')}** - Mood: {log.get('mood')}")
                completed = log.get('completed_tasks', [])
                if completed:
                    st.markdown(f"✅ Completed {len(completed)} task(s)")
                    for task in completed:
                        st.markdown(f"  • {task}")
                else:
                    st.markdown("⚠️ No tasks completed")
                st.markdown("---")
    
    if st.button("🧠 Get My Progress Report", type="primary", use_container_width=True):
        if len(st.session_state["logs"]) == 0:
            st.warning("📝 Start logging your daily progress first! Head to the ACTION tab to get started.")
        else:
            with st.spinner("🔍 Analyzing your progress patterns..."):
                try:
                    reflector = get_reflector_agent()
                    history_context = memory.get_history_context()
                    
                    prompt = f"""Analyze this user's progress and provide insights:

{history_context}

Create a warm, conversational progress report with:

1. 🏆 **Wins to Celebrate**
   - What they've accomplished (be specific!)
   - Progress toward their goal
   - Consistency and dedication

2. 📊 **Patterns I'm Seeing**
   - Mood and energy trends
   - Most productive days/times
   - Any obstacles or challenges
   - What's working well

3. 💪 **Let's Level Up**
   - What to focus on next
   - How to maintain momentum
   - Specific suggestions
   - Connection to their "why"

Write like you're talking to a friend - be encouraging, honest, and helpful!"""
                    
                    response = reflector.generate_content(prompt)
                    
                    st.markdown("---")
                    st.markdown("### 📊 Your SEYAL Progress Report")
                    st.info(response.text)
                    
                except Exception as e:
                    st.error(f"❌ Error generating report: {str(e)}")
    
    elif total_logs == 0:
        st.info("👋 Ready to start your journey? Head to the PLAN tab to set your goal, then log your daily progress in ACTION!")



# Footer
st.markdown("---")
st.caption("⚡ SEYAL - Your AI Action Partner")

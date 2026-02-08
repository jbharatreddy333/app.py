import streamlit as st
import google.generativeai as genai
import json
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# Voice mode imports (wrapped in try-except for optional installation)
try:
    from audio_recorder_streamlit import audio_recorder
    import speech_recognition as sr
    from gtts import gTTS
    import tempfile
    import os
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

# 1. Set the page title and the logo as the browser favicon
st.set_page_config(
    page_title="Seyal",
    page_icon="logo.jpg",  # This uses your logo.jpg file
    layout="wide"
)

# 2. Display the logo at the top of the app or in the sidebar
st.sidebar.image("logo.jpg", width=150)
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
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    api_key = st.sidebar.text_input("Enter Google Gemini API Key", type="password")
    
if not api_key:
    st.warning("⚠️ Please provide a Google Gemini API Key to run the agents.")
    st.stop()

# Initialize the Gemini Client
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
        nudge_agent = genai.GenerativeModel('gemini-2.0-flash-exp')
        
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
    """
    return genai.GenerativeModel(
        model_name='gemini-2.0-flash-exp',
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
        model_name='gemini-2.0-flash-exp',
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
    """
    return genai.GenerativeModel(
        model_name='gemini-2.0-flash-exp',
        system_instruction=system_instruction
    )

def get_conversation_agent():
    """Create conversational agent for morning/evening rituals."""
    system_instruction = """
    You are SEYAL's conversational interface. You help users through friendly dialogue.
    
    MORNING BRIEFING:
    - Review their plan for the day in a warm, encouraging way
    - Ask which task is their "frog" (hardest/most important to do first)
    - Suggest a realistic order based on their energy patterns from logs
    - Keep it under 3 conversational exchanges
    - Reference their "why" to motivate them
    
    EVENING REFLECTION:
    - Celebrate what got done (be specific about tasks)
    - Ask how they FEEL about their progress (emotional check-in)
    - If tasks were missed, ask why without judgment
    - Suggest ONE easy win for tomorrow to build momentum
    - Remind them of their streak or points if relevant
    
    GENERAL CONVERSATION:
    - Answer questions about their progress
    - Provide motivation when asked
    - Help them adjust plans if needed
    - Be encouraging but honest
    
    STYLE: 
    - Casual friend, not corporate coach
    - Use "we" language (we're in this together)
    - Ask ONE question at a time
    - Keep responses to 2-3 sentences max
    - Use emojis sparingly and naturally
    """
    return genai.GenerativeModel(
        model_name='gemini-2.0-flash-exp',
        system_instruction=system_instruction
    )


# --- 4. VOICE MODE FUNCTIONALITY ---

def render_voice_assistant():
    """Render voice assistant in sidebar."""
    if not VOICE_AVAILABLE:
        st.sidebar.warning("📦 Install voice packages:\n`pip install audio-recorder-streamlit SpeechRecognition gtts`")
        return
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎤 Voice Assistant")
    
    audio_bytes = audio_recorder(
        text="Click to talk to Seyal",
        recording_color="#e74c3c",
        neutral_color="#3498db",
        icon_name="microphone",
        icon_size="2x",
        pause_threshold=2.0,
        sample_rate=41000
    )
    
    if audio_bytes:
        # Save audio to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio_bytes)
            audio_path = f.name
        
        # Convert speech to text
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            try:
                user_text = recognizer.recognize_google(audio_data)
                st.sidebar.success(f"**You:** {user_text}")
                
                # Get conversation context
                context = memory.get_history_context()
                
                # Get AI response
                conv_agent = get_conversation_agent()
                full_prompt = f"{context}\n\nUser said: {user_text}"
                response = conv_agent.generate_content(full_prompt)
                
                st.sidebar.write(f"**Seyal:** {response.text}")
                
                # Save to conversation history
                st.session_state["conversation_history"].append({
                    "user": user_text,
                    "seyal": response.text,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                
                # Convert response to speech
                tts = gTTS(text=response.text, lang='en', slow=False)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as audio_file:
                    tts.save(audio_file.name)
                    st.sidebar.audio(audio_file.name, format='audio/mp3')
                
                # Cleanup temp files
                try:
                    os.unlink(audio_path)
                except:
                    pass
                    
            except sr.UnknownValueError:
                st.sidebar.error("🤔 Couldn't understand that. Please try again!")
            except sr.RequestError as e:
                st.sidebar.error(f"❌ Speech recognition error: {e}")
            except Exception as e:
                st.sidebar.error(f"❌ Error: {e}")


# --- 5. UI LAYOUT ---

st.title("⚡ SEYAL: The Action Agent")
st.caption("Your AI-Powered Action Partner with Voice, Gamification & Smart Insights")

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

# Voice Assistant
render_voice_assistant()

# Main Interface Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🗺️ PLAN", "⚡ ACTION", "🧠 REFLECT", "💬 CHAT"])

# --- TAB 1: PLANNER ---
with tab1:
    st.subheader("Define Your Goal & Your Why")
    
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
    
    if st.button("Generate Roadmap", type="primary"):
        if not user_goal:
            st.error("Please enter a goal.")
        else:
            # Save the why
            if user_why:
                st.session_state["core_why"] = user_why
            
            with st.spinner("Planner Agent is strategizing and saving milestones..."):
                try:
                    planner = get_planner_agent()
                    chat = planner.start_chat(enable_automatic_function_calling=True)
                    
                    prompt = f"My goal is: {user_goal}"
                    if user_why:
                        prompt += f"\n\nThis matters to me because: {user_why}"
                    
                    response = chat.send_message(prompt)
                    st.success("🎯 Roadmap created!")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"Error during planning: {e}")

    # Display Current Roadmap
    if st.session_state["roadmap"]:
        st.markdown("### 📍 Current Milestones")
        for i, m in enumerate(st.session_state["roadmap"]):
            st.info(f"**Milestone {i+1}:** {m}")
    
    # Display Why
    if st.session_state.get("core_why"):
        st.markdown("### 💭 Your Why")
        st.success(f"*\"{st.session_state['core_why']}\"*")

# --- TAB 2: ACTION ---
with tab2:
    col1, col2 = st.columns([1, 1])
    
    # Left: Task Generation
    with col1:
        st.markdown("### 📋 Daily Tasks")
        
        if st.button("🎯 Get Today's Tasks", type="primary"):
            with st.spinner("Task Agent is breaking down the plan..."):
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
                    
                    st.success("✅ Tasks generated!")
                    
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
            st.markdown("**Today's Tasks:**")
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
                st.markdown("**⏰ Pending from Yesterday:**")
                for task in st.session_state["pending_tasks"]:
                    st.warning(f"• {task}")

    # Right: Logging
    with col2:
        st.markdown("### 📝 Log Progress")
        log_input = st.text_area(
            "What did you complete today? Any challenges?", 
            key="daily_log_text",
            height=150,
            placeholder="Share your progress, wins, and any obstacles you faced..."
        )
        mood_input = st.select_slider(
            "How are you feeling?", 
            ["Drained", "Bored", "Neutral", "Good", "Energetic"]
        )
        
        if st.button("💾 Log Update", type="primary"):
            if not log_input:
                st.warning("Please enter your daily progress.")
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
                    st.info(f"✅ Logged {len(completed_tasks)} completed task(s)")
                
                # Offer to reschedule incomplete tasks
                if incomplete_tasks:
                    st.warning(f"⏰ {len(incomplete_tasks)} task(s) not completed")
                    st.info("💡 These will appear as pending tasks tomorrow")

# --- TAB 3: REFLECT ---
with tab3:
    st.subheader("📊 Day-by-Day Progress Analysis")
    st.info("The Reflector Agent analyzes your **daily tasks, mood patterns, and progress** to provide actionable insights.")
    
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
            st.metric("📈 Avg/Day", f"{avg_tasks:.1f}")
        with col4:
            st.metric("⚡ Points", st.session_state["seyal_points"])
        
        # Show recent activity preview
        with st.expander("📋 Recent Activity Preview"):
            for log in st.session_state["logs"][-3:]:
                st.markdown(f"**{log.get('date')}** - Mood: {log.get('mood')}")
                completed = log.get('completed_tasks', [])
                if completed:
                    st.markdown(f"✅ Completed: {len(completed)} task(s)")
                    for task in completed:
                        st.markdown(f"  • {task}")
                else:
                    st.markdown("⚠️ No tasks marked complete")
    
    if st.button("🧠 Analyze My Progress", type="primary"):
        if len(st.session_state["logs"]) == 0 and "User started" in st.session_state["long_term_summary"]:
            st.warning("📝 Not enough data yet. Log at least one day of progress before getting insights!")
        else:
            with st.spinner("🔍 Reflector Agent is analyzing your day-by-day progress..."):
                try:
                    reflector = get_reflector_agent()
                    history_context = memory.get_history_context()
                    
                    prompt = f"""Analyze this user's day-by-day progress and generate a comprehensive SEYAL Weekly Report.

{history_context}

Please provide a detailed analysis with:

1. 🏆 **Daily Wins Recap**
   - Go through each day and summarize what they accomplished
   - Mention specific tasks completed
   - Celebrate their progress

2. ⚠️ **Patterns & Insights Detected**
   - How did their mood change day to day?
   - Which days were most productive?
   - Any concerning patterns or obstacles?
   - Consistency in showing up?

3. 🚀 **Strategic Next Steps**
   - Based on their plan, what should they focus on next?
   - How can they maintain or improve momentum?
   - Specific actionable recommendations
   - Connect to their core "why" for motivation

Be encouraging, specific, and reference actual days and tasks!"""
                    
                    response = reflector.generate_content(prompt)
                    
                    st.markdown("---")
                    st.markdown("### 📊 Your SEYAL Progress Report")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"❌ Error generating reflection: {str(e)}")
                    with st.expander("🔍 Debug Information"):
                        st.exception(e)
    
    elif total_logs == 0:
        st.info("👋 Get started by creating a plan in the PLAN tab, then log your daily progress in the ACTION tab. Come back here to get insights!")

# --- TAB 4: CHAT ---
with tab4:
    st.subheader("💬 Chat with Seyal")
    st.caption("Have a conversation about your goals, progress, or get motivation!")
    
    # Morning/Evening Ritual Buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🌅 Morning Briefing", type="secondary"):
            st.session_state["chat_mode"] = "morning"
    with col2:
        if st.button("🌙 Evening Reflection", type="secondary"):
            st.session_state["chat_mode"] = "evening"
    
    # Chat interface
    chat_input = st.text_area(
        "Message Seyal...",
        placeholder="Ask me anything about your goals, progress, or just chat!",
        height=100,
        key="chat_input_box"
    )
    
    if st.button("Send", type="primary") or st.session_state.get("chat_mode"):
        mode = st.session_state.get("chat_mode", "general")
        
        # Prepare prompt based on mode
        if mode == "morning":
            user_message = "Give me a morning briefing for today."
            st.session_state["chat_mode"] = None
        elif mode == "evening":
            user_message = "Help me reflect on today's progress."
            st.session_state["chat_mode"] = None
        else:
            user_message = chat_input
        
        if user_message:
            with st.spinner("Seyal is thinking..."):
                try:
                    conv_agent = get_conversation_agent()
                    context = memory.get_history_context()
                    
                    # Add conversation history
                    conv_history = ""
                    if st.session_state.get("conversation_history"):
                        conv_history = "\n## Recent Conversation:\n"
                        for msg in st.session_state["conversation_history"][-3:]:
                            conv_history += f"\nUser: {msg['user']}\nSeyal: {msg['seyal']}\n"
                    
                    full_prompt = f"{context}\n{conv_history}\n\nUser said: {user_message}"
                    response = conv_agent.generate_content(full_prompt)
                    
                    # Save to conversation history
                    st.session_state["conversation_history"].append({
                        "user": user_message,
                        "seyal": response.text,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    
                    # Display conversation
                    st.markdown("---")
                    st.markdown(f"**You:** {user_message}")
                    st.markdown(f"**Seyal:** {response.text}")
                    
                except Exception as e:
                    st.error(f"Error: {e}")
    
    # Show conversation history
    if st.session_state.get("conversation_history"):
        with st.expander("💬 Conversation History"):
            for msg in reversed(st.session_state["conversation_history"][-10:]):
                st.markdown(f"**[{msg['timestamp']}]**")
                st.markdown(f"**You:** {msg['user']}")
                st.markdown(f"**Seyal:** {msg['seyal']}")
                st.markdown("---")

# --- DEBUG VIEW ---
with st.expander("🔍 Internals (Memory State and Observability)"):
    st.json({
        "Roadmap": st.session_state["roadmap"],
        "Core Why": st.session_state.get("core_why", ""),
        "Current Tasks": st.session_state["tasks"],
        "Task Completion Status": st.session_state["task_status"],
        "Pending Tasks": st.session_state.get("pending_tasks", []),
        "Recent Detailed Logs": st.session_state["logs"],
        "Long Term Memory Summary": st.session_state["long_term_summary"],
        "Seyal Points": st.session_state["seyal_points"],
        "Current Streak": st.session_state["current_streak"],
        "Last Log Date": st.session_state.get("last_log_date"),
        "Conversation History Count": len(st.session_state.get("conversation_history", []))
    })

# Footer
st.markdown("---")
st.caption("⚡ SEYAL - Your AI Action Partner")

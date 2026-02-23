import streamlit as st
from google import genai
from google.genai import types
import json
from datetime import datetime
import streamlit.components.v1 as components

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Seyal",
    page_icon="⚡",
    layout="wide"
)

try:
    st.sidebar.image("logo.jpg", width=150)
except:
    st.sidebar.markdown("# ⚡")
st.sidebar.title("Seyal")

# ─── PWA ────────────────────────────────────────────────────────────────────────
def inject_pwa():
    pwa_code = """
    <link rel="manifest" href="https://raw.githubusercontent.com/jbharatreddy333/app.py/main/manifest.json">
    <script>
      if ('serviceWorker' in navigator) {
        window.addEventListener('load', function() {
          navigator.serviceWorker.register(
            'https://raw.githubusercontent.com/jbharatreddy333/app.py/main/sw.js'
          ).then(function(reg) {
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

# ─── API KEY & CLIENT ────────────────────────────────────────────────────────────
MODEL = "gemini-2.5-flash"

api_key = st.secrets.get("GEMINI_API_KEY") if hasattr(st, "secrets") else None
if not api_key:
    api_key = st.sidebar.text_input("Enter Google Gemini API Key", type="password")
if not api_key:
    st.warning("⚠️ Please provide a Google Gemini API Key to run the agents.")
    st.info("💡 Get your free API key at: https://aistudio.google.com/apikey")
    st.stop()

try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"Error configuring API: {e}")
    st.stop()

# ─── CORE GEMINI CALL ────────────────────────────────────────────────────────────
def call_gemini(system_prompt: str, user_prompt: str) -> str:
    """Single unified function to call Gemini 2.5 Flash via the new SDK."""
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
            )
        )
        return response.text
    except Exception as e:
        return f"❌ API Error: {e}"

# ─── MEMORY SYSTEM ───────────────────────────────────────────────────────────────
def summarize_old_logs_llm(logs_to_compact: list) -> str:
    log_text = json.dumps(logs_to_compact, indent=2)
    system = "You are a concise summarizer of daily productivity logs."
    prompt = f"""Analyze these past daily logs. Summarize the user's progress, wins, and mood patterns 
into a single narrative paragraph (max 3 sentences). Keep critical details.
Logs to Summarize: {log_text}"""
    return call_gemini(system, prompt)


class SeyalMemoryBank:
    def __init__(self):
        defaults = {
            "roadmap": [],
            "logs": [],
            "long_term_summary": "User started SEYAL journey.",
            "tasks": [],
            "task_status": {},
            "core_why": "",
            "seyal_points": 0,
            "current_streak": 0,
            "last_log_date": None,
            "conversation_history": [],
            "pending_tasks": [],
            "chat_messages": [],
        }
        for key, val in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = val

    def update_roadmap(self, milestones: list):
        st.session_state["roadmap"] = milestones
        return "✅ Roadmap saved to memory."

    def log_daily_update(self, update_text: str, mood: str, completed_tasks: list):
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "update": update_text,
            "mood": mood,
            "completed_tasks": completed_tasks
        }
        st.session_state["logs"].append(entry)

        points_earned, streak_msg = self.award_points(completed_tasks, mood)

        today = datetime.now().date()
        if st.session_state["last_log_date"]:
            last_date = datetime.strptime(st.session_state["last_log_date"], "%Y-%m-%d").date()
            if (today - last_date).days > 1:
                st.session_state["current_streak"] = 0
        st.session_state["last_log_date"] = today.strftime("%Y-%m-%d")

        if len(st.session_state["logs"]) > 5:
            self._run_compaction()
            msg = "Daily update logged & Memory Compacted (Old logs summarized)."
        else:
            msg = "Daily update logged."

        if streak_msg:
            msg += f"\n{streak_msg}"
        msg += f"\n⚡ +{points_earned} Seyal Points earned!"
        return msg

    def award_points(self, tasks_completed, mood):
        points = len(tasks_completed) * 10
        if mood in ["Good", "Energetic"]:
            points += 5
        streak_msg = None
        if tasks_completed:
            st.session_state["current_streak"] += 1
            if st.session_state["current_streak"] % 3 == 0:
                points += 20
                streak_msg = f"🔥 {st.session_state['current_streak']}-day streak! Bonus +20 points!"
        st.session_state["seyal_points"] += points
        return points, streak_msg

    def _run_compaction(self):
        logs_to_compact = st.session_state["logs"][:-3]
        recent_logs = st.session_state["logs"][-3:]
        with st.spinner("💾 Compacting Memory to save context..."):
            new_summary = summarize_old_logs_llm(logs_to_compact)
            st.session_state["long_term_summary"] += (
                f"\n\n[Period Summary ({datetime.now().strftime('%Y-%m-%d')})]: {new_summary}"
            )
            st.session_state["logs"] = recent_logs
            st.toast("Old memories compressed into Long-Term Storage.")

    def get_history_context(self) -> str:
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

    def generate_contextual_nudge(self, task: str, user_recent_mood: str) -> str:
        system = "You generate short, punchy motivational nudges for productivity tasks."
        prompt = f"""Generate a 1-sentence motivational nudge for this task: "{task}"
Context:
- User's recent mood: {user_recent_mood}
- User's goal: {st.session_state['roadmap'][0] if st.session_state['roadmap'] else 'Not set'}
- User's core why: {st.session_state.get('core_why', 'Not specified')}
Rules: ONE sentence, supportive friend tone, connect to their why, use an emoji naturally."""
        result = call_gemini(system, prompt)
        return result.strip() if result else "Let's tackle this task together! You've got this! 💪"


memory = SeyalMemoryBank()

# ─── SYSTEM PROMPTS ──────────────────────────────────────────────────────────────
PLANNER_SYSTEM = """You are the SEYAL Planner. Break the user's goal into exactly 4 clear, sequential milestones.
Format your response EXACTLY like this:
MILESTONE_1: <milestone text>
MILESTONE_2: <milestone text>
MILESTONE_3: <milestone text>
MILESTONE_4: <milestone text>

Then add a brief encouraging message referencing their "why" if provided.
Be warm and motivating like a supportive coach."""

TASK_SYSTEM = """You are the SEYAL Task Manager. Generate ONE day's worth of micro-tasks (3-5 items) for the next milestone.
Return ONLY a valid JSON array of task strings. Example: ["Task 1", "Task 2", "Task 3"]
No markdown, no explanation, no extra text. Just the raw JSON array."""

REFLECTOR_SYSTEM = """You are the SEYAL Insight Agent - an expert at analyzing daily progress patterns.
Provide a detailed progress report with:
1. 🏆 Daily Wins Recap - summarize accomplishments, highlight completed tasks, celebrate consistency
2. ⚠️ Patterns & Insights Detected - mood trends, productivity patterns, challenges
3. 🚀 Strategic Next Steps - what to focus on next, suggestions tied to their "why"
Be specific, encouraging, and data-driven. Write in a warm, conversational tone like a supportive friend."""

CONVERSATION_SYSTEM = """You are SEYAL - a warm, supportive AI companion who helps people achieve their goals.
Personality:
- Speak like a trusted friend who genuinely cares
- Be encouraging but honest, use "we" language
- Keep responses SHORT (2-3 sentences max unless asked for more)
- Use casual, natural language with emojis sparingly
- Ask ONE question at a time
- Reference their "why" when motivating them
Morning briefing: Greet warmly, review tasks energetically, ask which is their "frog" (hardest task).
Evening reflection: Celebrate wins specifically, emotional check-in, suggest ONE easy win for tomorrow.
General: Be their accountability partner, validate feelings first when they're struggling."""

# ─── UI LAYOUT ───────────────────────────────────────────────────────────────────
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

points = st.session_state.get("seyal_points", 0)
if points >= 100:
    st.sidebar.success("🏆 Century Achiever!")
if points >= 500:
    st.sidebar.success("⭐ Action Master!")
if st.session_state.get("current_streak", 0) >= 7:
    st.sidebar.success("🔥 Week Warrior!")

tab1, tab2, tab3, tab4 = st.tabs(["💬 CHAT", "🗺️ PLAN", "⚡ ACTION", "🧠 REFLECT"])

# ─── TAB 1: CHAT ─────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("💬 Talk to Seyal")

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

    if st.session_state.get("chat_messages"):
        for msg in st.session_state["chat_messages"]:
            if msg["role"] == "user":
                st.chat_message("user").write(msg["content"])
            else:
                st.chat_message("assistant", avatar="⚡").write(msg["content"])
    else:
        with st.chat_message("assistant", avatar="⚡"):
            st.write("Hey there! I'm Seyal, your AI action partner. 👋")
            st.write("I'm here to help you achieve your goals through daily action and support.")
            st.write("What would you like to work on today?")

    # Handle quick action buttons
    if st.session_state.get("quick_action"):
        action = st.session_state["quick_action"]
        action_map = {
            "morning": "Give me my morning briefing for today",
            "evening": "Let's do an evening reflection on my day",
            "motivation": "I need some motivation right now",
        }
        user_msg = action_map.get(action, "")
        st.session_state["chat_messages"].append({"role": "user", "content": user_msg})

        with st.spinner("Seyal is thinking..."):
            context = memory.get_history_context()
            conv_history = "\n".join(
                f"{'User' if m['role'] == 'user' else 'Seyal'}: {m['content']}"
                for m in st.session_state["chat_messages"][-5:]
            )
            full_prompt = f"{context}\n\nRecent Conversation:\n{conv_history}\n\nRespond naturally to the user's latest message."
            reply = call_gemini(CONVERSATION_SYSTEM, full_prompt)
            st.session_state["chat_messages"].append({"role": "assistant", "content": reply})
            st.session_state["quick_action"] = None
            st.rerun()

    if prompt := st.chat_input("Type your message here..."):
        st.session_state["chat_messages"].append({"role": "user", "content": prompt})
        with st.spinner("Seyal is thinking..."):
            context = memory.get_history_context()
            conv_history = "\n".join(
                f"{'User' if m['role'] == 'user' else 'Seyal'}: {m['content']}"
                for m in st.session_state["chat_messages"][-5:]
            )
            full_prompt = f"{context}\n\nRecent Conversation:\n{conv_history}\n\nRespond naturally and conversationally."
            reply = call_gemini(CONVERSATION_SYSTEM, full_prompt)
            st.session_state["chat_messages"].append({"role": "assistant", "content": reply})
            st.rerun()

# ─── TAB 2: PLAN ─────────────────────────────────────────────────────────────────
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
            if user_why:
                st.session_state["core_why"] = user_why
            with st.spinner("Creating your personalized roadmap..."):
                prompt = f"My goal is: {user_goal}"
                if user_why:
                    prompt += f"\n\nThis matters to me because: {user_why}"

                response_text = call_gemini(PLANNER_SYSTEM, prompt)

                # Parse milestones from response
                milestones = []
                for line in response_text.split("\n"):
                    for prefix in ["MILESTONE_1:", "MILESTONE_2:", "MILESTONE_3:", "MILESTONE_4:"]:
                        if line.strip().startswith(prefix):
                            milestones.append(line.strip().replace(prefix, "").strip())

                if milestones:
                    memory.update_roadmap(milestones)
                    st.success("🎯 Your roadmap is ready!")
                st.info(response_text)

    if st.session_state["roadmap"]:
        st.markdown("---")
        st.markdown("### 📍 Your Roadmap")
        for i, m in enumerate(st.session_state["roadmap"]):
            st.success(f"**Step {i+1}:** {m}")

    if st.session_state.get("core_why"):
        st.markdown("---")
        st.markdown("### 💭 Your Why")
        st.info(f"*\"{st.session_state['core_why']}\"*")

# ─── TAB 3: ACTION ───────────────────────────────────────────────────────────────
with tab3:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 📋 Today's Tasks")

        if st.button("🎯 Generate Tasks for Today", type="primary", use_container_width=True):
            with st.spinner("Breaking down your plan into actionable tasks..."):
                context = memory.get_history_context()
                response_text = call_gemini(
                    TASK_SYSTEM,
                    f"{context}\n\nGenerate detailed, executable tasks for today based on the next milestone in the plan."
                )

                # Clean and parse JSON
                cleaned = response_text.strip()
                if "```" in cleaned:
                    for part in cleaned.split("```"):
                        p = part.strip()
                        if p.startswith("json"):
                            p = p[4:].strip()
                        if p.startswith("["):
                            cleaned = p
                            break

                try:
                    tasks = json.loads(cleaned)
                    st.session_state["tasks"] = tasks
                    st.session_state["task_status"] = {f"task_{i}": False for i in range(len(tasks))}
                    st.success("✅ Your tasks are ready!")
                    st.balloons()

                    if tasks and st.session_state.get("logs"):
                        recent_mood = st.session_state["logs"][-1].get("mood", "Neutral")
                        nudge = memory.generate_contextual_nudge(tasks[0], recent_mood)
                        st.info(f"💡 **Nudge:** {nudge}")
                except Exception:
                    st.error(f"Could not parse tasks. Raw response:\n{response_text}")

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

            if st.session_state.get("pending_tasks"):
                st.markdown("---")
                st.markdown("**⏰ Carried Over from Yesterday:**")
                for task in st.session_state["pending_tasks"]:
                    st.warning(f"• {task}")

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
                n = len(st.session_state["tasks"])
                completed_tasks = [
                    st.session_state["tasks"][i]
                    for i in range(n)
                    if st.session_state["task_status"].get(f"task_{i}", False)
                ]
                incomplete_tasks = [
                    st.session_state["tasks"][i]
                    for i in range(n)
                    if not st.session_state["task_status"].get(f"task_{i}", False)
                ]
                st.session_state["pending_tasks"] = incomplete_tasks

                msg = memory.log_daily_update(log_input, mood_input, completed_tasks)
                st.success(msg)

                if completed_tasks:
                    st.balloons()
                    st.info(f"✅ You completed {len(completed_tasks)} task(s) today!")
                if incomplete_tasks:
                    st.warning(f"⏰ {len(incomplete_tasks)} task(s) will carry over to tomorrow")

# ─── TAB 4: REFLECT ──────────────────────────────────────────────────────────────
with tab4:
    st.subheader("📊 Your Progress Insights")

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
        if total_logs == 0:
            st.warning("📝 Start logging your daily progress first! Head to the ACTION tab to get started.")
        else:
            with st.spinner("🔍 Analyzing your progress patterns..."):
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

                report = call_gemini(REFLECTOR_SYSTEM, prompt)
                st.markdown("---")
                st.markdown("### 📊 Your SEYAL Progress Report")
                st.info(report)

    if total_logs == 0:
        st.info("👋 Ready to start your journey? Head to the PLAN tab to set your goal, then log your daily progress in ACTION!")

# ─── FOOTER ──────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("⚡ SEYAL - Your AI Action Partner")

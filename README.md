SEYAL is built as a single-model, multi-agent execution system that runs entirely on top of Google Gemini and Streamlit. Even though only one LLM model is used, SEYAL creates separate “agents” by assigning each one a unique system instruction, tools, and responsibilities. Together, they form a coordinated pipeline that transforms goals into actions, logs progress, and produces insight reports.

The architecture is structured around four core layers:
Interface Layer → Agent Layer → Tooling Layer → Memory Layer
which are tied together by a lightweight implicit orchestrator, implemented through Streamlit’s event-driven workflow.




1. Interface Layer (Streamlit App)

SEYAL uses a modular three-tab UI that naturally maps the execution loop:

PLAN Tab → captures the user’s goal and triggers the Planner Agent.

ACTION Tab → shows daily tasks, tracks completion checkboxes, and logs daily updates.

REFLECT Tab → triggers the Insight Agent to analyze behavior, tasks, and moods.


The interface is reactive, meaning user interactions automatically trigger the right agents with the right context without requiring an explicit orchestration layer.


2. Agent Layer (LLM Roles using Gemini)

Although SEYAL uses only one Gemini model, three distinct agent personas are formed:

🧭 Planner Agent

Breaks user goals into four structured milestones.

Write the finalized roadmap to memory using the update_roadmap tool.

Uses gemini-2.5-flash for fast reasoning.


📋 Task Agent

Takes milestones + long-term summary and generates 3–4 micro tasks for the day.

Returns tasks in pure JSON, ensuring they can be programmatically consumed.

Also runs on gemini-2.5-flash.


🧠 Insight Agent

Performs deep behavioral analysis over:

Daily logs

Mood patterns

Completed tasks

Overall plan

Long-term summary


Produces a detailed weekly-style progress report.

Uses gemini-2.5-pro for richer reasoning quality.


Each agent exists as a separate GenerativeModel instance with unique system prompts and optional tools, turning a single model into a multi-agent ecosystem.



3. Tooling Layer (Function Calling)

SEYAL integrates custom tools using Gemini’s function calling mechanism.
Right now, two tools form the backbone of the system:

🔧 Roadmap Tool

update_roadmap(milestones: list)
Stores milestone structures into Streamlit session memory.

Used exclusively by the Planner Agent.

📝 Log Store Tool

Part of the SeyalMemoryBank, this tool:

Saves daily updates

Tracks completed tasks

Records mood

Triggers context compaction when logs grow too large


These tools ensure the system behaves like a true execution engine instead of just a chain of text prompts.



4. Memory Layer (State + Context Compaction)

SEYAL uses a hybrid memory system built around Streamlit’s session_state, enhanced with context compaction to maintain long-term continuity.

Memory has three parts:

1. Roadmap Memory

Stores the user’s milestone plan.

2. Short-Term Log Memory

Stores recent detailed daily logs:

User text updates

Mood

Completed tasks

Timestamp


3. Long-Term Summary Memory

Older logs are automatically compressed using the LLM:

When logs exceed 5 entries

The oldest logs are summarized by Gemini into a compact narrative

The summary is appended to long-term memory

Only recent logs remain detailed



5. Implicit Orchestrator (Workflow Control)

SEYAL does not use an explicit agent coordinator file.
Instead, the orchestration emerges naturally from:

Streamlit’s tab flow

State stored in session_state

Tools binding

Back-and-forth message passing


Here's how the orchestration looks under the hood:

1. User enters a goal → Planner Agent → roadmap saved via tool


2. User moves to ACTION tab → Task Agent reads memory → returns today’s tasks


3. User checks boxes + logs update → MemoryBank stores log → may compact context


4. User moves to REFLECT tab → Insight Agent reads:

Roadmap

Long-term summary

Recent detailed logs.

5. Insight Agent returns a weekly-style analysis



# Instructions for Setup 

Here is a clean, polished, GitHub-ready Setup Instructions section you can paste directly into your README.md:



🛠️ Setup Instructions

Follow the steps below to run SEYAL: AI Action Companion locally on your system.



1️⃣ Clone the Repository

git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name



2️⃣ Create a Virtual Environment

macOS / Linux

python3 -m venv venv
source venv/bin/activate

Windows (PowerShell)

python -m venv venv
.\venv\Scripts\Activate.ps1



3️⃣ Install Dependencies

If the repo includes requirements.txt:

pip install -r requirements.txt

Otherwise:

pip install streamlit google-generative-ai



4️⃣ Add Your Gemini API Key (Required)

Recommended Method — Using Streamlit Secrets

Create:

.streamlit/secrets.toml

Add:

GEMINI_API_KEY = "your_gemini_api_key_here"

⚠️ Important: Add .streamlit/secrets.toml to .gitignore so you don’t expose your API key.


Alternative Method — Environment Variable

macOS / Linux

export GEMINI_API_KEY="your_gemini_api_key_here"

Windows (PowerShell)

setx GEMINI_API_KEY "your_gemini_api_key_here"


Last-Resort Method — Entering in Sidebar

If no key is found, the app allows entering the API key manually in the Streamlit sidebar.


5️⃣ Run the Application

streamlit run app.py

Streamlit will open automatically, or you can visit:

http://localhost:8501


6️⃣ Using the App

PLAN

Enter your goal

Click Generate Roadmap

The Planner agent creates 4 milestones and stores them in memory


ACTION

Click Get Today's Tasks

Complete tasks using checkboxes

Log your progress and mood

The Memory System auto-compacts older logs into summaries


REFLECT

Click Analyze My Progress

The Insight Agent generates a detailed weekly-style progress report



7️⃣ (Optional) Update Dependencies

If you modify or upgrade packages:

pip freeze > requirements.txt

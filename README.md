SEYAL is built as a single-model, multi-agent execution system that runs entirely on top of Google Gemini and Streamlit. Even though only one LLM model is used, SEYAL creates separate “agents” by assigning each one a unique system instruction, tools, and responsibilities. Together, they form a coordinated pipeline that transforms goals into actions, logs progress, and produces insight reports.

The architecture is structured around four core layers:
Interface Layer → Agent Layer → Tooling Layer → Memory Layer
which are tied together by a lightweight implicit orchestrator, implemented through Streamlit’s event-driven workflow.



## 🔧 SEYAL — Architecture & Setup Guide

SEYAL is a **single-model, multi-agent execution system** built entirely on top of **Google Gemini** and **Streamlit**. Even though only one LLM model is used, SEYAL forms a coordinated ecosystem of intelligent agents—each with its own responsibilities, tools, and memory system. Together, they help convert **goals → daily actions → meaningful insights**.

---

## 🧩 System Architecture

SEYAL operates through **four tightly-integrated layers**, connected by Streamlit’s event-driven workflow:

```
Interface Layer → Agent Layer → Tooling Layer → Memory Layer
```

### 1️⃣ Interface Layer — Streamlit App

A clean, three-tab UI driving the execution loop:

| Tab         | Purpose                             | Triggered Agent |
| ----------- | ----------------------------------- | --------------- |
| **PLAN**    | Capture goal & generate roadmap     | Planner Agent   |
| **ACTION**  | Show daily tasks & log progress     | Task Agent      |
| **REFLECT** | Weekly-style insights & mood trends | Insight Agent   |

The UI is **reactive**, meaning user actions automatically call the right agent with the right context—**no explicit orchestrator needed**.

---

### 2️⃣ Agent Layer — Multi-Agent Roles (Powered by Gemini)

Although only one LLM model is used, SEYAL creates three agent personas—each with unique system prompts & tool access:

| Agent                | Role                                             | Model Used       |
| -------------------- | ------------------------------------------------ | ---------------- |
| 🧭 **Planner Agent** | Breaks goals into 4 milestones & stores roadmap  | gemini-2.5-flash |
| 📋 **Task Agent**    | Generates 3–4 achievable micro-tasks for the day | gemini-2.5-flash |
| 🧠 **Insight Agent** | Behavioral + performance analysis across time    | gemini-2.5-pro   |

Each agent exists as a **separate GenerativeModel instance**, transforming a single LLM into a **multi-agent execution system**.

---

### 3️⃣ Tooling Layer — Function Calling

SEYAL integrates tools via Gemini’s function-calling:

| Tool                      | Used By       | Purpose                     |
| ------------------------- | ------------- | --------------------------- |
| 🔧 `update_roadmap`       | Planner Agent | Store milestone-based plans |
| 📝 Log Store (MemoryBank) | Task Agent    | Save tasks, logs & mood     |

These tools ensure SEYAL **acts**, not just generates text.

---

### 4️⃣ Memory Layer — State + Context Compaction

A hybrid memory system built around Streamlit’s `session_state`:

| Memory Type               | Stores                     |
| ------------------------- | -------------------------- |
| **Roadmap Memory**        | 4 structured milestones    |
| **Short-Term Log Memory** | Detailed last 5 logs       |
| **Long-Term Summary**     | Auto-summarized older logs |

When logs exceed 5 entries → **LLM compacts context** and preserves continuity.

---

## 🔄 Implicit Orchestrator — Lightweight Workflow Control

Instead of explicit orchestration:

* Tabs guide context flow
* Tools update memory
* Session state stores progress
* Agents read/write just-in-time information

Result → a **smooth end-to-end goal execution loop**.

---

## 🚀 Setup Instructions

Follow the steps to run **SEYAL: AI Action Companion** locally 👇

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2️⃣ Create a Virtual Environment

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell)**

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

Or, if not included:

```bash
pip install streamlit google-generative-ai
```

### 4️⃣ Add Your Gemini API Key *(Required)*

📌 Recommended — **Streamlit Secrets**
Create:

```
.streamlit/secrets.toml
```

Add:

```toml
GEMINI_API_KEY = "your_gemini_api_key_here"
```

⚠️ Make sure `.streamlit/secrets.toml` is added to `.gitignore`

---

Alternative — **Environment Variable**

| OS            | Command                            |
| ------------- | ---------------------------------- |
| macOS / Linux | `export GEMINI_API_KEY="your_key"` |
| Windows       | `setx GEMINI_API_KEY "your_key"`   |

---

Last-Resort — **Enter manually in Streamlit Sidebar**

---

### 5️⃣ Run the App

```bash
streamlit run app.py
```

Then open:

```
http://localhost:8501
```

---

## 🎯 How to Use SEYAL

| Step            | Tab     | What Happens                   |
| --------------- | ------- | ------------------------------ |
| 1️⃣ Set a goal  | PLAN    | Planner Agent builds roadmap   |
| 2️⃣ Take action | ACTION  | Daily tasks + progress logging |
| 3️⃣ Reflect     | REFLECT | Insight Agent generates report |

Consistent usage = **better insights + smarter planning** 📈


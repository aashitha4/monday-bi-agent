# 📊 Skylark BI Agent (Monday.com Intelligence)

> **An AI-powered Business Intelligence analyst that connects to Monday.com, cleans messy real-world data, and answers executive queries with Python-grade precision.**

---

## 🚀 Project Overview

The **Skylark BI Agent** solves the "Executive Data Problem": Founders need quick answers ("How is the Mining sector performing?"), but data is often trapped in messy Monday.com boards with inconsistent naming, mixed types, and formatting errors.

Instead of hallucinating answers, this Agent uses a **Dual-Stage Architecture**:
1.  **Stage 1 (Code Gen):** The AI (Llama-3.3 via Groq) writes a custom Python script to solve the user's specific question.
2.  **Stage 2 (Execution):** The system executes this code on the live Monday.com data to get a mathematically perfect result.
3.  **Stage 3 (Synthesis):** The AI interprets the raw number into a professional executive summary.

### 🌟 Key Features
* **Live Monday.com Sync:** Fetches real-time data from "Deals" and "Work Orders" boards.
* **Auto-Sanitization:** Automatically cleans currency symbols (`$`, `,`, `Rs`), normalizes headers, and handles `NaN` values.
* **"Quintillion Bug" Defense:** Includes a robust Sanity Filter that detects and zeroes out ID numbers disguised as currency (values > 1 Trillion).
* **Cross-Board Logic:** Can analyze Sales (Deals) and Operations (Work Orders) simultaneously.
* **Secure:** Uses Environment Variables for all credentials.

---

## 🛠️ Tech Stack

* **Frontend:** [Streamlit](https://streamlit.io/) (Python-based UI)
* **AI Engine:** Llama-3.3-70b (via [Groq API](https://groq.com/) for sub-second latency)
* **Data Processing:** Pandas (Vectorized operations for speed)
* **Integration:** Monday.com GraphQL API

---

## ⚙️ Local Setup Guide

Follow these steps to run the agent on your machine.

### 1. Clone & Install
```bash
git clone [https://github.com/your-username/skylark-bi-agent.git](https://github.com/your-username/skylark-bi-agent.git)
cd skylark-bi-agent

# Create virtual environment (Recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

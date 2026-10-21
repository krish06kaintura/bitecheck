# 🥗 BiteCheck India

### Autonomous Multimodal Multi-Agent Food Label & FSSAI Compliance Detective

BiteCheck India is an autonomous multi-agent AI system designed to audit Indian packaged food and beverage (FMCG) labels against **FSSAI (Food Safety and Standards Authority of India)** regulations and **ICMR-NIN (National Institute of Nutrition) 2024 Dietary Guidelines**.

---

## 🏗️ Architecture Overview

The system processes dual-photo uploads (Front claims + Back nutritional facts) through a 4-agent committee:

1. **Agent 1: Multimodal Vision & Label Ingestion (Gemini 2.5 Flash)**
   - Extracts dense, curved, and reflective packaging text.
   - Enforces a strict Pydantic data contract (`PackagingData`).
2. **Agent 2: FSSAI & Scientific Food Auditor (Deterministic Rule Engine)**
   - Zero-hallucination compliance checking across 12 statutory food science modules.
   - Decodes 35+ hidden sugar synonyms, INS/E-number additives, and grain purity ratios.
3. **Agent 3: Indian Consumer Sentiment Detective**
   - Scrapes and filters authentic discussions from Reddit India (`r/Fitness_India`) and Amazon India.
   - Applies an anti-bot hype filter to isolate genuine reports on taste, bloating, and mixability.
4. **Agent 4: Transparency Scorecard & Clean Swap Agent**
   - Computes the mathematical **FSSAI Honesty Score (0–100)**.
   - Highlights Whole-Pack intake multipliers and recommends clean Indian alternatives on Blinkit/Zepto.

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
- Python 3.11+
- Google Gemini API Key

### 2. Environment Setup
```bash
# Clone the repository
git clone https://github.com/krish06kaintura/bitecheck.git
cd bitecheck

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and insert your GEMINI_API_KEY
```

### 3. Running Sanity Tests
```bash
pytest tests/
```

---

## 📂 Project Structure
```
bitecheck/
├── data/                     # Knowledge bases (INS, sugars, clean swaps)
├── src/
│   └── bitecheck/
│       ├── config.py         # Type-safe application settings (Pydantic)
│       ├── logger.py         # Structured logging utilities
│       ├── schemas/          # Pydantic data contracts between agents
│       ├── agents/           # Specialized autonomous agents
│       ├── orchestrator/     # State graph and workflow coordinator
│       └── api/              # FastAPI backend endpoints
├── tests/                    # Unit, integration, and adversarial test suites
└── requirements.txt          # Production dependencies
```

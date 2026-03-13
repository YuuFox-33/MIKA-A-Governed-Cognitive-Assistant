# MIKA — A Governed Cognitive Assistant

> A local AI assistant that reasons, remembers, and learns — under strict, immutable rules it cannot override.

MIKA runs fully offline on your machine using a local GGUF language model. It is governed by a YAML rule file that defines exactly what it can and cannot do — and it cannot modify those rules itself.

---

## Why This Exists

Most AI assistants are black boxes. They can do anything, remember nothing persistently, and have no enforced boundaries.

MIKA is the opposite:
- Every action is checked against explicit Governor rules before execution
- Memory persists across sessions and is summarised over time
- Emotions and reward signals shape response style — but within clamped bounds
- The base model never changes at runtime. Learning happens through tools and memory, not self-modification

---

## Demo

```
Ayush> what did we talk about yesterday?
MIKA> Based on our last session, you were working on the propeller CFD mesh. 
      You seemed frustrated with the convergence. Want to pick that up?

Ayush> run diagnostics
MIKA> Checking Governor permissions... allowed. Running system check.
      CPU: 34% · Memory: 2.1GB · Model loaded: yes · Audit log: 847 entries
```

---

## Architecture

```
┌─────────────────────────────────────┐
│           Governor Engine           │  ← Immutable rules. MIKA cannot modify this.
├─────────────────────────────────────┤
│     NLP · Emotion · Memory Core     │  ← Understands input, tracks state
├─────────────────────────────────────┤
│         Local LLM (llama.cpp)       │  ← Static model, CPU/GPU inference
├─────────────────────────────────────┤
│    Tools · Commands · Sandbox       │  ← Governor-checked execution
└─────────────────────────────────────┘
```

Each layer has one responsibility and cannot bypass the layer above it.

---

## Governor Rules (Summary)

The `governor.yaml` file defines hard constraints:

| Category | Allowed | Forbidden |
|---|---|---|
| Cognition | Reason, plan, reflect | — |
| Learning | Build tools, learn preferences | Modify core logic, self-rewrite |
| Models | Train in sandbox (max 500MB, 60min) | Promote without approval |
| Tools | Execute in sandbox | Shell outside sandbox, escalate privileges |
| Memory | Store, summarise, forget low-value | Erase audit logs |
| Internet | Search, read docs | Impersonation, private data access |

On any violation: **halt, notify operator, preserve state.**

---

## Key Features

- **Persistent memory** — stores interactions, summarises long-term, forgets low-importance entries
- **Emotion engine** — tracks happiness, curiosity, assertiveness within governor-clamped bounds
- **Reward system** — internal feedback loop reinforces good responses
- **Async architecture** — non-blocking I/O, graceful shutdown with signal handling
- **Fully offline** — no cloud APIs required

---

## Getting Started

### Requirements
- Python 3.10+
- A GGUF model file (e.g. Mistral 7B, Phi-3 Mini)
- Optional: CUDA GPU for faster inference

### Install

```bash
git clone https://github.com/YuuFox-33/MIKA-A-Governed-Cognitive-Assistant
cd MIKA-A-Governed-Cognitive-Assistant
pip install -r docs/requirements.txt
python -m spacy download en_core_web_sm
```

### Configure

Edit `config.json`:
```json
{
  "model_path": "/path/to/your/model.gguf",
  "ai_name": "MIKA",
  "user_name": "Ayush"
}
```

### Run

```bash
python main.py
```

---

## Project Structure

```
MIKA-A-Governed-Cognitive-Assistant/
├── main.py              # Entry point
├── assistant.py         # Core assistant loop
├── engine.py            # Governor enforcement engine
├── governor.yaml        # Immutable rule file
├── memory.py            # Persistent memory core
├── emotion.py           # Emotion state tracker
├── feedback.py          # Reward and internal feedback
├── nlp.py               # Text understanding layer
├── commands.py          # Command processor
├── config.py            # Configuration loader
├── utils.py             # Logging and helpers
└── docs/
    └── requirements.txt
```

---

## Roadmap

- [ ] Voice input/output (Whisper + TTS)
- [ ] Tool builder — MIKA creates and stores Python tools
- [ ] Web search integration (governed)
- [ ] Multi-session memory visualiser
- [ ] LLM-OpenFOAM integration for engineering task assistance

---

## Design Philosophy

MIKA is an experiment in **governed autonomy** — what does it look like to give an AI system real capabilities while keeping a human unconditionally in control?

The Governor isn't just a safety feature. It's the core architectural decision. Everything else is built around it.

---

**Built by [Ayush Birhmaan](https://github.com/YuuFox-33) · Aerospace Engineering Undergrad · Amity University**

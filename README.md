# MIKA

MIKA is a **local, governed AI assistant** designed to reason, remember, and gradually improve **without modifying its own core logic**.

It runs fully offline, uses a local language model, and operates under explicit rules that strictly limit what it can and cannot do.

---

## What MIKA Is

- A local AI assistant you run on your own machine  
- Governed by clear, immutable rules  
- Capable of remembering conversations and adapting behavior  
- Designed to grow by building **tools and models**, not rewriting itself  

---

## What MIKA Is Not

- Not a cloud service  
- Not an always-online system  
- Not a self-modifying or self-authorizing AI  
- Not an uncontrolled autonomous agent  

---

## Core Principles

- **Governance first**  
  All actions are checked against explicit rules before execution.

- **Learning without fine-tuning**  
  The base language model never changes during runtime.

- **Human authority**  
  MIKA can propose actions but cannot escalate privileges on its own.

- **Local by design**  
  No external APIs or cloud dependencies required.

---

## How It Works

- Governor rules

- Governor engine

- MIKA core (reasoning + memory)

- Tools / models (sandboxed


Each layer has a single responsibility and cannot bypass the layer above it.

---

## Model Used

- Local LLM via **llama.cpp**
- GGUF model format
- CPU-first with optional GPU offload
- Used only for language understanding and reasoning

The model is **static**.  
All learning happens outside the model through experience and tools.

---

## Project Structure

- governance/ # Rules and enforcement

- mika_trial/ # Core assistant logic

- config.json # User configuration

- requirements.txt # Dependencies

---


---

## Getting Started

### Install dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm



# MIKA-A-Governed-Cognitive-Assistant

MIKA is an experimental governed cognitive agent designed to reason, reflect, and extend its own capabilities under explicit, immutable constraints.

Unlike conventional chatbots or fine-tuned AI models, MIKA does not improve by retraining itself.
Instead, it learns by building tools, models, and strategies—including neural networks—while operating inside a clearly defined governance framework.

This project explores how autonomy, learning, and safety can coexist in a single system.

✨ Core Principles

Governed Autonomy
MIKA operates under an immutable Governor that defines what actions are allowed, forbidden, or require approval.

Learning Without Fine-Tuning
The base language model remains static.
Learning happens through tool creation, strategy adaptation, and experience.

Internal Monologue
MIKA maintains a private reasoning layer used for self-reflection and decision-making.

Tool & Model Creation
When existing capabilities are insufficient, MIKA can propose and build new tools or neural networks (in sandboxed environments).

Human-Centric Authority
Final authority always remains with the human operator.

Model & Intelligence Stack
Base Language Model

llama.cpp (GGUF format)

Supports CPU and GPU offloading

Model is static (not fine-tuned during runtime)

MIKA uses the LLM strictly as a language and reasoning substrate, not as a learning mechanism.
Learning Philosophy
 No online fine-tuning
 No self-modifying core logic
 Experience-based learning
 Tool and model generation
 Strategy adaptation



🛡️Governance Model

MIKA follows a parent–child governance model:
The Governor defines non-negotiable rules.
MIKA may explore, reason, and build within those rules.
MIKA may request approval for escalations.
MIKA may never alter the Governor itself.
This separation ensures:
bounded autonomy
transparency
accountability
safety

🧪 Capabilities (Current & Planned)
Implemented:

Conversational reasoning
Emotional state tracking
Memory with importance weighting
Feedback-driven behavior adjustment
Governor-aware decision making
Local LLM inference via llama.cpp

In Progress / Planned:

Internal monologue module
Capability registry
Sandboxed execution environment

Dependencies

Requirements:
pyyaml
pytz
vaderSentiment
spacy
scikit-learn
numpy
sentence-transformers
llama-cpp-python

Download:python -m spacy download en_core_web_sm

Configure MIKA

Edit config.json to set:
user name
model path (GGUF)
runtime preferences


⚠️ Disclaimer

This project is experimental and intended for:
research
learning
architectural exploration
It is not a production-ready autonomous system.

📜 License
MIT

Tool & neural network generation
Approval workflow for new capabilities
Resource-bounded learning lifecycle

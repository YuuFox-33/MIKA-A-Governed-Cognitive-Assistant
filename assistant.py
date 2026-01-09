import asyncio
import os
import signal
import functools
from typing import Optional, Callable, Dict, Any

from .config import Config
from .utils import logger, handle_exceptions
from .emotion import EmotionState
from .commands import CommandProcessor
from .feedback import RewardSystem, InternalFeedback
from .nlp import TextUnderstandingLayer
from .memory import MemoryCore

# 🛡 Governor Engine
from .engine import GovernorEngine

# Optional torch
try:
    import torch
except ImportError:
    torch = None

# Optional llama.cpp
try:
    from llama_cpp import Llama
except Exception:
    Llama = None
    logger.warning("llama_cpp not available. Running without LLM.")


class MikaAssistant:
    """
    Mika v0.7
    Governor-aware cognitive assistant.
    """

    def __init__(
        self,
        config: Config,
        listen_fn: Optional[Callable[[], Any]] = None,
        speak_fn: Optional[Callable[[str], Any]] = None,
    ):
        self.config = config
        self.listen_fn = listen_fn or self._fallback_input
        self.speak_fn = speak_fn or self._fallback_speak

        # ---------------- Device ---------------- #
        if torch and torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"
        logger.info(f"Using device: {self.device}")

        # ---------------- Governor ---------------- #
        self.governor = GovernorEngine(
            governor_path=os.path.join(
                os.path.dirname(__file__), "governor.yaml"
            )
        )
        logger.info("Governor engine initialized.")

        # ---------------- Core Systems ---------------- #
        self.emotion_engine = EmotionState()
        self.reward_system = RewardSystem(self.config)
        self.internal_feedback = InternalFeedback(self.config, self.emotion_engine)
        self.command_processor = CommandProcessor(self.config, self.emotion_engine)
        self.nlp = TextUnderstandingLayer(self.config)

        self.memory = MemoryCore(
            memory_path="mika_memory.json",
            short_term_limit=10,
            importance_threshold=0.6,
        )

        # ---------------- Model ---------------- #
        self.model: Optional[Llama] = None
        if self.config.model_path and os.path.exists(self.config.model_path):
            self._load_model()
        else:
            logger.warning("No local model found. Using fallback responses.")

        self.shutdown_event = asyncio.Event()

    # --------------------------------------------------
    # Setup
    # --------------------------------------------------

    def register_signal_handlers(self) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(
                    sig, functools.partial(self._signal_handler, sig=sig)
                )
            except NotImplementedError:
                pass

    def _signal_handler(self, sig: signal.Signals) -> None:
        logger.info(f"Received signal {sig.name}, shutting down.")
        asyncio.create_task(self.shutdown())

    def _load_model(self) -> None:
        if not Llama:
            return

        logger.info("Loading GGUF model...")
        self.model = Llama(
            model_path=self.config.model_path,
            n_ctx=4096,
            n_threads=os.cpu_count() or 4,
            n_gpu_layers=40 if self.device == "cuda" else 0,
            verbose=False,
        )

    async def _fallback_input(self) -> str:
        return await asyncio.to_thread(input, f"{self.config.user_name}> ")

    async def _fallback_speak(self, text: str) -> None:
        print(f"{self.config.ai_name}> {text}")

    # --------------------------------------------------
    # Core Loop
    # --------------------------------------------------

    @handle_exceptions
    async def start(self) -> None:
        await self.speak(f"{self.config.ai_name} is online.")
        while not self.shutdown_event.is_set():
            user_text = await self.listen_fn()
            if not user_text:
                continue
            await self.handle_input(str(user_text).strip())

    async def handle_input(self, text: str) -> None:
        """
        Core interaction pipeline.
        """
        # ---------------- Governor: cognition allowed? ---------------- #
        if not self.governor.allows("cognition.reason"):
            await self.speak("I’m not allowed to reason right now.")
            return

        # ---------------- NLP ---------------- #
        intent, metadata = await asyncio.to_thread(self.nlp.analyze, text)
        emotion_before = self.emotion_engine.emotional_summary()

        # ---------------- Command Path ---------------- #
        if text.lower() in self.config.commands:
            if not self.governor.allows("tools.execute_code_in_sandbox"):
                response = "I’m not permitted to execute that command."
            else:
                try:
                    handler = self.command_processor.resolve_handler(
                        self.config.commands[text.lower()]
                    )
                    response = await handler(text, metadata)
                    self.reward_system.apply_reward(1, "command_success")
                except Exception:
                    response = "I couldn’t complete that command."
                    self.reward_system.apply_reward(-1, "command_failure")
        else:
            response = await asyncio.to_thread(self._llm_response, text)

        # ---------------- Internal Feedback ---------------- #
        adjusted_response, _, _ = await asyncio.to_thread(
            self.internal_feedback.evaluate_response, text, response
        )

        # ---------------- Memory ---------------- #
        importance = self._estimate_importance(
            intent, metadata.get("sentiment", {}), emotion_before
        )

        self.memory.add_interaction(
            user_input=text,
            assistant_response=adjusted_response,
            intent=intent,
            emotion=emotion_before,
            importance=importance,
        )

        await self.speak(adjusted_response)

    # --------------------------------------------------
    # Intelligence Helpers
    # --------------------------------------------------

    def _estimate_importance(
        self, intent: str, sentiment: Dict[str, Any], emotion: Dict[str, float]
    ) -> float:
        score = (
            abs(emotion.get("happiness", 0.5) - 0.5)
            + abs(emotion.get("sadness", 0.2))
            + abs(emotion.get("curiosity", 0.3))
        )

        if intent in {"gratitude", "emotion_check", "conversation"}:
            score += 0.2

        if sentiment:
            score += abs(sentiment.get("compound", 0.0)) * 0.3

        return min(score, 1.0)

    def _llm_response(self, prompt: str) -> str:
        if not self.model:
            return "I’m listening. Tell me more."

        memory_context = self.memory.get_recent_context()
        emotional_trend = self.memory.get_emotional_trend()

        system_prompt = (
            f"You are {self.config.ai_name}.\n"
            f"Recent context:\n{memory_context}\n\n"
            f"Emotional trend:\n{emotional_trend}\n\n"
            f"Respond naturally.\n"
        )

        full_prompt = f"{system_prompt}\nUser: {prompt}\n{self.config.ai_name}:"
        out = self.model(
            full_prompt,
            max_tokens=256,
            temperature=0.7,
            top_p=0.9,
            stop=["User:", f"{self.config.ai_name}:"],
        )

        text = out["choices"][0].get("text", "")
        return text.strip() if text else "I’m listening."

    # --------------------------------------------------
    # Shutdown
    # --------------------------------------------------

    async def speak(self, text: str) -> None:
        if asyncio.iscoroutinefunction(self.speak_fn):
            await self.speak_fn(text)
        else:
            await asyncio.to_thread(self.speak_fn, text)

    async def shutdown(self) -> None:
        if self.shutdown_event.is_set():
            return
        self.shutdown_event.set()
        await asyncio.to_thread(self.memory.summarize_long_term)
        await asyncio.to_thread(self.memory.save)
        logger.info("MIKA shut down cleanly.")

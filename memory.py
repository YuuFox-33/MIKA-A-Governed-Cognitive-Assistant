import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from .utils import logger


@dataclass
class MemoryItem:
    timestamp: float
    user_input: str
    assistant_response: str
    intent: str
    emotion: Dict[str, float]
    importance: float
    summary: Optional[str] = None


class MemoryCore:
    def __init__(
        self,
        memory_path: str = "mika_memory.json",
        short_term_limit: int = 10,
        importance_threshold: float = 0.6,
    ):
        self.memory_file = Path(memory_path)
        self.short_term_limit = short_term_limit
        self.importance_threshold = importance_threshold

        self.short_term: List[MemoryItem] = []
        self.long_term: List[MemoryItem] = []

        self._load()

    # ---------------- Persistence ---------------- #

    def _load(self) -> None:
        if not self.memory_file.exists():
            return
        try:
            data = json.loads(self.memory_file.read_text(encoding="utf-8"))
            self.short_term = [MemoryItem(**m) for m in data.get("short_term", [])]
            self.long_term = [MemoryItem(**m) for m in data.get("long_term", [])]
        except Exception as e:
            logger.error(f"Failed to load memory: {e}")

    def save(self) -> None:
        try:
            data = {
                "short_term": [asdict(m) for m in self.short_term],
                "long_term": [asdict(m) for m in self.long_term],
            }
            self.memory_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")

    # ---------------- Core Ops ---------------- #

    def add_interaction(
        self,
        user_input: str,
        assistant_response: str,
        intent: str,
        emotion: Dict[str, float],
        importance: float,
    ) -> None:
        item = MemoryItem(
            timestamp=time.time(),
            user_input=user_input,
            assistant_response=assistant_response,
            intent=intent,
            emotion=emotion,
            importance=importance,
        )

        self.short_term.append(item)
        if len(self.short_term) > self.short_term_limit:
            self.short_term.pop(0)

        if importance >= self.importance_threshold:
            self.long_term.append(item)

        self.save()

    # ---------------- Retrieval ---------------- #

    def get_recent_context(self) -> str:
        lines = []
        for m in self.short_term:
            lines.append(f"User: {m.user_input}")
            lines.append(f"MIKA: {m.assistant_response}")
        return "\n".join(lines)

    def get_emotional_trend(self) -> Dict[str, float]:
        if not self.short_term:
            return {}
        totals: Dict[str, float] = {}
        for m in self.short_term:
            for k, v in m.emotion.items():
                totals[k] = totals.get(k, 0.0) + v
        return {k: v / len(self.short_term) for k, v in totals.items()}

    # ---------------- Compression ---------------- #

    def summarize_long_term(self, max_items: int = 20) -> None:
        if len(self.long_term) <= max_items:
            return

        summary_text = " | ".join(
            f"{m.intent} ({round(m.importance,2)})" for m in self.long_term[-max_items:]
        )

        summary_item = MemoryItem(
            timestamp=time.time(),
            user_input="(summary)",
            assistant_response="(summary)",
            intent="memory_summary",
            emotion=self.get_emotional_trend(),
            importance=1.0,
            summary=summary_text,
        )

        self.long_term = [summary_item]
        self.save()

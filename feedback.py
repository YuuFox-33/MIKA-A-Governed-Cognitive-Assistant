import logging
from typing import Dict, Optional
from random import choice
from .utils import logger
from .emotion import EmotionState


class RewardSystem:
    def __init__(self, config):
        self.config = config
        self.score = 0

    def apply_reward(self, points: float, reason: str = "") -> None:
        self.score += points
        logger.info(f"⭐ Reward {points} ({reason}), score={self.score}")

        # Soft emotional coupling
        if points > 0:
            self.config.state.emotion_state["happiness"] = min(
                1.0, self.config.state.emotion_state.get("happiness", 0.5) + 0.05
            )
        elif points < 0:
            self.config.state.emotion_state["sadness"] = min(
                1.0, self.config.state.emotion_state.get("sadness", 0.2) + 0.05
            )


class InternalFeedback:
    def __init__(self, config, emotion_engine: EmotionState):
        self.config = config
        self.emotion_engine = emotion_engine

    def evaluate_response(self, user_text: str, response: str):
        adjusted = response
        adjustments = []

        traits = self.config.personality.get("core_traits", [])

        if "empathetic" in traits and any(
            w in user_text.lower() for w in ["sad", "stressed", "upset"]
        ):
            adjusted += " I'm here with you."
            adjustments.append("empathy_added")

        return adjusted, 0.0, adjustments

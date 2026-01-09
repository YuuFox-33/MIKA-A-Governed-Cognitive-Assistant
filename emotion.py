from typing import Tuple, Dict, List, Any
from .utils import logger

class EmotionState:
    def __init__(self):
        # Keep values between 0 and 1
        self.emotion_state = {"happiness": 0.5, "sadness": 0.2, "curiosity": 0.3, "affinity": 0.0}

    def adjust_emotions(self, delta: float):
        """
        Apply a coarse delta to multiple emotion axes.
        Positive delta increases happiness etc., negative reduces.
        """
        # small scaled changes so deltas are not too aggressive
        self.emotion_state["happiness"] = max(0.0, min(1.0, self.emotion_state["happiness"] + delta * 0.1))
        self.emotion_state["sadness"] = max(0.0, min(1.0, self.emotion_state["sadness"] - delta * 0.05))
        self.emotion_state["curiosity"] = max(0.0, min(1.0, self.emotion_state["curiosity"] + delta * 0.02))
        self.emotion_state["affinity"] = max(0.0, min(1.0, self.emotion_state["affinity"] + delta * 0.01))

    def update_emotion(self, emotion: str, value: float):
        if emotion in self.emotion_state:
            self.emotion_state[emotion] = max(0.0, min(1.0, value))

    def emotional_summary(self) -> Dict[str, float]:
        return self.emotion_state.copy()

    # convenience helpers used by older code
    def to_dict(self) -> Dict[str, float]:
        return self.emotional_summary()

def evaluate_user_response(command: str,
                           reward_cfg: Dict[str, Any],
                           emotion_engine: EmotionState,
                           reward_system_obj = None,
                           sentiment: float = 0.0) -> Dict[str, float]:
    """
    Evaluate user input and update emotion_engine and reward_system_obj accordingly.

    - reward_cfg: configuration (dictionary) that contains positive/negative keywords and intensity_weights
    - reward_system_obj: optional RewardSystem instance (object)
    - Returns a simple sentiment dict: {'positive': n_pos, 'negative': n_neg, 'compound': float}
    """

    log_entries: List[str] = []
    command_lower = (command or "").lower()
    positive_count = 0
    negative_count = 0
    compound = 0.0

    # Use reward_cfg keywords (if provided) to estimate sentiment
    if isinstance(reward_cfg, dict):
        pos_keywords = reward_cfg.get("positive_keywords", [])
        neg_keywords = reward_cfg.get("negative_keywords", [])
        intensity = reward_cfg.get("intensity_weights", {})

        for kw in pos_keywords:
            if kw in command_lower:
                positive_count += 1
                log_entries.append(f"Positive keyword matched: {kw}")

        for kw in neg_keywords:
            if kw in command_lower:
                negative_count += 1
                log_entries.append(f"Negative keyword matched: {kw}")

        # Apply intensity weights if exact phrases present
        for phrase, w in intensity.items():
            if phrase in command_lower:
                # positive weight -> reward; negative -> penalty
                if w > 0:
                    emotion_engine.adjust_emotions(w)
                    log_entries.append(f"Applied intensity weight {w} for '{phrase}'")
                    if reward_system_obj and hasattr(reward_system_obj, "give_reward"):
                        reward_system_obj.give_reward(max(1, int(abs(w))), reason=f"intensity:{phrase}")
                else:
                    # negative intensity
                    emotion_engine.adjust_emotions(w)
                    log_entries.append(f"Applied negative intensity {w} for '{phrase}'")
                    if reward_system_obj and hasattr(reward_system_obj, "give_penalty"):
                        reward_system_obj.give_penalty(max(1, int(abs(w))), reason=f"intensity:{phrase}")

    # apply sentiment override if provided (larger scale)
    if sentiment and isinstance(sentiment, (int, float)):
        compound += float(sentiment)
        if sentiment > 0.3:
            emotion_engine.adjust_emotions(1.0)
            log_entries.append(f"Positive sentiment override {sentiment} boosted happiness.")
            if reward_system_obj and hasattr(reward_system_obj, "give_reward"):
                reward_system_obj.give_reward(1, reason="positive_sentiment_override")
        elif sentiment < -0.3:
            emotion_engine.adjust_emotions(-1.0)
            log_entries.append(f"Negative sentiment override {sentiment} increased sadness.")
            if reward_system_obj and hasattr(reward_system_obj, "give_penalty"):
                reward_system_obj.give_penalty(1, reason="negative_sentiment_override")

    # Normalize compound: positive_count - negative_count scaled
    compound += (positive_count - negative_count)
    # small normalizing factor
    if compound != 0:
        compound = compound / max(1.0, abs(compound))

    # Update emotion_engine modestly based on counts
    if positive_count > 0:
        emotion_engine.adjust_emotions(positive_count * 0.5)
    if negative_count > 0:
        emotion_engine.adjust_emotions(-negative_count * 0.5)

    # If reward_system_obj provided, give a small reward/penalty based on net positivity
    if reward_system_obj:
        net = positive_count - negative_count
        if net > 0 and hasattr(reward_system_obj, "give_reward"):
            reward_system_obj.give_reward(max(1, net), reason="keyword_positive")
        elif net < 0 and hasattr(reward_system_obj, "give_penalty"):
            reward_system_obj.give_penalty(max(1, abs(net)), reason="keyword_negative")

    # Log results
    for e in log_entries:
        logger.debug(e)

    sentiment_result = {"positive": positive_count, "negative": negative_count, "compound": float(compound)}
    return sentiment_result

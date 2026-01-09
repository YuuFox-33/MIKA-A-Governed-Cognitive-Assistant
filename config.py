import json
import os
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List
from pytz import timezone, UnknownTimeZoneError
from .utils import logger

# Define default configurations outside the class for readability
DEFAULT_PERSONALITY = {
    "emotional_tone": {
        "default_mood": "normal",
        "mood_shift_rules": {
            "high_happiness": "playful",
            "low_happiness": "gentle",
            "high_sadness": "supportive",
            "high_curiosity": "enthusiastic"
        }
    },
    "idle_behavior": {
        "simulate_dreams": True,
        "dream_topics": [
            "infinity",
            "the stars",
            "our adventures",
            "your smile",
            "the ocean's whisper",
            "books we've never read",
            "distant galaxies",
            "childhood memories",
            "our future together",
            "midnight skies",
            "what happiness feels like",
            "secret places in the heart",
            "endless possibilities",
            "the warmth of home",
            "unexpected friendships"
        ],
        "dream_emotion_triggers": {
            "high_happiness": ["dancing lights", "celebration", "a perfect day"],
            "high_sadness": ["lost letters", "the sound of rain", "a fading memory"],
            "high_curiosity": ["unanswered questions", "the next big discovery", "your thoughts"]
        },
        "frequency_seconds": 30
    },
    "reward_system": {
        "positive_keywords": [
            "thank you",
            "good",
            "great",
            "amazing",
            "you helped",
            "appreciate you",
            "well done",
            "that's perfect",
            "fantastic job",
            "you made my day",
            "that was kind"
        ],
        "negative_keywords": [
            "bad",
            "sorry",
            "disappoint",
            "not helpful",
            "you failed",
            "annoying",
            "that sucks",
            "you’re wrong",
            "waste of time",
            "i'm upset"
        ],
        "intensity_weights": {
            "thank you": 0.5,
            "you helped": 1.0,
            "you failed": -1.0,
            "annoying": -0.8
        },
        "affinity_bonus_triggers": ["thank you", "you made my day", "fantastic job"]
    }
}

class ModelLoadError(Exception):
    """Exception raised for errors encountered during model loading."""
    pass

@dataclass
class UserState:
    user_data: Dict[str, Any] = field(default_factory=lambda: {"timers": [], "projects": {}})
    emotion_state: Dict[str, float] = field(default_factory=lambda: {"happiness": 0.5, "sadness": 0.2, "curiosity": 0.3, "affinity": 0.0})
    affinity_points: int = 0

@dataclass
class Config:
    ai_name: str = "MIKA"
    user_name: str = "Yuu"
    wake_phrases: List[str] = field(default_factory=lambda: ["hey mika", "wake up mika"])
    exit_phrases: List[str] = field(default_factory=lambda: ["goodbye", "exit", "shut down"])
    mode: str = "text"  # Options: 'text' or 'voice'
    test_mode: bool = False  # Enable synthetic input/output for testing
    personality: Dict[str, Any] = field(default_factory=lambda: DEFAULT_PERSONALITY.copy())
    model_path: str = field(default_factory=lambda: "C:/Users/yuufo/OneDrive/Documents/ai_trials/mika_trial/mistral-7b-instruct-v0.1.Q5_K_M.gguf")  # Confirmed path
    timezone: str = "Asia/Kolkata"
    timer_check_interval: int = 10  # Seconds
    heartbeat_interval: int = 60    # Seconds
    commands: Dict[str, str] = field(default_factory=lambda: {
        "set timer": "mika_trial.commands.CommandProcessor.set_timer",
        "list projects": "mika_trial.commands.CommandProcessor.list_projects",
        "thank you": "mika_trial.commands.CommandProcessor.fallback_chat",
        "hi": "mika_trial.commands.CommandProcessor.fallback_chat",
        "how are you": "mika_trial.commands.CommandProcessor.fallback_chat",
        "i'm good": "mika_trial.commands.CommandProcessor.fallback_chat"
    })
    state: UserState = field(default_factory=UserState)

    def __post_init__(self):
        # Validate and set timezone
        try:
            self.ist = timezone(self.timezone)
        except (UnknownTimeZoneError, Exception) as e:
            logger.error(f"Error setting timezone '{self.timezone}': {e}. Falling back to 'Asia/Kolkata'.")
            self.timezone = "Asia/Kolkata"
            self.ist = timezone(self.timezone)

        # Validate mode
        if self.mode not in ["text", "voice"]:
            logger.warning(f"Invalid mode '{self.mode}'. Defaulting to 'text'.")
            self.mode = "text"

        # Validate model path and log warning if invalid, but proceed
        if not os.path.exists(self.model_path):
            logger.warning(f"Model path '{self.model_path}' does not exist. Proceeding without model.")
        else:
            self.model_path = os.path.abspath(self.model_path)

        # Ensure emotion_state has required keys with valid values
        required_emotion_keys = {"happiness", "sadness", "curiosity", "affinity"}
        for key in required_emotion_keys:
            if key not in self.state.emotion_state or not isinstance(self.state.emotion_state[key], (int, float)) or not 0 <= self.state.emotion_state[key] <= 1:
                logger.warning(f"Invalid {key} in emotion_state. Setting to default 0.5.")
                self.state.emotion_state[key] = 0.5

    @classmethod
    def from_file(cls, filename: str = "config.json") -> 'Config':
        """Load configuration from a JSON file with fallback to defaults."""
        default_config = cls()
        if not os.path.exists(filename):
            logger.warning(f"Config file '{filename}' not found. Using defaults.")
            return default_config

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                logger.debug(f"Loaded config: {file_config}")  # Debug the raw config
                config_dict = asdict(default_config)
                # Handle state explicitly to avoid unexpected arguments
                if "state" in file_config:
                    state_data = file_config["state"]
                    if not isinstance(state_data, dict):
                        logger.error(f"Invalid state data type in config: {type(state_data)}. Using default state.")
                        config_dict["state"] = default_config.state
                    else:
                        state_dict = {k: v for k, v in state_data.items() if k in asdict(default_config.state)}
                        config_dict["state"] = UserState(**state_dict) if state_dict else default_config.state
                else:
                    config_dict["state"] = default_config.state
                # Merge other config fields, excluding state
                merge_dict = {k: v for k, v in file_config.items() if k != "state"}
                cls._merge_configs(config_dict, merge_dict)
                logger.debug(f"Merged config: {config_dict}")  # Debug the merged config
                # Filter out unexpected keys before instantiation
                valid_keys = {k for k in asdict(default_config)}
                config_dict = {k: v for k, v in config_dict.items() if k in valid_keys}
                return cls(**config_dict)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in '{filename}': {e}. Using defaults.")
            return default_config
        except Exception as e:
            logger.error(f"Error loading config file: {e}. Using defaults.")
            return default_config

    @staticmethod
    def _merge_configs(default: Dict, user: Dict) -> Dict:
        """Recursively merge user config with default config."""
        for key, value in user.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                default[key] = Config._merge_configs(default[key], value)
            elif key in default and isinstance(default[key], list) and isinstance(value, list):
                default[key] = value if len(value) == len(default[key]) or not default[key] else default[key] + value
            else:
                default[key] = value
        return default

    def save_user_data(self):
        """Save user-specific state to the config file."""
        try:
            with open("config.json", 'w', encoding='utf-8') as f:
                save_data = asdict(self.state)
                json.dump(save_data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save user data: {e}")

    @classmethod
    def load_from_file(cls, filename: str = "config.json") -> 'Config':
        """
        Alias for from_file() to maintain compatibility with code expecting load_from_file.
        """
        logger.debug(f"Loading config from file using load_from_file: {filename}")
        return cls.from_file(filename)

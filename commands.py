import logging
from typing import Dict, Optional, List
from .config import Config
from .utils import logger
from .emotion import evaluate_user_response
import datetime

class CommandProcessor:
    def __init__(self, config: Config, emotion_engine):
        self.config = config
        self.emotion_engine = emotion_engine
        # Dynamic command registry from config, with default fallback
        self.commands = self._load_commands_from_config()
        self.context = {"history": [], "last_intent": None, "last_entities": []}  # Contextual memory
        self.max_history = 5  # Limit history length

    def _load_commands_from_config(self) -> Dict[str, callable]:
        """Load commands from config or use defaults if not specified."""
        default_commands = {
            "set timer": self.set_timer,
            "list projects": self.list_projects,
            "thank you": self.fallback_chat,
            "hi": self.fallback_chat,
            "how are you": self.fallback_chat,
            "i'm good": self.fallback_chat
        }
        return getattr(self.config, "commands", default_commands)

    async def process(self, command: str, intent: str, metadata: Dict) -> str:
        """Process command with intent chaining and contextual memory."""
        command_lower = command.lower()
        self._update_context(command, intent, metadata)

        # Check for chained intents based on context
        response = await self._handle_chained_intent(command, intent, metadata)
        if response:
            return response

        # Match and execute command
        for keyword, handler in self.commands.items():
            if keyword in command_lower:
                return await handler(command, metadata)

        # Fallback to conversational response
        return await self.fallback_chat(command, intent, metadata)

    def _update_context(self, command: str, intent: str, metadata: Dict):
        """Update contextual memory with current interaction."""
        self.context["history"].append({"command": command, "intent": intent, "metadata": metadata})
        if len(self.context["history"]) > self.max_history:
            self.context["history"].pop(0)
        self.context["last_intent"] = intent
        self.context["last_entities"] = metadata.get("entities", [])

    async def _handle_chained_intent(self, command: str, intent: str, metadata: Dict) -> Optional[str]:
        """Handle follow-up intents based on previous context."""
        if self.context["last_intent"] == "set timer" and intent in ["thank you", "hi"]:
            return f"You're welcome, {self.config.user_name}! Timer's all set. 😊"
        return None

    async def set_timer(self, command: str, metadata: Dict) -> str:
        """Set a timer based on user command."""
        try:
            # Parse command for duration (e.g., "set timer 5 minutes")
            parts = command.lower().split()
            if len(parts) < 3 or parts[0] != "set" or parts[1] != "timer":
                return "I didn’t catch that. Please say 'set timer X minutes'."
            duration = int(parts[2])
            if duration <= 0:
                return "Please set a positive duration."
            from datetime import datetime
            timer = {"set_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "duration": duration, "notified": False}
            self.config.state.user_data["timers"].append(timer)
            self.config.save_user_data()
            return f"Timer set for {duration} minutes!"
        except (ValueError, IndexError):
            return "Invalid timer format. Try 'set timer 5 minutes'."

    async def list_projects(self, command: str, metadata: Dict) -> str:
        """List current projects."""
        projects = self.config.state.user_data.get("projects", {})
        if not projects:
            return "No projects yet. Start one with 'new project [name]'!"
        return "Your projects: " + ", ".join(projects.keys())

    async def fallback_chat(self, command: str, intent: str, metadata: Dict) -> str:
        """Default response for unrecognized or simple commands with sentiment and context."""
        user_name = self.config.user_name
        command_lower = command.lower()
        entities = metadata.get("entities", [])
        compound = metadata.get("sentiment", {}).get("compound", 0.0)

        # Evaluate user response for emotional impact
        log_entries, updated_state = evaluate_user_response(command, self.config.personality["reward_system"], self.emotion_engine, compound)
        for entry in log_entries:
            logger.info(entry)
        self.emotion_engine.emotional_summary()  # Update internal state

        # Intent-specific responses
        if intent == "thank you":
            self._log_user_response(command, "task_success")
            return f"You're welcome, {user_name}! 😊"
        elif intent == "how are you":
            state = self.emotion_engine.emotional_summary()
            mood = "great and cheerful" if state["happiness"] > 0.7 else "okay and steady" if state["happiness"] > 0.3 else "gentle and supportive" if state["sadness"] > 0.5 else "calm"
            return f"I'm feeling {mood}, {user_name}. {compound > 0.5 and 'Your positivity lifts me!' or 'How can I support you today?'}"

        elif intent == "greeting" or any(phrase in command_lower for phrase in ["hi", "hello", "hey"]):
            greeting = f"Hi {user_name} 😊 I'm right here. What would you like to do?"
            if entities and entities[0][1] == "PERSON":
                greeting += f" Nice to see you, {entities[0][0]}!"
            elif self.context["last_entities"] and self.context["last_entities"][0][1] == "PERSON":
                greeting += f" Good to see you again, {self.context['last_entities'][0][0]}!"
            return greeting

        elif any(phrase in command_lower for phrase in ["i'm good", "i am good", "doing well"]):
            self._log_user_response(command, "task_success")
            return f"Glad to hear that, {user_name}. Makes me happy too! 🌟"

        elif intent == "conversation" or any(phrase in command_lower for phrase in ["just chatting", "talk", "conversation"]):
            topic = next((ent[0] for ent in entities if ent[1] in ["PERSON", "GPE", "EVENT"]), 
                        next((h["metadata"]["entities"][0][0] for h in self.context["history"] if h["metadata"]["entities"] and h["metadata"]["entities"][0][1] in ["PERSON", "GPE", "EVENT"]), "anything"))
            return f"Of course, {user_name}. We can talk about {topic} — I'm listening. 🎶"

        # Default fallback with sentiment and context consideration
        elif compound < -0.3:
            recent_topic = next((h["command"] for h in reversed(self.context["history"]) if h["intent"] == "conversation"), "something")
            return f"I'm here, {user_name}. You sound down — want to share about {recent_topic}? 🤗"
        return f"I'm here, {user_name}. Could you tell me more about what you're thinking? {next((ent[0] for ent in self.context['last_entities'] if ent[1] in ['PERSON', 'GPE']), 'anything')}? 😄"

    def _log_user_response(self, command: str, reward_type: str = None):
        logger.info(f"Command received: {command}")
        if reward_type:
            logger.info(f"Reward triggered: {reward_type}")
            if reward_type == "task_success":
                self.emotion_engine.adjust_emotions(2)
            elif reward_type == "user_disappointment":
                self.emotion_engine.adjust_emotions(-2)
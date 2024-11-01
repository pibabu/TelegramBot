from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ConversationExample(BaseModel):
    user: str
    bot: str

class PersonalityConfig(BaseModel):
    personality: str
    description: str
    examples: List[ConversationExample]
    
    def format_examples(self) -> str:
        formatted = "\nExamples:\n"
        for ex in self.examples:
            formatted += f"User: {ex.user}\nAssistant: {ex.bot}\n\n"
        return formatted

class UserState(BaseModel):
    user_id: int
    current_personality: str = Field(default="business-bro")
    last_interaction: datetime = Field(default_factory=datetime.now)
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    
    def update_personality(self, new_personality: str) -> None:
        self.current_personality = new_personality
        self.last_interaction = datetime.now()
    
    def add_to_history(self, message: str, response: str) -> None:
        self.conversation_history.append({
            "message": message,
            "response": response,
            "timestamp": datetime.now().isoformat()
        })

class ChatBotState:
    def __init__(self, personalities: List[Dict]):
        self.users: Dict[int, UserState] = {}
        self.personalities: Dict[str, PersonalityConfig] = {}
        
        # Safely initialize personalities with validation
        try:
            for personality in personalities:
                if not isinstance(personality, dict):
                    print(f"Warning: Skipping invalid personality format: {personality}")
                    continue
                    
                if "personality" not in personality:
                    print(f"Warning: Personality missing 'personality' field: {personality}")
                    continue
                
                try:
                    config = PersonalityConfig(**personality)
                    self.personalities[personality["personality"]] = config
                except Exception as e:
                    print(f"Error creating PersonalityConfig for {personality.get('personality', 'unknown')}: {str(e)}")
                    continue
            
            if not self.personalities:
                raise ValueError("No valid personalities were loaded!")
                
        except Exception as e:
            print(f"Critical error initializing ChatBotState: {str(e)}")
            raise
    
    def get_user_state(self, user_id: int) -> UserState:
        """
        Get or create user state for a given user ID.
        
        Args:
            user_id: The Telegram user ID
            
        Returns:
            UserState object for the user
        """
        try:
            if not isinstance(user_id, int):
                raise ValueError(f"Invalid user_id type: {type(user_id)}")
                
            if user_id not in self.users:
                # Get the first personality as default if business-bro isn't available
                default_personality = "business-bro"
                if default_personality not in self.personalities:
                    default_personality = next(iter(self.personalities.keys()))
                    
                self.users[user_id] = UserState(
                    user_id=user_id,
                    current_personality=default_personality
                )
            return self.users[user_id]
            
        except Exception as e:
            print(f"Error in get_user_state for user {user_id}: {str(e)}")
            # Create emergency default state
            return UserState(user_id=user_id)
    
    def get_personality(self, personality_name: str) -> Optional[PersonalityConfig]:
        """
        Get personality configuration by name.
        
        Args:
            personality_name: Name of the personality to retrieve
            
        Returns:
            PersonalityConfig if found, None otherwise
        """
        try:
            if not isinstance(personality_name, str):
                print(f"Warning: Invalid personality_name type: {type(personality_name)}")
                return None
                
            return self.personalities.get(personality_name)
            
        except Exception as e:
            print(f"Error in get_personality for {personality_name}: {str(e)}")
            return None
    
    def update_user_personality(self, user_id: int, personality: str) -> bool:
        """
        Update a user's personality if the requested personality exists.
        
        Args:
            user_id: The Telegram user ID
            personality: Name of the personality to switch to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not isinstance(user_id, int):
                print(f"Warning: Invalid user_id type: {type(user_id)}")
                return False
                
            if not isinstance(personality, str):
                print(f"Warning: Invalid personality type: {type(personality)}")
                return False
                
            if personality not in self.personalities:
                return False
                
            user_state = self.get_user_state(user_id)
            user_state.update_personality(personality)
            return True
            
        except Exception as e:
            print(f"Error in update_user_personality for user {user_id}: {str(e)}")
            return False
            
    def get_available_personalities(self) -> List[str]:
        """
        Get list of available personality names.
        
        Returns:
            List of personality names
        """
        return list(self.personalities.keys())
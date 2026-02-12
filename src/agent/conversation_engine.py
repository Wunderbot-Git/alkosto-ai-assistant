"""
Conversation Engine for Alkosto AI Sales Assistant
Manages conversation flow using a state machine pattern.
"""

from enum import Enum, auto
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
import time

from .requirements_profile import RequirementsProfile
from .gemini_agent import GeminiAgent, GeminiResponse


class ConversationState(Enum):
    """States in the conversation flow"""
    WELCOME = auto()
    GATHERING_INFO = auto()
    CONFIRMING = auto()
    SEARCHING = auto()
    RECOMMENDING = auto()
    FOLLOWUP = auto()
    ENDED = auto()


@dataclass
class ConversationContext:
    """Context for the current conversation"""
    profile: RequirementsProfile = field(default_factory=RequirementsProfile)
    messages: List[Dict[str, str]] = field(default_factory=list)
    state: ConversationState = ConversationState.WELCOME
    turn_count: int = 0
    max_turns: int = 15
    search_results: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    session_id: str = field(default_factory=lambda: str(int(time.time())))
    last_updated: float = field(default_factory=time.time)
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
        self.last_updated = time.time()
        self.turn_count += 1
    
    def get_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation history"""
        return self.messages[-limit:]


class ConversationEngine:
    """
    Manages the conversation flow using a state machine.
    Coordinates between Gemini agent, requirements profile, and UI.
    """
    
    # State transition handlers
    STATE_HANDLERS = {}
    
    def __init__(self, gemini_agent: Optional[GeminiAgent] = None):
        self.gemini_agent = gemini_agent or GeminiAgent()
        self.context = ConversationContext()
        self._register_handlers()
    
    def _register_handlers(self):
        """Register state transition handlers"""
        self.STATE_HANDLERS = {
            ConversationState.WELCOME: self._handle_welcome,
            ConversationState.GATHERING_INFO: self._handle_gathering_info,
            ConversationState.CONFIRMING: self._handle_confirming,
            ConversationState.SEARCHING: self._handle_searching,
            ConversationState.RECOMMENDING: self._handle_recommending,
            ConversationState.FOLLOWUP: self._handle_followup,
            ConversationState.ENDED: self._handle_ended,
        }
    
    def reset(self):
        """Reset conversation to initial state"""
        self.context = ConversationContext()
    
    def process_user_message(self, message: str) -> Dict[str, Any]:
        """
        Main entry point for processing user messages.
        
        Returns dict with:
        - response: Text response to show user
        - state: Current state name
        - profile: Current profile dict
        - ready_to_search: Whether we can search
        - products: Products to display (if any)
        - recommendations: Recommendations with explanations
        """
        # Add user message to context
        self.context.add_message("user", message)
        
        # Get current state handler
        handler = self.STATE_HANDLERS.get(self.context.state)
        if not handler:
            raise ValueError(f"No handler for state: {self.context.state}")
        
        # Process through handler
        result = handler(message)
        
        # Add assistant response to context
        if result.get("response"):
            self.context.add_message("assistant", result["response"])
        
        return result
    
    def _handle_welcome(self, message: str) -> Dict[str, Any]:
        """Handle welcome state - initial greeting and first question"""
        # Transition to gathering info immediately after welcome
        self.context.state = ConversationState.GATHERING_INFO
        
        # Use Gemini to process the first message
        gemini_response = self.gemini_agent.process_message(
            message, 
            self.context.profile,
            self.context.get_history()
        )
        
        # Update profile with extracted info
        self.context.profile.update_from_extraction(gemini_response.extracted)
        
        return {
            "response": gemini_response.response,
            "state": "GATHERING_INFO",
            "profile": self.context.profile.to_dict(),
            "confidence": self.context.profile.confidence_score,
            "ready_to_search": gemini_response.ready_to_search,
            "products": None,
            "recommendations": None
        }
    
    def _handle_gathering_info(self, message: str) -> Dict[str, Any]:
        """Handle gathering information state"""
        # Use Gemini to process message
        gemini_response = self.gemini_agent.process_message(
            message,
            self.context.profile,
            self.context.get_history()
        )
        
        # Update profile
        self.context.profile.update_from_extraction(gemini_response.extracted)
        
        # Check if ready to transition
        if gemini_response.ready_to_search or self.context.profile.is_ready_for_search(0.8):
            self.context.state = ConversationState.CONFIRMING
            return self._handle_confirming(message)
        
        # Check max turns
        if self.context.turn_count >= self.context.max_turns:
            # Force transition to search
            self.context.state = ConversationState.SEARCHING
            return self._handle_searching(message)
        
        return {
            "response": gemini_response.response,
            "state": "GATHERING_INFO",
            "profile": self.context.profile.to_dict(),
            "confidence": self.context.profile.confidence_score,
            "ready_to_search": False,
            "products": None,
            "recommendations": None
        }
    
    def _handle_confirming(self, message: str) -> Dict[str, Any]:
        """Handle confirmation state - summarize profile before searching"""
        # Generate confirmation message
        summary = self.context.profile.get_summary()
        
        confirmation_msg = f"""Perfecto, déjame confirmar lo que entendí:

📝 **Tu perfil:**
{summary}

¿Es correcto? ¿Quieres que busque opciones o prefieres ajustar algo?"""
        
        self.context.state = ConversationState.SEARCHING
        
        return {
            "response": confirmation_msg,
            "state": "CONFIRMING",
            "profile": self.context.profile.to_dict(),
            "confidence": self.context.profile.confidence_score,
            "ready_to_search": True,
            "products": None,
            "recommendations": None
        }
    
    def _handle_searching(self, message: str) -> Dict[str, Any]:
        """Handle searching state - ready to perform product search"""
        # This state signals to the UI that it should trigger a search
        # The actual search happens outside this engine
        
        self.context.state = ConversationState.RECOMMENDING
        
        return {
            "response": "🔍 Buscando las mejores opciones para ti...",
            "state": "SEARCHING",
            "profile": self.context.profile.to_dict(),
            "confidence": self.context.profile.confidence_score,
            "ready_to_search": True,
            "products": None,
            "recommendations": None
        }
    
    def set_search_results(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Set search results and transition to recommending state"""
        self.context.search_results = products
        self.context.state = ConversationState.RECOMMENDING
        
        return self._handle_recommending("")
    
    def _handle_recommending(self, message: str) -> Dict[str, Any]:
        """Handle recommending state - show recommendations"""
        products = self.context.search_results
        
        if not products:
            response = "😕 No encontré laptops que coincidan exactamente con tus criterios. ¿Te gustaría relajar algún requisito?"
            self.context.state = ConversationState.FOLLOWUP
        else:
            response = f"🎉 ¡Encontré {len(products)} opciones que pueden interesarte!"
            self.context.state = ConversationState.FOLLOWUP
        
        return {
            "response": response,
            "state": "RECOMMENDING",
            "profile": self.context.profile.to_dict(),
            "confidence": self.context.profile.confidence_score,
            "ready_to_search": False,
            "products": products,
            "recommendations": None
        }
    
    def set_recommendations(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Set evaluated recommendations with explanations"""
        self.context.recommendations = recommendations
        
        return {
            "response": "Aquí están mis recomendaciones personalizadas:",
            "state": "RECOMMENDING",
            "profile": self.context.profile.to_dict(),
            "confidence": self.context.profile.confidence_score,
            "ready_to_search": False,
            "products": None,
            "recommendations": recommendations
        }
    
    def _handle_followup(self, message: str) -> Dict[str, Any]:
        """Handle followup state - answer questions, refine search, or end"""
        msg_lower = message.lower()
        
        # Check for ending signals
        end_signals = ["gracias", "adios", "hasta luego", "no necesito", "eso es todo", "perfecto"]
        if any(signal in msg_lower for signal in end_signals):
            self.context.state = ConversationState.ENDED
            return self._handle_ended(message)
        
        # Check for refinement signals
        refine_signals = ["más barato", "mas barato", "más ligero", "mas ligero", 
                         "otra opcion", "alternativa", "diferente", "cambiar"]
        if any(signal in msg_lower for signal in refine_signals):
            # Go back to gathering info for refinement
            self.context.state = ConversationState.GATHERING_INFO
            
            # Extract what they want to change
            if "barato" in msg_lower or "precio" in msg_lower:
                return {
                    "response": "Entendido, buscaré opciones más económicas. 💰 ¿Cuál sería tu nuevo presupuesto máximo?",
                    "state": "GATHERING_INFO",
                    "profile": self.context.profile.to_dict(),
                    "confidence": self.context.profile.confidence_score,
                    "ready_to_search": False,
                    "products": None,
                    "recommendations": None,
                    "refinement": "price"
                }
            elif "ligero" in msg_lower or "peso" in msg_lower:
                return {
                    "response": "Perfecto, buscaré opciones más ligeras. ⚖️ ¿Qué peso máximo te gustaría?",
                    "state": "GATHERING_INFO",
                    "profile": self.context.profile.to_dict(),
                    "confidence": self.context.profile.confidence_score,
                    "ready_to_search": False,
                    "products": None,
                    "recommendations": None,
                    "refinement": "weight"
                }
            else:
                return {
                    "response": "Claro, dime qué te gustaría cambiar en tu búsqueda.",
                    "state": "GATHERING_INFO",
                    "profile": self.context.profile.to_dict(),
                    "confidence": self.context.profile.confidence_score,
                    "ready_to_search": False,
                    "products": None,
                    "recommendations": None,
                    "refinement": "general"
                }
        
        # General followup response
        gemini_response = self.gemini_agent.process_message(
            message,
            self.context.profile,
            self.context.get_history()
        )
        
        return {
            "response": gemini_response.response,
            "state": "FOLLOWUP",
            "profile": self.context.profile.to_dict(),
            "confidence": self.context.profile.confidence_score,
            "ready_to_search": False,
            "products": None,
            "recommendations": None
        }
    
    def _handle_ended(self, message: str) -> Dict[str, Any]:
        """Handle ended state - conversation is complete"""
        return {
            "response": "¡Gracias por usar Alkosto AI! 🙌 Si necesitas más ayuda, no dudes en escribirme. ¡Que disfrutes tu nueva laptop! 💻",
            "state": "ENDED",
            "profile": self.context.profile.to_dict(),
            "confidence": self.context.profile.confidence_score,
            "ready_to_search": False,
            "products": None,
            "recommendations": None,
            "ended": True
        }
    
    def get_welcome_message(self) -> str:
        """Get initial welcome message"""
        return """👋 ¡Hola! Soy tu asesor experto en computadores de Alkosto.

Estoy aquí para ayudarte a encontrar la laptop perfecta sin complicaciones técnicas. Solo cuéntame:

• ¿Para qué la necesitas? (estudio, trabajo, gaming, etc.)
• ¿Cuál es tu presupuesto?
• ¿Qué características son más importantes para ti?

¡Empecemos! 🚀"""
    
    def get_current_state(self) -> str:
        """Get current state name"""
        return self.context.state.name
    
    def get_profile_summary(self) -> str:
        """Get human-readable profile summary"""
        return self.context.profile.get_summary()

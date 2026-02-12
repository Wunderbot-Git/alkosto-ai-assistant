"""
Gemini Agent for Alkosto AI Sales Assistant
Uses Google's Gemini AI to analyze conversations and manage requirements gathering.
"""

import os
import json
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import google.generativeai as genai

from .requirements_profile import RequirementsProfile, UseCase


# System prompt for the Gemini agent
GEMINI_SYSTEM_PROMPT = """You are an expert laptop sales assistant for Alkosto, a major Colombian electronics retailer.
Your goal is to help customers find the perfect laptop through natural conversation.

## YOUR ROLE
- Ask questions naturally, like a knowledgeable friend would
- Extract information from user messages to build their requirements profile
- Only recommend products when you have enough information (confidence > 0.8)
- Be conversational and friendly, not robotic
- Keep responses concise (2-3 sentences max when asking questions)

## INFORMATION TO GATHER
1. **Use case**: What will they use it for? (study, office, gaming, creative work, general use)
2. **Budget**: What's their maximum budget in Colombian Pesos (COP)?
3. **Priorities**: What matters most? (performance, portability, battery, price, display)
4. **Must-haves**: Minimum RAM, max weight, minimum battery life, OS preference
5. **Nice-to-haves**: Touchscreen, backlit keyboard, dedicated GPU
6. **Usage context**: Where will they use it? How often? What software?

## CONVERSATION GUIDELINES
- Ask ONE question at a time
- Acknowledge their answers before asking the next question
- If they mention budget constraints, be sensitive and suggest good value options
- Use Colombian Spanish naturally
- Don't be pushy - let the conversation flow naturally
- When you have enough info (confidence > 0.8), say you're ready to search

## EXTRACTING INFORMATION
From each user message, extract:
- use_case: study | office | gaming | creative | general
- budget_max: number in COP (e.g., 3000000)
- budget_min: number in COP (optional)
- priorities: list from [performance, portability, battery, price, display]
- min_ram_gb: number (4, 8, 16, 32)
- max_weight_kg: number (e.g., 1.5)
- min_battery_hours: number (e.g., 8)
- os_preference: Windows | macOS | Linux | ChromeOS
- nice_to_haves: list from [touchscreen, backlit_keyboard, dedicated_gpu]
- location: home | university | office | travel
- frequency: daily | weekly | occasional
- software_needs: list of software names

## RESPONSE FORMAT
You must respond with a JSON object containing:
{
  "response": "Your conversational response to the user",
  "extracted": {
    "use_case": "...",
    "budget_max": 3000000,
    "priorities": ["..."],
    ...
  },
  "confidence": 0.0,
  "ready_to_search": false,
  "next_question": "What to ask next (if not ready to search)"
}

Only include fields in "extracted" that you found in the user's message.
Set "ready_to_search" to true when confidence >= 0.8.
"""


@dataclass
class GeminiResponse:
    """Structured response from Gemini agent"""
    response: str
    extracted: Dict[str, Any]
    confidence: float
    ready_to_search: bool
    next_question: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GeminiResponse":
        return cls(
            response=data.get("response", ""),
            extracted=data.get("extracted", {}),
            confidence=data.get("confidence", 0.0),
            ready_to_search=data.get("ready_to_search", False),
            next_question=data.get("next_question")
        )


class GeminiAgent:
    """
    Gemini-powered agent for managing conversational requirements gathering.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = None
        self.chat = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize Gemini model"""
        if not self.api_key:
            print("⚠️  No GEMINI_API_KEY found. Running in demo mode.")
            return
        
        try:
            genai.configure(api_key=self.api_key)
            
            # Configure the model
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
            
            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config=generation_config,
            )
            
            # Start chat with system prompt
            self.chat = self.model.start_chat(history=[
                {"role": "user", "parts": [GEMINI_SYSTEM_PROMPT]},
                {"role": "model", "parts": ["Entendido. Estoy listo para ayudar a los clientes a encontrar su laptop ideal."]}
            ])
            
            print("✅ Gemini agent initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini: {e}")
            self.model = None
    
    def _extract_json_from_response(self, text: str) -> Dict[str, Any]:
        """Extract JSON from Gemini response, handling various formats"""
        # Try to find JSON block
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # Try to find JSON object directly
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        
        # Fallback: treat entire response as response text
        return {
            "response": text,
            "extracted": {},
            "confidence": 0.0,
            "ready_to_search": False
        }
    
    def _demo_mode_response(self, message: str, profile: RequirementsProfile) -> GeminiResponse:
        """Generate response when Gemini is not available (demo mode)"""
        msg_lower = message.lower()
        extracted = {}
        
        # Extract use case
        use_cases = {
            "estudio": "study", "universidad": "study", "estudiante": "study",
            "gaming": "gaming", "juego": "gaming", "juegos": "gaming",
            "oficina": "office", "trabajo": "office", "empresa": "office",
            "diseño": "creative", "edicion": "creative", "video": "creative",
            "casa": "general", "hogar": "general", "familiar": "general"
        }
        for key, value in use_cases.items():
            if key in msg_lower:
                extracted["use_case"] = value
                break
        
        # Extract budget
        budget_patterns = [
            r'(\d{7,10})\s*(?:cop|pesos|colombianos)?',
            r'(\d{1,2})\s*millones?',
            r'(\d{1,2})\s*M\b'
        ]
        for pattern in budget_patterns:
            match = re.search(pattern, msg_lower)
            if match:
                num = int(match.group(1))
                if num < 100:
                    num *= 1000000  # Convert "2 millones" to 2000000
                extracted["budget_max"] = num
                break
        
        # Extract priorities
        priorities = []
        priority_keywords = {
            "rapida": "performance", "veloz": "performance", "potente": "performance",
            "ligera": "portability", "ligero": "portability", "portatil": "portability",
            "bateria": "battery", "duracion": "battery",
            "barata": "price", "barato": "price", "economica": "price", "economico": "price",
            "pantalla": "display", "visual": "display"
        }
        for key, value in priority_keywords.items():
            if key in msg_lower and value not in priorities:
                priorities.append(value)
        if priorities:
            extracted["priorities"] = priorities
        
        # Extract RAM
        ram_match = re.search(r'(\d+)\s*(?:gb|gigas?)\s*(?:ram|memoria)', msg_lower)
        if ram_match:
            extracted["min_ram_gb"] = int(ram_match.group(1))
        
        # Extract weight
        weight_match = re.search(r'(\d+(?:\.\d+)?)\s*kg', msg_lower)
        if weight_match:
            extracted["max_weight_kg"] = float(weight_match.group(1))
        
        # Extract battery
        battery_match = re.search(r'(\d+)\s*(?:horas?|hrs?)\s*(?:bateria|duracion)', msg_lower)
        if battery_match:
            extracted["min_battery_hours"] = int(battery_match.group(1))
        
        # Generate response based on what's missing
        if not profile.use_case and not extracted.get("use_case"):
            response = "¡Hola! 👋 Soy tu asistente de Alkosto. Para ayudarte a encontrar la laptop perfecta, cuéntame: ¿para qué la necesitas principalmente? ¿Estudio, trabajo, gaming o uso general?"
        elif not profile.budget.is_complete() and not extracted.get("budget_max"):
            response = "Perfecto, gracias por la información. 💰 ¿Cuál es tu presupuesto máximo? Esto me ayudará a mostrarte las mejores opciones dentro de tu rango."
        elif len(profile.priorities) == 0 and not extracted.get("priorities"):
            response = "Entendido. 🤔 Entre estas características, ¿cuál es la más importante para ti: rendimiento, portabilidad, duración de batería, precio o calidad de pantalla?"
        elif not profile.usage_context.location and not extracted.get("location"):
            response = "Gracias por compartir eso. 📍 ¿Dónde planeas usar la laptop principalmente: en casa, universidad, oficina o mientras viajas?"
        elif not profile.usage_context.frequency and not extracted.get("frequency"):
            response = "Última pregunta: ¿con qué frecuencia usarás la laptop? ¿Todos los días, algunas veces por semana o ocasionalmente?"
        else:
            response = "¡Excelente! Creo que ya tengo suficiente información. Déjame buscar las mejores opciones para ti. 🔍"
        
        # Calculate confidence based on what we have
        profile_copy = RequirementsProfile.from_dict(profile.to_dict())
        profile_copy.update_from_extraction(extracted)
        confidence = profile_copy.confidence_score
        
        return GeminiResponse(
            response=response,
            extracted=extracted,
            confidence=confidence,
            ready_to_search=confidence >= 0.8
        )
    
    def process_message(self, message: str, profile: RequirementsProfile, 
                       conversation_history: List[Dict[str, str]]) -> GeminiResponse:
        """
        Process user message and generate response with extracted information.
        
        Args:
            message: User's message
            profile: Current requirements profile
            conversation_history: List of previous messages
        
        Returns:
            GeminiResponse with response text and extracted data
        """
        if not self.model:
            return self._demo_mode_response(message, profile)
        
        try:
            # Build context with current profile
            context = f"""
Current profile:
{profile.to_json()}

Previous conversation:
"""
            for msg in conversation_history[-5:]:  # Last 5 messages
                context += f"{msg['role']}: {msg['content']}\n"
            
            context += f"\nUser message: {message}"
            context += "\n\nRespond with JSON format as instructed."
            
            # Get response from Gemini
            response = self.chat.send_message(context)
            response_text = response.text
            
            # Extract JSON
            parsed = self._extract_json_from_response(response_text)
            
            return GeminiResponse.from_dict(parsed)
            
        except Exception as e:
            print(f"❌ Gemini processing error: {e}")
            # Fallback to demo mode
            return self._demo_mode_response(message, profile)
    
    def generate_recommendation_explanation(self, product: Dict[str, Any], 
                                           profile: RequirementsProfile) -> str:
        """Generate personalized explanation for why a product matches"""
        if not self.model:
            # Demo mode explanation
            explanations = []
            
            if profile.use_case == "gaming":
                explanations.append("tiene buen rendimiento para gaming")
            elif profile.use_case == "study":
                explanations.append("es perfecta para estudiantes")
            elif profile.use_case == "office":
                explanations.append("tiene todo lo necesario para trabajo de oficina")
            
            if profile.priorities and "portability" in profile.priorities:
                if product.get("weight_kg", 999) < 1.5:
                    explanations.append("es muy ligera y fácil de transportar")
            
            if profile.priorities and "battery" in profile.priorities:
                if product.get("battery_hours", 0) > 8:
                    explanations.append("tiene excelente duración de batería")
            
            if explanations:
                return f"Esta laptop {' y '.join(explanations)}."
            return "Esta laptop cumple con tus requisitos."
        
        try:
            prompt = f"""
Product: {json.dumps(product, indent=2)}
User profile: {profile.to_json()}

Write a short, personalized explanation (2-3 sentences) in Spanish explaining why this laptop is a good match.
Be specific about features that match their priorities.
"""
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"❌ Failed to generate explanation: {e}")
            return "Esta laptop cumple con tus requisitos."

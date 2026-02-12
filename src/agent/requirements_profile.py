"""
Requirements Profile Schema for Alkosto AI Sales Assistant
Defines the structure for capturing user requirements dynamically.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json


class UseCase(Enum):
    STUDY = "study"
    OFFICE = "office"
    GAMING = "gaming"
    CREATIVE = "creative"
    GENERAL = "general"


class Location(Enum):
    HOME = "home"
    UNIVERSITY = "university"
    OFFICE = "office"
    TRAVEL = "travel"


class Frequency(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    OCCASIONAL = "occasional"


class Priority(Enum):
    PERFORMANCE = "performance"
    PORTABILITY = "portability"
    BATTERY = "battery"
    PRICE = "price"
    DISPLAY = "display"


@dataclass
class Budget:
    min: Optional[int] = None
    max: Optional[int] = None
    currency: str = "COP"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "min": self.min,
            "max": self.max,
            "currency": self.currency
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Budget":
        return cls(
            min=data.get("min"),
            max=data.get("max"),
            currency=data.get("currency", "COP")
        )
    
    def is_complete(self) -> bool:
        """Budget is considered complete if max is set"""
        return self.max is not None and self.max > 0
    
    def __str__(self) -> str:
        if self.min and self.max:
            return f"${self.min:,} - ${self.max:,} {self.currency}"
        elif self.max:
            return f"Hasta ${self.max:,} {self.currency}"
        elif self.min:
            return f"Desde ${self.min:,} {self.currency}"
        return "No definido"


@dataclass
class MustHaves:
    min_ram_gb: Optional[int] = None
    max_weight_kg: Optional[float] = None
    min_battery_hours: Optional[float] = None
    os_preference: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "min_ram_gb": self.min_ram_gb,
            "max_weight_kg": self.max_weight_kg,
            "min_battery_hours": self.min_battery_hours,
            "os_preference": self.os_preference
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MustHaves":
        return cls(
            min_ram_gb=data.get("min_ram_gb"),
            max_weight_kg=data.get("max_weight_kg"),
            min_battery_hours=data.get("min_battery_hours"),
            os_preference=data.get("os_preference")
        )
    
    def get_filled_count(self) -> int:
        """Count how many must-haves are specified"""
        return sum([
            1 for x in [self.min_ram_gb, self.max_weight_kg, 
                       self.min_battery_hours, self.os_preference] 
            if x is not None
        ])


@dataclass
class UsageContext:
    location: Optional[str] = None
    frequency: Optional[str] = None
    software_needs: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "location": self.location,
            "frequency": self.frequency,
            "software_needs": self.software_needs
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UsageContext":
        return cls(
            location=data.get("location"),
            frequency=data.get("frequency"),
            software_needs=data.get("software_needs", [])
        )
    
    def is_complete(self) -> bool:
        return self.location is not None and self.frequency is not None


@dataclass
class RequirementsProfile:
    """
    Main profile class that captures all user requirements
    for laptop recommendations.
    """
    use_case: Optional[str] = None
    budget: Budget = field(default_factory=Budget)
    priorities: List[str] = field(default_factory=list)
    must_haves: MustHaves = field(default_factory=MustHaves)
    nice_to_haves: List[str] = field(default_factory=list)
    usage_context: UsageContext = field(default_factory=UsageContext)
    confidence_score: float = 0.0
    missing_info: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "use_case": self.use_case,
            "budget": self.budget.to_dict(),
            "priorities": self.priorities,
            "must_haves": self.must_haves.to_dict(),
            "nice_to_haves": self.nice_to_haves,
            "usage_context": self.usage_context.to_dict(),
            "confidence_score": self.confidence_score,
            "missing_info": self.missing_info
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RequirementsProfile":
        return cls(
            use_case=data.get("use_case"),
            budget=Budget.from_dict(data.get("budget", {})),
            priorities=data.get("priorities", []),
            must_haves=MustHaves.from_dict(data.get("must_haves", {})),
            nice_to_haves=data.get("nice_to_haves", []),
            usage_context=UsageContext.from_dict(data.get("usage_context", {})),
            confidence_score=data.get("confidence_score", 0.0),
            missing_info=data.get("missing_info", [])
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "RequirementsProfile":
        return cls.from_dict(json.loads(json_str))
    
    def calculate_confidence(self) -> float:
        """
        Calculate confidence score based on profile completeness.
        Returns value between 0.0 and 1.0
        """
        score = 0.0
        total_weight = 0.0
        
        # Use case (weight: 0.25)
        total_weight += 0.25
        if self.use_case:
            score += 0.25
        
        # Budget (weight: 0.25)
        total_weight += 0.25
        if self.budget.is_complete():
            score += 0.25
        
        # Priorities (weight: 0.15)
        total_weight += 0.15
        if len(self.priorities) > 0:
            score += min(0.15, len(self.priorities) * 0.05)
        
        # Must-haves (weight: 0.20)
        total_weight += 0.20
        must_have_score = self.must_haves.get_filled_count() / 4.0
        score += 0.20 * must_have_score
        
        # Usage context (weight: 0.15)
        total_weight += 0.15
        if self.usage_context.is_complete():
            score += 0.15
        elif self.usage_context.location or self.usage_context.frequency:
            score += 0.075
        
        self.confidence_score = round(score / total_weight, 2) if total_weight > 0 else 0.0
        return self.confidence_score
    
    def get_missing_critical_info(self) -> List[str]:
        """Get list of critical missing information, ordered by priority"""
        missing = []
        
        if not self.use_case:
            missing.append("use_case")
        
        if not self.budget.is_complete():
            missing.append("budget")
        
        if len(self.priorities) == 0:
            missing.append("priorities")
        
        if not self.usage_context.location:
            missing.append("usage_location")
        
        if not self.usage_context.frequency:
            missing.append("usage_frequency")
        
        self.missing_info = missing
        return missing
    
    def update_from_extraction(self, extracted: Dict[str, Any]) -> None:
        """Update profile with extracted information from user message"""
        # Use case
        if "use_case" in extracted and not self.use_case:
            self.use_case = extracted["use_case"]
        
        # Budget
        if "budget_max" in extracted:
            self.budget.max = extracted["budget_max"]
        if "budget_min" in extracted:
            self.budget.min = extracted["budget_min"]
        
        # Priorities
        if "priorities" in extracted:
            for p in extracted["priorities"]:
                if p not in self.priorities:
                    self.priorities.append(p)
        
        # Must-haves
        if "min_ram_gb" in extracted:
            self.must_haves.min_ram_gb = extracted["min_ram_gb"]
        if "max_weight_kg" in extracted:
            self.must_haves.max_weight_kg = extracted["max_weight_kg"]
        if "min_battery_hours" in extracted:
            self.must_haves.min_battery_hours = extracted["min_battery_hours"]
        if "os_preference" in extracted:
            self.must_haves.os_preference = extracted["os_preference"]
        
        # Nice-to-haves
        if "nice_to_haves" in extracted:
            for n in extracted["nice_to_haves"]:
                if n not in self.nice_to_haves:
                    self.nice_to_haves.append(n)
        
        # Usage context
        if "location" in extracted:
            self.usage_context.location = extracted["location"]
        if "frequency" in extracted:
            self.usage_context.frequency = extracted["frequency"]
        if "software_needs" in extracted:
            for s in extracted["software_needs"]:
                if s not in self.usage_context.software_needs:
                    self.usage_context.software_needs.append(s)
        
        # Recalculate confidence
        self.calculate_confidence()
        self.get_missing_critical_info()
    
    def get_summary(self) -> str:
        """Generate human-readable summary of requirements"""
        parts = []
        
        if self.use_case:
            use_case_names = {
                "study": "estudio/universidad",
                "office": "oficina/trabajo",
                "gaming": "gaming/juegos",
                "creative": "diseño/edición",
                "general": "uso general"
            }
            parts.append(f"Uso: {use_case_names.get(self.use_case, self.use_case)}")
        
        if self.budget.is_complete():
            parts.append(f"Presupuesto: {self.budget}")
        
        if self.priorities:
            priority_names = {
                "performance": "rendimiento",
                "portability": "portabilidad",
                "battery": "batería",
                "price": "precio",
                "display": "pantalla"
            }
            parts.append(f"Prioridades: {', '.join([priority_names.get(p, p) for p in self.priorities])}")
        
        if self.must_haves.min_ram_gb:
            parts.append(f"RAM mínima: {self.must_haves.min_ram_gb}GB")
        
        if self.must_haves.max_weight_kg:
            parts.append(f"Peso máximo: {self.must_haves.max_weight_kg}kg")
        
        if self.must_haves.min_battery_hours:
            parts.append(f"Batería mínima: {self.must_haves.min_battery_hours}h")
        
        return " | ".join(parts) if parts else "Perfil incompleto"
    
    def is_ready_for_search(self, threshold: float = 0.7) -> bool:
        """Check if profile has enough info to perform search"""
        return self.calculate_confidence() >= threshold

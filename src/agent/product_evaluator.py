"""
Product Evaluation Engine for Alkosto AI Sales Assistant
Scores and ranks products based on user requirements profile.
"""

from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
import re

from .requirements_profile import RequirementsProfile


@dataclass
class ProductScore:
    """Score breakdown for a product"""
    product: Dict[str, Any]
    total_score: float
    match_percentage: int
    explanation: str
    highlights: List[str]


class ProductEvaluator:
    """Evaluates products against requirements profile"""
    
    USE_CASE_REQS = {
        "gaming": {"min_ram": 16, "min_battery": 4},
        "creative": {"min_ram": 16, "min_battery": 6},
        "study": {"min_ram": 8, "min_battery": 6},
        "office": {"min_ram": 8, "min_battery": 6},
        "general": {"min_ram": 8, "min_battery": 5}
    }
    
    def __init__(self, profile: RequirementsProfile):
        self.profile = profile
        self.reqs = self.USE_CASE_REQS.get(profile.use_case or "general", self.USE_CASE_REQS["general"])
    
    def evaluate(self, products: List[Dict], top_n: int = 2) -> List[ProductScore]:
        """Score products and return top N"""
        scored = []
        for p in products:
            score = self._score_product(p)
            scored.append(score)
        scored.sort(key=lambda x: x.total_score, reverse=True)
        return scored[:top_n]
    
    def _score_product(self, p: Dict) -> ProductScore:
        """Score single product"""
        highlights = []
        scores = []
        
        # Price score
        price = p.get("price_sale", 0)
        budget = self.profile.budget.max or 5000000
        price_score = 100 if price <= budget else max(0, 100 - (price - budget) / budget * 100)
        scores.append(price_score * 0.25)
        
        # RAM score
        ram = self._extract_ram(p.get("ram", ""))
        min_ram = self.reqs["min_ram"]
        if ram >= min_ram:
            ram_score = min(100, 80 + (ram - min_ram) * 5)
            if ram >= min_ram * 2:
                highlights.append(f"Excelente RAM ({ram}GB)")
            scores.append(ram_score * 0.20)
        else:
            scores.append(ram / min_ram * 50 * 0.20)
        
        # Weight score
        weight = p.get("weight_kg", 999)
        max_w = self.profile.must_haves.max_weight_kg or 999
        if weight <= max_w:
            weight_score = 100 if weight < 1.5 else 70 if weight < 2 else 50
            if weight < 1.3:
                highlights.append("Ultraligera")
            scores.append(weight_score * 0.15)
        else:
            scores.append(0)
        
        # Battery score
        batt = p.get("battery_hours", 0)
        min_b = self.reqs["min_battery"]
        if batt >= min_b:
            batt_score = min(100, 80 + (batt - min_b) * 3)
            if batt > 10:
                highlights.append("Larga batería")
            scores.append(batt_score * 0.15)
        else:
            scores.append(batt / min_b * 60 * 0.15)
        
        # Brand score
        brand = p.get("brand", "").upper()
        brand_score = 85 if brand in ["HP", "LENOVO", "ASUS", "DELL"] else 75
        scores.append(brand_score * 0.10)
        
        total = sum(scores)
        
        # Generate explanation
        explanation = self._explain(p, highlights, price, budget)
        
        return ProductScore(
            product=p,
            total_score=total,
            match_percentage=int(total),
            explanation=explanation,
            highlights=highlights
        )
    
    def _extract_ram(self, ram_str: str) -> int:
        match = re.search(r'(\d+)', str(ram_str))
        return int(match.group(1)) if match else 0
    
    def _explain(self, p: Dict, highlights: List[str], price: int, budget: int) -> str:
        use_case = {
            "study": "para estudiantes",
            "office": "para oficina",
            "gaming": "para gaming",
            "creative": "para diseño",
            "general": "para uso diario"
        }.get(self.profile.use_case, "para ti")
        
        parts = [f"Ideal {use_case}."]
        if highlights:
            parts.append(f"Destaca: {', '.join(highlights[:2])}.")
        if price <= budget:
            parts.append(f"Precio: ${price:,} COP.")
        
        return " ".join(parts)

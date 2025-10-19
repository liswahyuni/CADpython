"""LLM-based Natural Language Parser for CAD Generation"""

import json
import logging
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass

import ollama


@dataclass
class LLMParsedData:
    furniture_type: str
    dimensions: Dict[str, float]
    features: Dict[str, Any]
    implicit_requirements: Dict[str, Any]
    normalized_description: str
    confidence: float


class LLMParser:
    """Hybrid LLM parser using Llama 3.2 for NLU + deterministic regex extraction"""
    
    def __init__(self, model_name: str = "llama3.2:1b"):
        self.model_name = model_name
        logging.info(f"LLM Parser initialized with model: {self.model_name}")
    
    def parse_description(self, description: str, rag_context: Optional[str] = None) -> Optional[LLMParsedData]:
        try:
            # Construct prompt for structured extraction
            prompt = self._construct_prompt(description, rag_context)
            
            # Call Ollama with llama3.2:1b
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a furniture specification expert. Extract structured data from descriptions in Indonesian or English. Always respond with valid JSON only, no additional text.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={'temperature': 0.1, 'top_p': 0.9}
            )
            
            llm_output = response['message']['content']
            return self._parse_llm_output(llm_output, description)
            
        except Exception as e:
            logging.error(f"LLM parsing failed: {e}")
            return None
    
    def _construct_prompt(self, description: str, rag_context: Optional[str] = None) -> str:
        
        context_section = ""
        if rag_context:
            context_section = f"\n\nFurniture Standards Context:\n{rag_context}"
        
        prompt = f"""Extract furniture specifications from the following description.

Description: "{description}"{context_section}

Extract the following information in JSON format:
{{
  "furniture_type": "chair|table|sofa|cabinet|room|house",
  "dimensions": {{
    "width": <number in meters>,
    "length": <number in meters>,
    "height": <number in meters>,
    "diameter": <number in meters or null if not circular>
  }},
  "features": {{
    "legs": <number or null>,
    "seats": <number or null>,
    "doors": <number or null>,
    "windows": <number or null>,
    "bedrooms": <number or null>,
    "has_backrest": <boolean>,
    "has_armrest": <boolean>,
    "has_garage": <boolean>,
    "seat_shape": "square|circular|null",
    "style": "modern|traditional|null",
    "room_type": "bedroom|living|dining|null"
  }},
  "implicit_requirements": {{
    "usage_context": "<e.g., dining for 6 people, children's room>",
    "inferred_dimensions": "<any dimensions inferred from context>",
    "user_intent": "<what user really wants>"
  }},
  "normalized_description": "<clear English description with all explicit dimensions>",
  "confidence": <0.0-1.0>
}}

Examples:

Input: "Kursi dengan 4 kaki, dudukan persegi 40x40 cm, tinggi 45 cm"
Output: {{
  "furniture_type": "chair",
  "dimensions": {{"width": 0.40, "length": 0.40, "height": 0.45, "diameter": null}},
  "features": {{"legs": 4, "seat_shape": "square", "seats": 1}},
  "implicit_requirements": {{"usage_context": "single dining chair", "inferred_dimensions": "none", "user_intent": "basic 4-legged chair"}},
  "normalized_description": "Chair with 4 legs, square seat 40x40 cm, height 45 cm",
  "confidence": 1.0
}}

Input: "Saya mau meja makan untuk 6 orang"
Output: {{
  "furniture_type": "table",
  "dimensions": {{"width": 1.02, "length": 1.63, "height": 0.74, "diameter": null}},
  "features": {{"legs": 4}},
  "implicit_requirements": {{"usage_context": "dining table for 6 people", "inferred_dimensions": "from furniture standards: dining table 64x40 inches (1.63x1.02m)", "user_intent": "dining table suitable for 6 people"}},
  "normalized_description": "Dining table for 6 people, approximately 163x102 cm based on furniture standards",
  "confidence": 0.8
}}

Input: "Meja makan lingkaran diameter 120 cm dengan 4 kaki, tinggi 75 cm"
Output: {{
  "furniture_type": "table",
  "dimensions": {{"width": 1.20, "length": 1.20, "height": 0.75, "diameter": 1.20}},
  "features": {{"legs": 4, "seat_shape": "circular"}},
  "implicit_requirements": {{"usage_context": "round dining table", "inferred_dimensions": "none", "user_intent": "circular dining table"}},
  "normalized_description": "Round dining table, diameter 120 cm with 4 legs, height 75 cm",
  "confidence": 1.0
}}

Now extract from the given description. Return ONLY the JSON object, no other text.
"""
        return prompt
    
    def _parse_llm_output(self, llm_output: str, original_description: str) -> LLMParsedData:
        json_str = llm_output.strip()
        if '```json' in json_str:
            json_str = json_str.split('```json')[1].split('```')[0].strip()
        elif '```' in json_str:
            json_str = json_str.split('```')[1].split('```')[0].strip()
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse LLM JSON: {e}")
            return LLMParsedData(
                furniture_type="furniture",
                dimensions={},
                features={},
                implicit_requirements={},
                normalized_description=original_description,
                confidence=0.0
            )
        
        validated_dimensions = self._validate_dimensions(data.get('dimensions', {}), original_description)
        
        return LLMParsedData(
            furniture_type=data.get('furniture_type', 'furniture'),
            dimensions=validated_dimensions,
            features=data.get('features', {}),
            implicit_requirements=data.get('implicit_requirements', {}),
            normalized_description=data.get('normalized_description', original_description),
            confidence=data.get('confidence', 0.5)
        )
    
    def _validate_dimensions(self, llm_dimensions: Dict[str, float], original_text: str) -> Dict[str, float]:
        regex_dimensions = self._extract_dimensions_regex(original_text)
        if regex_dimensions:
            return regex_dimensions
        
        validated = {}
        width = llm_dimensions.get('width', 0)
        validated['width'] = width if 0.1 <= width <= 20.0 else 1.0
        
        length = llm_dimensions.get('length', 0)
        validated['length'] = length if 0.1 <= length <= 20.0 else 1.0
        
        height = llm_dimensions.get('height', 0)
        validated['height'] = height if 0.1 <= height <= 10.0 else 0.75
        
        diameter = llm_dimensions.get('diameter')
        if diameter and 0.1 <= diameter <= 5.0:
            validated['diameter'] = diameter
            validated['width'] = diameter
            validated['length'] = diameter
        
        return validated
    
    def _extract_dimensions_regex(self, text: str) -> Optional[Dict[str, float]]:
        text_lower = text.lower()
        
        pattern1 = r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*cm.*?tinggi\s*(\d+(?:\.\d+)?)\s*cm'
        match = re.search(pattern1, text_lower)
        if match:
            return {
                'width': float(match.group(1)) / 100,
                'length': float(match.group(2)) / 100,
                'height': float(match.group(3)) / 100
            }
        
        pattern2 = r'panjang\s+(\d+(?:\.\d+)?)\s*cm.*?lebar\s+(\d+(?:\.\d+)?)\s*cm.*?tinggi\s+(\d+(?:\.\d+)?)\s*cm'
        match = re.search(pattern2, text_lower)
        if match:
            return {
                'length': float(match.group(1)) / 100,
                'width': float(match.group(2)) / 100,
                'height': float(match.group(3)) / 100
            }
        
        pattern3 = r'ukuran\s+(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*cm.*?tinggi\s+(\d+(?:\.\d+)?)\s*cm'
        match = re.search(pattern3, text_lower)
        if match:
            return {
                'width': float(match.group(1)) / 100,
                'length': float(match.group(2)) / 100,
                'height': float(match.group(3)) / 100
            }
        
        pattern4 = r'diameter\s+(\d+(?:\.\d+)?)\s*cm.*?tinggi\s+(\d+(?:\.\d+)?)\s*cm'
        match = re.search(pattern4, text_lower)
        if match:
            diameter = float(match.group(1)) / 100
            return {
                'diameter': diameter,
                'width': diameter,
                'length': diameter,
                'height': float(match.group(2)) / 100
            }
        
        pattern5 = r'(?:ruangan|rumah)?\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*meter'
        match = re.search(pattern5, text_lower)
        if match:
            height = 3.0
            if 'tinggi' in text_lower:
                height_match = re.search(r'tinggi\s+(\d+(?:\.\d+)?)\s*meter', text_lower)
                if height_match:
                    height = float(height_match.group(1))
            return {'width': float(match.group(1)), 'length': float(match.group(2)), 'height': height}
        
        return None

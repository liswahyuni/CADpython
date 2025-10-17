import re
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Dimension:
    width: float = 0
    length: float = 0
    height: float = 0


@dataclass
class Feature:
    name: str
    position: str
    size: Optional[Dimension] = None


@dataclass
class ParsedObject:
    object_type: str
    dimensions: Dimension
    features: List[Feature]
    unit: str = "cm"


class TextParser:
    def __init__(self):
        self.dimension_patterns = [
            r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*(?:x\s*(\d+(?:\.\d+)?))?\s*(cm|m|mm)',
            r'ukuran\s+(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*(meter|m|cm|mm)',
            r'tinggi\s+(\d+(?:\.\d+)?)\s*(cm|m|mm)',
            r'lebar\s+(\d+(?:\.\d+)?)\s*(cm|m|mm)',
            r'panjang\s+(\d+(?:\.\d+)?)\s*(cm|m|mm)',
            r'dudukan\s+persegi\s+(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*(cm|m|mm)'
        ]
        
        self.object_patterns = {
            'kursi': ['kursi', 'chair'],
            'meja': ['meja', 'table'],
            'ruangan': ['ruangan', 'room', 'kamar'],
            'lemari': ['lemari', 'cabinet'],
            'rak': ['rak', 'shelf']
        }
        
        self.feature_patterns = {
            'pintu': r'(\d+)?\s*pintu\s*(?:di\s+)?(?:sisi\s+)?(\w+)?',
            'jendela': r'(\d+)?\s*jendela\s*(?:di\s+)?(?:sisi\s+)?(\w+)?',
            'kaki': r'(\d+)\s*kaki',
            'laci': r'(\d+)?\s*laci',
            'rak': r'(\d+)?\s*rak'
        }

    def parse_description(self, description: str) -> ParsedObject:
        description = description.lower().strip()
        
        object_type = self._extract_object_type(description)
        dimensions = self._extract_dimensions(description)
        features = self._extract_features(description)
        
        return ParsedObject(
            object_type=object_type,
            dimensions=dimensions,
            features=features
        )

    def _extract_object_type(self, description: str) -> str:
        for obj_type, keywords in self.object_patterns.items():
            for keyword in keywords:
                if keyword in description:
                    return obj_type
        return "object"

    def _convert_to_cm(self, value: float, unit: str) -> float:
        """Convert value to centimeters based on unit"""
        unit = unit.lower().strip()
        if unit in ['m', 'meter']:
            return value * 100  # meters to cm
        elif unit in ['mm']:
            return value / 10   # millimeters to cm
        else:  # cm or no unit
            return value

    def _extract_dimensions(self, description: str) -> Dimension:
        dimension = Dimension()
        
        for pattern in self.dimension_patterns:
            matches = re.findall(pattern, description)
            for match in matches:
                if len(match) >= 2:
                    if 'x' in pattern and len(match) >= 4:
                        unit = match[3] if len(match) > 3 else 'cm'
                        dimension.width = self._convert_to_cm(float(match[0]), unit)
                        dimension.length = self._convert_to_cm(float(match[1]), unit)
                        if len(match) > 2 and match[2] and match[2].strip():
                            try:
                                dimension.height = self._convert_to_cm(float(match[2]), unit)
                            except ValueError:
                                pass
                    elif 'ukuran' in pattern:
                        unit = match[2] if len(match) > 2 else 'cm'
                        dimension.width = self._convert_to_cm(float(match[0]), unit)
                        dimension.length = self._convert_to_cm(float(match[1]), unit)
                    elif 'dudukan' in pattern:
                        unit = match[2] if len(match) > 2 else 'cm'
                        dimension.width = self._convert_to_cm(float(match[0]), unit)
                        dimension.length = self._convert_to_cm(float(match[1]), unit)
                    elif 'tinggi' in pattern:
                        unit = match[1] if len(match) > 1 else 'cm'
                        dimension.height = self._convert_to_cm(float(match[0]), unit)
                    elif 'lebar' in pattern:
                        unit = match[1] if len(match) > 1 else 'cm'
                        dimension.width = self._convert_to_cm(float(match[0]), unit)
                    elif 'panjang' in pattern:
                        unit = match[1] if len(match) > 1 else 'cm'
                        dimension.length = self._convert_to_cm(float(match[0]), unit)
        
        if dimension.width == 0 and dimension.length == 0:
            dimension.width = 50
            dimension.length = 50
        if dimension.height == 0:
            dimension.height = 45 if 'kursi' in description else 100
            
        return dimension

    def _extract_features(self, description: str) -> List[Feature]:
        features = []
        
        for feature_name, pattern in self.feature_patterns.items():
            matches = re.findall(pattern, description)
            for match in matches:
                count = 1
                position = "center"
                
                if isinstance(match, tuple):
                    if match[0]:
                        count = int(match[0])
                    if len(match) > 1 and match[1]:
                        position = match[1]
                elif isinstance(match, str) and match.isdigit():
                    count = int(match)
                
                for i in range(count):
                    features.append(Feature(
                        name=feature_name,
                        position=position if count == 1 else f"{position}_{i+1}"
                    ))
        
        return features
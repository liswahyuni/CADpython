#!/usr/bin/env python3
"""
CAD Generator Demo System

Demonstrates the complete CAD generation pipeline:
- Indonesian text input parsing
- RAG dimension extraction from PDF standards
- 2D CAD generation (DXF + SVG)
- 3D model generation (STL + OBJ)
"""

import os
import re
import traceback
from pdf_rag import PDFRAGProcessor, Dimensions
from cad_generator import CADGenerator  
from extruder_3d import Extruder3D
from llm_parser import LLMParser


class CADDemo:
    """
    Demo system integrating RAG database with CAD generation.
    
    Supports:
    - Indonesian input text
    - English furniture database
    - Automatic dimension extraction
    - Multi-format output (DXF, SVG, STL, OBJ)
    """
    
    def __init__(self):
        """Initialize all system components."""
        print("Initializing CAD System...")
        
        self.rag = PDFRAGProcessor()
        print("  RAG processor ready")
        
        self.llm_parser = LLMParser()
        print("  LLM parser ready (Llama 3.2:1b)")
        
        self.cad_generator = CADGenerator()
        print("  2D CAD generator ready")
        
        self.extruder = Extruder3D()
        print("  3D extruder ready")
        
        self.output_dir = "demo_output"
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"  Output directory: {self.output_dir}")
        
    def parse_description(self, description: str) -> dict:
        """
        Parse furniture description and extract metadata.
        
        Hybrid approach:
        1. Try LLM parser first (natural language understanding)
        2. Validate with RAG standards
        3. Fallback to deterministic regex if needed
        
        Args:
            description: Indonesian text description
            
        Returns:
            Dictionary with type, dimensions, and features
        """
        print(f"\nParsing: '{description}'")
        
        # Step 1: Try LLM parsing first
        print("  Using LLM (Llama 3.2:1b) for natural language understanding...")
        
        # Get RAG context for LLM
        rag_results = self.rag.search_documents(description, top_k=2)
        rag_context = "\n".join([r['text'][:200] for r in rag_results]) if rag_results else None
        
        llm_result = self.llm_parser.parse_description(description, rag_context)
        
        if llm_result and llm_result.confidence > 0.5:
            print(f"  LLM parsing successful (confidence: {llm_result.confidence:.2f})")
            print(f"  Type: {llm_result.furniture_type}")
            print(f"  Implicit requirements: {llm_result.implicit_requirements.get('user_intent', 'N/A')}")
            
            # Normalize furniture type to standard categories
            normalized_type = self._normalize_furniture_type(llm_result.furniture_type)
            print(f"  Normalized type: {normalized_type}")
            
            # Convert LLM result to standard format
            dimensions = None
            if llm_result.dimensions:
                dimensions = Dimensions(
                    width=llm_result.dimensions.get('width', 1.0),
                    length=llm_result.dimensions.get('length', 1.0),
                    height=llm_result.dimensions.get('height', 0.75)
                )
            
            # Merge features: Regex (explicit) takes priority over LLM (inferred)
            # Regex is deterministic and accurate for explicit text mentions
            # LLM fills in implicit/missing features only
            regex_features = self._parse_features(description)
            llm_features = llm_result.features
            
            # Start with LLM features (for implicit inference)
            features = {}
            for key, llm_val in llm_features.items():
                # Skip LLM value if it's a default/zero/None
                if llm_val not in [0, None, False, '']:
                    features[key] = llm_val
            
            # Override with regex features (explicit text always wins)
            for key, regex_val in regex_features.items():
                if regex_val not in [None, False, '']:
                    features[key] = regex_val
                    if key in llm_features and llm_features[key] != regex_val:
                        print(f"  ! Regex override: {key} = {regex_val} (LLM had {llm_features[key]})")
            
            return {
                'type': normalized_type,
                'dimensions': dimensions,
                'features': features,
                'rag_used': True,
                'llm_used': True,
                'implicit_requirements': llm_result.implicit_requirements
            }
        
        # Step 2: Fallback to original regex-based parsing
        print("  LLM confidence low, using regex-based parsing (deterministic)...")
        
        furniture_terms = self.rag._extract_furniture_terms(description)
        print(f"  Translated terms: {furniture_terms[:5]}...")
        
        rag_results = self.rag.search_documents(description, top_k=3)
        print(f"  Found {len(rag_results)} relevant standards")
        
        dimensions = self._extract_dimensions(description)
        if not dimensions and rag_results:
            for result in rag_results:
                dimensions = self.rag._extract_furniture_standards(result['text'])
                if dimensions:
                    print("  Using RAG standard dimensions")
                    break
        
        furniture_type = self._identify_type(description, furniture_terms)
        features = self._parse_features(description)
        
        return {
            'type': furniture_type,
            'dimensions': dimensions,
            'features': features,
            'rag_used': bool(rag_results),
            'llm_used': False
        }
    
    def _extract_dimensions(self, text: str) -> Dimensions:
        """Extract dimensions from text description."""
        text_lower = text.lower()
        
        # Check for circular/round furniture
        diameter_match = re.search(r'(?:lingkaran|bulat|round|circular).*?(?:diameter|dia\.?)\s*(\d+(?:\.\d+)?)\s*(?:cm|m)', text_lower)
        if diameter_match:
            diameter = float(diameter_match.group(1))
            if 'cm' in text_lower:
                diameter = diameter / 100
            
            # Extract height
            height_match = re.search(r'tinggi\s+(\d+(?:\.\d+)?)\s*(?:cm|m)', text_lower)
            height = 0.75  # default
            if height_match:
                height = float(height_match.group(1))
                if 'cm' in text_lower:
                    height = height / 100
            
            return Dimensions(diameter, diameter, height)
        
        patterns = [
            # Pattern untuk "panjang X lebar Y tinggi Z"
            r'panjang\s+(\d+(?:\.\d+)?)\s*cm.*?lebar\s+(\d+(?:\.\d+)?)\s*cm.*?tinggi\s+(\d+(?:\.\d+)?)\s*cm',
            r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*(?:x\s*(\d+(?:\.\d+)?))?\s*(?:cm|meter|m)',
            r'dudukan\s+(?:persegi\s+)?(\d+)x(\d+)\s*cm',
            r'tinggi\s+(\d+)\s*cm',
            r'ukuran\s+(\d+)x(\d+)\s*meter',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    if len(match.groups()) >= 3 and match.group(3):
                        width = float(match.group(1))
                        length = float(match.group(2)) 
                        height = float(match.group(3))
                        
                        if 'cm' in text_lower:
                            width, length, height = width/100, length/100, height/100
                            
                        return Dimensions(width, length, height)
                    elif len(match.groups()) >= 2:
                        width = float(match.group(1))
                        length = float(match.group(2))
                        
                        if 'cm' in text_lower:
                            width, length = width/100, length/100
                        
                        height_match = re.search(r'tinggi\s+(\d+(?:\.\d+)?)\s*(?:cm|m)', text_lower)
                        if height_match:
                            height = float(height_match.group(1))
                            if 'cm' in text_lower:
                                height = height/100
                        else:
                            height = 0.75 if 'chair' in text_lower or 'kursi' in text_lower else 3.0
                            
                        return Dimensions(width, length, height)
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _normalize_furniture_type(self, furniture_type: str) -> str:
        """
        Normalize furniture type to standard English categories.
        Maps Indonesian or LLM-generated types to CAD generator types.
        
        Priority: More specific types first (house > room > cabinet > sofa > table > chair)
        """
        type_lower = furniture_type.lower()
        
        # Check most specific types first to avoid false matches
        if any(word in type_lower for word in ['rumah', 'house', 'bangunan']):
            return 'house'
        elif any(word in type_lower for word in ['ruangan', 'kamar', 'room', 'bedroom']):
            return 'room'
        elif any(word in type_lower for word in ['lemari', 'wardrobe', 'cabinet']):
            return 'cabinet'
        elif any(word in type_lower for word in ['sofa', 'couch']):
            return 'sofa'
        elif any(word in type_lower for word in ['meja', 'table', 'dining']):
            return 'table'
        elif any(word in type_lower for word in ['kursi', 'chair']):
            return 'chair'
        
        return 'furniture'
    
    def _identify_type(self, text: str, terms: list) -> str:
        """Identify furniture type from text and translated terms."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['rumah', 'house', 'bangunan']):
            return 'house'
        elif any(word in text_lower for word in ['ruangan', 'kamar', 'room']):
            return 'room'
        elif any(word in text_lower for word in ['kursi', 'chair']):
            return 'chair'
        elif any(word in text_lower for word in ['meja', 'table']):
            return 'table'
        elif any(word in text_lower for word in ['sofa', 'couch']):
            return 'sofa'
        elif any(word in text_lower for word in ['lemari', 'wardrobe', 'cabinet']):
            return 'cabinet'
        
        return 'furniture'
    
    def _parse_features(self, text: str) -> dict:
        """Extract specific features from description."""
        features = {}
        text_lower = text.lower()
        
        door_match = re.search(r'(\d+)\s*pintu', text_lower)
        if door_match:
            features['doors'] = int(door_match.group(1))
            
        window_match = re.search(r'(\d+)\s*jendela', text_lower)
        if window_match:
            features['windows'] = int(window_match.group(1))
            
        leg_match = re.search(r'(\d+)\s*kaki', text_lower)
        if leg_match:
            features['legs'] = int(leg_match.group(1))
        
        # Room/bedroom detection
        kamar_match = re.search(r'(\d+)\s*kamar', text_lower)
        if kamar_match:
            features['bedrooms'] = int(kamar_match.group(1))
            
        # Seat/dudukan detection
        dudukan_match = re.search(r'(\d+)\s*dudukan', text_lower)
        if dudukan_match:
            features['seats'] = int(dudukan_match.group(1))
            
        # Shape detection
        if 'persegi' in text_lower or 'square' in text_lower:
            features['seat_shape'] = 'square'
        elif 'lingkaran' in text_lower or 'bulat' in text_lower or 'round' in text_lower or 'circular' in text_lower:
            features['seat_shape'] = 'circular'
        
        # Sofa features
        if 'sandaran' in text_lower or 'backrest' in text_lower:
            features['has_backrest'] = True
        if 'lengan' in text_lower or 'armrest' in text_lower:
            features['has_armrest'] = True
        if 'lengkung' in text_lower or 'curved' in text_lower or 'rounded' in text_lower:
            features['has_curves'] = True
            
        # House features
        if 'garasi' in text_lower or 'garage' in text_lower:
            features['has_garage'] = True
        if 'modern' in text_lower:
            features['style'] = 'modern'
            
        if 'bedroom' in text_lower or 'kamar tidur' in text_lower:
            features['room_type'] = 'bedroom'
            
        if 'rumah' in text_lower or 'house' in text_lower:
            features['building_type'] = 'house'
            
        return features
    
    def generate_cad(self, parsed_data: dict, filename: str) -> dict:
        """
        Generate all CAD output formats.
        
        Args:
            parsed_data: Parsed furniture metadata
            filename: Base filename for output
            
        Returns:
            Dictionary with paths to generated files
        """
        furniture_type = parsed_data['type']
        dimensions = parsed_data['dimensions']
        
        if not dimensions:
            print(f"\nSkipping {furniture_type}: No dimensions available")
            return {}
        
        print(f"\nGenerating CAD output for: {furniture_type}")
        print(f"  Dimensions: {dimensions.width:.2f}m x {dimensions.length:.2f}m x {dimensions.height:.2f}m")
        
        output_files = {}
        
        # 2D CAD files
        print("  Creating 2D views...")
        dxf_file = os.path.join(self.output_dir, f"{filename}.dxf")
        svg_file = os.path.join(self.output_dir, f"{filename}.svg")
        
        self.cad_generator.create_2d_views(parsed_data, dxf_file, svg_file)
        
        output_files['dxf'] = dxf_file
        output_files['svg'] = svg_file
        print(f"    DXF: {dxf_file}")
        print(f"    SVG: {svg_file}")
        
        # 3D models
        print("  Creating 3D models...")
        stl_file = os.path.join(self.output_dir, f"{filename}.stl")
        obj_file = os.path.join(self.output_dir, f"{filename}.obj")
        
        self.extruder.create_3d_model(parsed_data, stl_file, obj_file)
        
        output_files['stl'] = stl_file
        output_files['obj'] = obj_file
        print(f"    STL: {stl_file}")
        print(f"    OBJ: {obj_file}")
        
        return output_files
    
    def run_examples(self):
        """Run demonstration examples."""
        print("\n" + "="*80)
        print("CAD GENERATION DEMO - RAG + Translation")
        print("="*80)
        
        examples = [
            {
                'description': 'Kursi dengan 4 kaki, dudukan persegi 40x40 cm, tinggi 45 cm',
                'filename': 'chair_demo'
            },
            {
                'description': 'Ruangan ukuran 4x5 meter, dengan 1 pintu di sisi barat dan 1 jendela di sisi utara',
                'filename': 'room_demo'
            },
            {
                'description': 'Meja makan lingkaran diameter 120 cm dengan 4 kaki, tinggi 75 cm',
                'filename': 'round_dining_table'
            },
            {
                'description': 'Meja makan untuk 6 orang',
                'filename': 'dining_table_6_people'
            },
            {
                'description': 'Sofa 3 dudukan dengan sandaran dan lengan, panjang 200 cm lebar 90 cm tinggi 85 cm',
                'filename': 'three_seat_sofa'
            },
            {
                'description': 'Lemari pakaian 2 pintu, ukuran 120x60 cm, tinggi 200 cm',
                'filename': 'wardrobe'
            },
            {
                'description': 'Rumah modern 10x12 meter dengan garasi, 2 kamar tidur, 4 jendela, tinggi 3.5 meter',
                'filename': 'modern_house'
            }
        ]
        
        results = []
        
        for i, example in enumerate(examples, 1):
            print(f"\n{'='*80}")
            print(f"EXAMPLE {i}: {example['description']}")
            print('-'*80)
            
            try:
                parsed = self.parse_description(example['description'])
                
                print(f"  Type: {parsed['type']}")
                if parsed['dimensions']:
                    d = parsed['dimensions']
                    print(f"  Dimensions: {d.width:.2f}m x {d.length:.2f}m x {d.height:.2f}m")
                print(f"  Features: {parsed['features']}")
                print(f"  RAG Used: {parsed['rag_used']}")
                print(f"  LLM Used: {parsed.get('llm_used', False)}")
                if parsed.get('implicit_requirements'):
                    print(f"  User Intent: {parsed['implicit_requirements'].get('user_intent', 'N/A')}")
                
                files = self.generate_cad(parsed, example['filename'])
                results.append({
                    'example': example,
                    'parsed': parsed,
                    'files': files
                })
                
            except Exception as e:
                print(f"  ERROR: {str(e)}")
                traceback.print_exc()
        
        print("\n" + "="*80)
        print("DEMO COMPLETE")
        print("="*80)
        print(f"\nGenerated {len(results)} CAD file sets")
        print(f"Output directory: {os.path.abspath(self.output_dir)}")
        print("\nFeatures demonstrated:")
        print("  - Indonesian input → English database search")
        print("  - LLM natural language understanding (Llama 3.2:1b)")
        print("  - RAG dimension extraction from PDF standards")
        print("  - Deterministic regex validation")
        print("  - 2D CAD generation (DXF + SVG)")
        print("  - 3D model generation (STL + OBJ)")
        
        return results


def main():
    """Main entry point."""
    demo = CADDemo()
    demo.run_examples()


if __name__ == "__main__":
    main()

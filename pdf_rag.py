"""
PDF-based RAG processor for CAD generation
"""

import os
import re
import hashlib
import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

import PyPDF2
from sentence_transformers import SentenceTransformer
import chromadb


@dataclass
class Dimensions:
    """Object dimensions"""
    width: float
    length: float
    height: float


@dataclass
class Feature:
    """Object feature"""
    name: str
    position: str = ""
    count: int = 1
    size: float = 0.0


@dataclass
class ParsedObject:
    """Parsed CAD object"""
    object_type: str
    dimensions: Dimensions
    features: List[Feature]
    is_circular: bool = False
    diameter: float = None
    materials: List[str] = None


class PDFRAGProcessor:
    """PDF-based RAG processor for CAD generation"""
    
    def __init__(self, pdf_dir: str = "rag_documents", model_name: str = "all-MiniLM-L6-v2"):
        """Initialize PDF RAG processor"""
        self.pdf_dir = pdf_dir
        self.chroma_dir = os.path.join(pdf_dir, "chroma_db")
        self.max_tokens = 256  # Token limit for all-MiniLM-L6-v2
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_dir)
        self.collection = self.chroma_client.get_or_create_collection(
            name="pdf_chunks",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize sentence transformer model (force CPU usage)
        try:
            # Set environment variable to force CPU usage
            os.environ['CUDA_VISIBLE_DEVICES'] = ''
            
            self.encoder = SentenceTransformer(model_name)
            logging.info(f"Loaded sentence transformer on CPU: {model_name}")
        except Exception as e:
            logging.warning(f"Could not load sentence transformer: {e}. Falling back to keyword search.")
            self.encoder = None
        
        # Process all PDFs
        self._load_pdfs()
    
    def _load_pdfs(self):
        """Load and process PDF and text files"""
        if not os.path.exists(self.pdf_dir):
            os.makedirs(self.pdf_dir)
            return
        
        for filename in os.listdir(self.pdf_dir):
            file_path = os.path.join(self.pdf_dir, filename)
            if filename.lower().endswith('.pdf'):
                self._process_pdf(file_path)
            elif filename.lower().endswith(('.txt', '.md')):
                self._process_text_file(file_path)
    
    def _process_pdf(self, pdf_path: str):
        """Process individual PDF file"""
        
        # Check if already processed
        file_hash = self._get_file_hash(pdf_path)
        
        # Check if any documents exist with this file hash
        try:
            results = self.collection.get(
                where={"file_hash": file_hash},
                limit=1
            )
            if len(results['ids']) > 0:
                return
        except Exception:
            pass
        
        # Extract text from PDF
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            # Split into chunks
            chunks = self._split_text_into_chunks(text)
            
            # Store chunks with embeddings in ChromaDB
            for i, chunk in enumerate(chunks):
                chunk_id = f"{file_hash}_{i}"
                truncated_chunk = self._truncate_text(chunk)
                
                # Create embedding if encoder is available
                embedding = None
                if self.encoder:
                    embedding = self.encoder.encode([truncated_chunk])[0].tolist()
                
                # Store in ChromaDB
                self.collection.add(
                    documents=[chunk],
                    embeddings=[embedding] if embedding else None,
                    metadatas=[{
                        "file_path": pdf_path,
                        "file_hash": file_hash,
                        "chunk_index": i,
                        "filename": os.path.basename(pdf_path)
                    }],
                    ids=[chunk_id]
                )
            
        except Exception as e:
            logging.error(f"Error processing PDF {pdf_path}: {e}")
    
    def _process_text_file(self, file_path: str):
        """Process text/markdown files"""
        file_hash = self._get_file_hash(file_path)
        
        # Check if already processed
        try:
            results = self.collection.get(
                where={"file_hash": file_hash},
                limit=1
            )
            if len(results['ids']) > 0:
                return
        except Exception:
            pass
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            
            chunks = self._split_text_into_chunks(text)
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{file_hash}_{i}"
                truncated_chunk = self._truncate_text(chunk)
                
                # Create embedding if encoder is available
                embedding = None
                if self.encoder:
                    embedding = self.encoder.encode([truncated_chunk])[0].tolist()
                
                # Store in ChromaDB
                self.collection.add(
                    documents=[chunk],
                    embeddings=[embedding] if embedding else None,
                    metadatas=[{
                        "file_path": file_path,
                        "file_hash": file_hash,
                        "chunk_index": i,
                        "filename": os.path.basename(file_path)
                    }],
                    ids=[chunk_id]
                )
            
        except Exception as e:
            logging.error(f"Error processing text file {file_path}: {e}")
    
    def _get_file_hash(self, file_path: str) -> str:
        """Get file hash for caching"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def _split_text_into_chunks(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Split text into manageable chunks"""
        # Clean text
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Split into sentences first
        sentences = re.split(r'[.!?]+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _truncate_text(self, text: str) -> str:
        """Truncate text to fit within token limits"""
        if not self.encoder:
            return text
        
        # Simple word-based approximation (1 token ≈ 0.75 words for English)
        max_words = int(self.max_tokens * 0.75)
        words = text.split()
        
        if len(words) <= max_words:
            return text
        
        return ' '.join(words[:max_words])
    
    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search documents with relevance scoring"""
        
        if self.encoder:
            # Use semantic search with furniture term extraction
            furniture_terms = self._extract_furniture_terms(query)
            expanded_query = f"{query} {' '.join(furniture_terms)}"
            
            truncated_query = self._truncate_text(expanded_query)
            query_embedding = self.encoder.encode([truncated_query])[0].tolist()
            
            try:
                # Query ChromaDB with relevance scoring
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(top_k * 2, 20)  # Get more results for better filtering
                )
                
                # Filter and score results based on relevance
                search_results = []
                for i in range(len(results['documents'][0])):
                    doc = results['documents'][0][i]
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i]
                    
                    # Calculate relevance score
                    relevance_score = self._calculate_relevance(query, doc, furniture_terms)
                    final_score = (1 - distance) * 0.7 + relevance_score * 0.3
                    
                    if final_score > 0.3:  # Only include relevant results
                        search_results.append({
                            "text": doc,
                            "file": metadata.get('filename', 'unknown'),
                            "similarity": final_score,
                            "relevance": relevance_score
                        })
                
                # Sort by final score and return top results
                search_results.sort(key=lambda x: x['similarity'], reverse=True)
                return search_results[:top_k]
                
            except Exception as e:
                logging.warning(f"ChromaDB search failed: {e}. Falling back to keyword search.")
        
        # Fallback keyword search
        return self._keyword_search(query, top_k)
    
    def get_cad_context(self, description: str) -> List[str]:
        """Get relevant CAD context from PDFs"""
        # Search for relevant information
        search_results = self.search_documents(description, top_k=5)
        return [result["text"] for result in search_results]
    
    def parse_with_rag(self, description: str, context: List[str]) -> ParsedObject:
        """Parse description using RAG context"""
        # Combine description with context
        full_context = f"Context: {' '.join(context)}\n\nDescription: {description}"
        
        # Extract object type
        object_type = self._extract_object_type(full_context)
        
        # Extract dimensions
        dimensions = self._extract_dimensions(full_context)
        
        # Extract features
        features = self._extract_features(full_context)
        
        # Check if circular
        is_circular, diameter = self._extract_circular_info(full_context)
        
        # Extract materials
        materials = self._extract_materials(full_context)
        
        return ParsedObject(
            object_type=object_type,
            dimensions=dimensions,
            features=features,
            is_circular=is_circular,
            diameter=diameter,
            materials=materials
        )
    
    def _extract_object_type(self, text: str) -> str:
        """Extract object type from text"""
        text_lower = text.lower()
        
        # Prioritize original description over context
        description_part = text_lower.split("description:")[-1] if "description:" in text_lower else text_lower
        
        object_types = {
            "lingkaran": ["lingkaran", "bulat", "bundar", "circular", "round", "cylinder"],
            "sofa": ["sofa", "couch"],
            "meja": ["meja", "table", "desk"],
            "kursi": ["kursi", "chair", "seat"],
            "lemari": ["lemari", "wardrobe", "cabinet", "closet"],
            "rak": ["rak", "shelf", "bookshelf"],
            "ruangan": ["ruangan", "room", "kamar"],
            "rumah": ["rumah", "house", "building", "bangunan"]
        }
        
        # First check the description part (user input)
        for obj_type, keywords in object_types.items():
            if any(keyword in description_part for keyword in keywords):
                return obj_type
        
        # Then check full context
        for obj_type, keywords in object_types.items():
            if any(keyword in text_lower for keyword in keywords):
                return obj_type
        
        return "meja"  # Default
    
    def _extract_dimensions(self, text: str) -> Dimensions:
        """Extract dimensions from text - prioritize user description"""
        
        # First try to extract from user description part
        if "Description:" in text:
            user_description = text.split("Description:")[-1].strip()
            user_dimensions = self._extract_from_description(user_description)
            if user_dimensions:
                return user_dimensions
        
        # Then look for furniture standard dimensions in RAG context
        furniture_dimensions = self._extract_furniture_standards(text)
        if furniture_dimensions:
            return furniture_dimensions
        
        # Look for explicit dimension patterns
        dimension_patterns = [
            # Pattern: "40x40 cm tinggi 45 cm"
            r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*cm.*tinggi\s*(\d+(?:\.\d+)?)\s*cm',
            # Pattern: "WxLxH"
            r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)',
            # Pattern: "WxL meter"
            r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*meter',
            # Pattern: explicit dimensions
            r'lebar\s*(\d+(?:\.\d+)?)\s*cm.*panjang\s*(\d+(?:\.\d+)?)\s*cm.*tinggi\s*(\d+(?:\.\d+)?)\s*cm',
            # Pattern: "ruangan 4x5 meter"
            r'ruangan\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*meter',
        ]
        
        for pattern in dimension_patterns:
            match = re.search(pattern, text.lower())
            if match:
                values = [float(m) for m in match.groups()]
                if len(values) == 3:
                    return Dimensions(values[0]/100, values[1]/100, values[2]/100)  # Convert cm to m
                elif len(values) == 2:
                    return Dimensions(values[0], values[1], 0.75)  # Default height
        
        # Default dimensions based on object type
        object_type = self._extract_object_type(text)
        defaults = {
            "lingkaran": Dimensions(1.0, 1.0, 0.1),  # Circular disk
            "kursi": Dimensions(0.40, 0.40, 0.45),   # Chair with exact specs
            "meja": Dimensions(1.60, 0.90, 0.75),    # Table for 6 people
            "sofa": Dimensions(2.00, 0.80, 0.80),    # 3-seater sofa
            "lemari": Dimensions(1.20, 0.60, 2.00),  # Wardrobe
            "rak": Dimensions(0.80, 0.30, 1.80),     # Shelf
            "ruangan": Dimensions(4.0, 5.0, 2.8),    # Room 4x5m
            "rumah": Dimensions(8.0, 10.0, 6.0),     # House
        }
        
        return defaults.get(object_type, Dimensions(1.0, 1.0, 1.0))
    
    def _extract_from_description(self, description: str) -> Dimensions:
        """Extract dimensions directly from user description"""
        description = description.lower().strip()
        
        # Pattern: "40x40 cm tinggi 45 cm" 
        pattern1 = r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*cm.*tinggi\s*(\d+(?:\.\d+)?)\s*cm'
        match = re.search(pattern1, description)
        if match:
            width = float(match.group(1)) / 100  # Convert cm to m
            length = float(match.group(2)) / 100
            height = float(match.group(3)) / 100
            return Dimensions(width, length, height)
        
        # Pattern: "ruangan 4x5 meter"
        pattern2 = r'ruangan\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*meter'
        match = re.search(pattern2, description)
        if match:
            width = float(match.group(1))
            length = float(match.group(2))
            height = 2.8  # Standard room height
            return Dimensions(width, length, height)
        
        # Pattern: "WxLxH cm/m"
        pattern3 = r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*(cm|m)'
        match = re.search(pattern3, description)
        if match:
            width = float(match.group(1))
            length = float(match.group(2))
            height = float(match.group(3))
            unit = match.group(4)
            if unit == 'cm':
                width /= 100
                length /= 100 
                height /= 100
            return Dimensions(width, length, height)
        
        return None
    
    def _extract_furniture_terms(self, query: str) -> List[str]:
        """Extract furniture-related terms with Indonesian-English translation"""
        # Furniture translation dictionary
        furniture_keywords = {
            # Basic furniture - exact matching
            'kursi': ['chair', 'seat', 'sitting', 'backrest', 'armrest', 'legs', 'dining', 'side'],
            'meja': ['table', 'desk', 'surface', 'top', 'dining', 'office', 'coffee', 'kitchen', 'end'],
            'sofa': ['couch', 'seating', 'cushion', 'living', 'comfort', 'sofa', 'settee', 'easy'],
            'lemari': ['cabinet', 'wardrobe', 'storage', 'closet', 'shelves', 'chest'],
            'tempat tidur': ['bed', 'mattress', 'twin', 'queen', 'king', 'double', 'full'],
            'rak': ['shelf', 'rack', 'bookcase', 'shelving'],
            
            # Compound terms - prioritize these for better matching
            'kursi makan': ['dining chair', 'dining side', 'dining arm', 'dining', 'side', 'chair'],
            'meja makan': ['dining table', 'dining', 'table'],
            'meja kopi': ['coffee table', 'coffee', 'table'],
            'meja kerja': ['desk', 'workstation', 'office table'],
            'kursi kantor': ['office chair', 'desk chair', 'office', 'chair'],
            'sofa ruang tamu': ['sofa', 'couch', 'living room', 'seating'],
            'lemari pakaian': ['wardrobe', 'closet', 'clothing'],
            'rak buku': ['bookcase', 'bookshelf', 'shelf'],
            
            # Room types
            'ruangan': ['room', 'space', 'interior', 'floor', 'ceiling'],
            'rumah': ['house', 'building', 'architecture', 'structure'],
            'ruang tamu': ['living room', 'lounge', 'sitting room'],
            'kamar tidur': ['bedroom', 'sleeping'],
            'dapur': ['kitchen', 'cooking'],
            'kantor': ['office', 'workspace'],
            'ruang makan': ['dining room', 'dining']
        }
        
        query_lower = query.lower()
        terms = []
        
        # First pass: look for compound terms (more specific)
        compound_terms = {k: v for k, v in furniture_keywords.items() if len(k.split()) > 1}
        for furniture_type, keywords in compound_terms.items():
            if furniture_type in query_lower:
                terms.extend(keywords)
                return terms  # Return immediately for compound matches
        
        # Second pass: look for individual terms
        single_terms = {k: v for k, v in furniture_keywords.items() if len(k.split()) == 1}
        for furniture_type, keywords in single_terms.items():
            if furniture_type in query_lower:
                terms.extend(keywords)
        
        # Third pass: check if query already contains English terms
        for keywords in furniture_keywords.values():
            for keyword in keywords:
                if keyword in query_lower:
                    terms.append(keyword)
        
        return list(set(terms))
    
    def _calculate_relevance(self, query: str, document: str, furniture_terms: List[str]) -> float:
        """Calculate relevance score for a document"""
        query_words = set(query.lower().split())
        doc_words = set(document.lower().split())
        
        # Keyword overlap score
        overlap = len(query_words.intersection(doc_words))
        keyword_score = overlap / max(len(query_words), 1)
        
        # Furniture terms score
        furniture_score = 0
        if furniture_terms:
            furniture_matches = sum(1 for term in furniture_terms if term in document.lower())
            furniture_score = furniture_matches / len(furniture_terms)
        
        # Dimension/measurement score
        dimension_patterns = [r'\d+\s*(cm|meter|inch|feet)', r'\d+\s*x\s*\d+', r'dimension', r'size']
        dimension_score = 0
        for pattern in dimension_patterns:
            if re.search(pattern, document.lower()):
                dimension_score += 0.25
        
        return (keyword_score * 0.4 + furniture_score * 0.4 + min(dimension_score, 1.0) * 0.2)
    
    def _keyword_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Keyword search with scoring"""
        try:
            all_results = self.collection.get()
            if not all_results['documents']:
                return []
            
            query_words = query.lower().split()
            furniture_terms = self._extract_furniture_terms(query)
            scored_results = []
            
            for i, doc in enumerate(all_results['documents']):
                # Multi-factor scoring
                keyword_score = sum(1 for word in query_words if word in doc.lower())
                relevance_score = self._calculate_relevance(query, doc, furniture_terms)
                final_score = keyword_score + relevance_score * 2
                
                if final_score > 0:
                    scored_results.append({
                        "text": doc,
                        "file": all_results['metadatas'][i].get('filename', 'unknown'),
                        "score": final_score,
                        "relevance": relevance_score
                    })
            
            scored_results.sort(key=lambda x: x['score'], reverse=True)
            return scored_results[:top_k]
            
        except Exception as e:
            logging.error(f"Keyword search failed: {e}")
            return []
    
    def _extract_furniture_standards(self, text: str) -> Dimensions:
        """Extract standard furniture dimensions from context"""
        # Patterns for furniture dimension tables (inches converted to meters)
        patterns = {
            # Chairs - format: "Dining, Side 19 19 18 36" (width, depth, seat_height, back_height)
            'dining_chair': r'dining,?\s+side\s+(\d+)\s+(\d+)\s+(\d+)(?:\s+(\d+))?',
            'dining_arm': r'dining,?\s+arm\s+(\d+)\s+(\d+)\s+(\d+)(?:\s+(\d+))?',
            'easy_chair': r'easy\s+(\d+)\s+(\d+)\s+(\d+)(?:\s+(\d+))?',
            'kitchen_chair': r'kitchen\s+(\d+)\s+(\d+)\s+(\d+)(?:\s+(\d+))?',
            
            # Tables - format: "Dining 29 40 64" (height, width, length)
            'dining_table': r'dining\s+(\d+)\s+(\d+)\s+(\d+)',
            'coffee_table': r'coffee\s+(\d+)\s+(\d+)\s+(\d+(?:-\d+)?)',
            'end_table': r'end\s+(\d+)\s+(\d+)\s+(\d+)',
            'kitchen_table': r'kitchen\s+(\d+)\s+(\d+)\s+(\d+)',
            
            # Sofas - format: "Sofa 26 14 72" (height, depth, width)
            'sofa': r'(?:^|\s)sofa\s+(\d+)\s+(\d+)\s+(\d+)',
            
            # General furniture type matching
            'general_chair': r'chair.*?(\d+)\s+(\d+)\s+(\d+)',
            'general_table': r'table.*?(\d+)\s+(\d+)\s+(\d+)',
        }
        
        text_lower = text.lower()
        
        # Try patterns in priority order
        for furniture_type, pattern in patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                try:
                    if 'chair' in furniture_type:
                        # Chair format: width, depth, seat_height, [back_height]
                        width = float(match.group(1)) * 0.0254  # inches to meters
                        length = float(match.group(2)) * 0.0254  # depth -> length
                        height = float(match.group(3)) * 0.0254
                        if match.group(4):  # back height available
                            height = float(match.group(4)) * 0.0254
                        return Dimensions(width, length, height)
                        
                    elif 'table' in furniture_type:
                        # Table format: height, width, length
                        height = float(match.group(1)) * 0.0254
                        width = float(match.group(2)) * 0.0254
                        length_str = match.group(3)
                        # Handle ranges like "36-48"
                        if '-' in length_str:
                            length = float(length_str.split('-')[0]) * 0.0254
                        else:
                            length = float(length_str) * 0.0254
                        return Dimensions(width, length, height)
                        
                    elif 'sofa' in furniture_type:
                        # Sofa format: height, depth, width
                        height = float(match.group(1)) * 0.0254
                        length = float(match.group(2)) * 0.0254  # depth -> length
                        width = float(match.group(3)) * 0.0254
                        return Dimensions(width, length, height)
                        
                except (ValueError, AttributeError):
                    continue
        
        # Fallback: look for any dimension pattern
        dimension_pattern = r'(\d+\.?\d*)\s*(?:x|×)\s*(\d+\.?\d*)\s*(?:x|×)\s*(\d+\.?\d*)'
        match = re.search(dimension_pattern, text_lower)
        if match:
            try:
                width = float(match.group(1)) * 0.0254
                length = float(match.group(2)) * 0.0254  # depth -> length
                height = float(match.group(3)) * 0.0254
                return Dimensions(width, length, height)
            except ValueError:
                pass
        
        return None
    
    def _extract_features(self, text: str) -> List[Feature]:
        """Extract features from text"""
        features = []
        text_lower = text.lower()
        
        # Look for legs/feet
        leg_patterns = [
            r'(\d+)\s*kaki',
            r'(\d+)\s*legs?',
            r'kaki\s*(\d+)',
        ]
        
        for pattern in leg_patterns:
            match = re.search(pattern, text_lower)
            if match:
                count = int(match.group(1))
                features.append(Feature("kaki", "corner", count))
                break
        
        # Look for doors
        if any(word in text_lower for word in ["pintu", "door"]):
            position = "selatan"  # Default
            if "utara" in text_lower or "north" in text_lower:
                position = "utara"
            elif "timur" in text_lower or "east" in text_lower:
                position = "timur"
            elif "barat" in text_lower or "west" in text_lower:
                position = "barat"
            
            features.append(Feature("pintu", position))
        
        # Look for windows
        if any(word in text_lower for word in ["jendela", "window"]):
            position = "timur"  # Default
            if "utara" in text_lower or "north" in text_lower:
                position = "utara"
            elif "selatan" in text_lower or "south" in text_lower:
                position = "selatan"
            elif "barat" in text_lower or "west" in text_lower:
                position = "barat"
            
            features.append(Feature("jendela", position))
        
        return features
    
    def _extract_circular_info(self, text: str) -> Tuple[bool, float]:
        """Extract circular information - prioritize user description"""
        
        # Only look in user description part, not RAG context
        if "Description:" in text:
            description_part = text.split("Description:")[-1].strip().lower()
        else:
            description_part = text.lower()
        
        is_circular = any(word in description_part for word in ["bulat", "bundar", "circular", "round", "lingkaran", "silinder"])
        
        diameter = None
        if is_circular:
            # Look for diameter in description part only
            diameter_patterns = [
                r'diameter\s*(\d+(?:\.\d+)?)\s*cm',
                r'diameter\s*(\d+(?:\.\d+)?)\s*m',
                r'(\d+(?:\.\d+)?)\s*cm\s*diameter',
            ]
            
            for pattern in diameter_patterns:
                match = re.search(pattern, description_part)
                if match:
                    value = float(match.group(1))
                    if "cm" in match.group(0):
                        diameter = value / 100  # Convert to meters
                    else:
                        diameter = value
                    break
            
            if diameter is None:
                diameter = 1.0  # Default diameter
        
        return is_circular, diameter
    
    def _extract_materials(self, text: str) -> List[str]:
        """Extract materials from text"""
        text_lower = text.lower()
        materials = []
        
        material_keywords = {
            "kayu": ["kayu", "wood", "timber"],
            "metal": ["metal", "steel", "besi", "aluminium"],
            "plastik": ["plastik", "plastic"],
            "kaca": ["kaca", "glass"],
            "beton": ["beton", "concrete"],
            "keramik": ["keramik", "ceramic", "tile"]
        }
        
        for material, keywords in material_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                materials.append(material)
        
        return materials if materials else ["kayu"]  # Default material


def main():
    """Build RAG database from PDF documents"""
    
    pdf_folder = "./rag_documents"
    
    if not os.path.exists(pdf_folder):
        print(f"Error: {pdf_folder} folder not found")
        return
    
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
    if not pdf_files:
        print(f"No PDF files found in {pdf_folder}")
        return
    
    print(f"Found {len(pdf_files)} PDF files. Initializing RAG processor...")
    
    # Initialize processor (this will automatically process all PDFs)
    rag = PDFRAGProcessor()
    
    # Check if documents were successfully loaded
    count = rag.collection.count()
    print(f"RAG database initialized with {count} document chunks!")
    
    # Test search functionality
    print("\nTesting search functionality:")
    test_queries = ["furniture dimensions", "chair specifications", "sofa size"]
    for query in test_queries:
        results = rag.search_documents(query, top_k=2)
        print(f"Query '{query}': Found {len(results)} relevant documents")


if __name__ == "__main__":
    main()
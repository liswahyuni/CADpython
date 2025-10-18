# CAD Generator with RAG

A CAD generation system that converts Indonesian text descriptions into professional CAD files using Retrieval-Augmented Generation (RAG) from PDF furniture standards.

**Author**: Lis Wahyuni

## Overview

This system uses RAG to retrieve furniture dimensions from PDF documents. It translates Indonesian furniture terms to English, searches through a PDF knowledge base, and extracts relevant dimensions to generate CAD files.

## Features

- **Indonesian Language Support**: Natural language input in Indonesian
- **PDF-based RAG**: Retrieves furniture standards from PDF documents
- **2D CAD Output**: DXF and SVG formats with top and front views
- **3D Model Generation**: STL and OBJ/MTL formats
- **Circular Shape Support**: Circular geometry for round tables
- **2D-3D Consistency**: Matching proportions across all views
- **3D GIF Preview**: Converted STL files to rotating GIF animations for GitHub preview (since GitHub cannot directly render 3D models in README)

## Installation

### Using uv (Recommended)

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/liswahyuni/CADpython.git
cd CADpython

# Install dependencies
uv sync
```

### Using pip

```bash
# Clone repository
git clone https://github.com/liswahyuni/CADpython.git
cd CADpython

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .
```

## Quick Start

```bash
# Run demo examples
python demo.py
```

The system will generate 30 files (6 objects × 5 formats) in the `demo_output/` directory.

Output formats: DXF, SVG, STL, OBJ, MTL

## Demo Examples

### 1. Chair (Kursi 4 Kaki)

**Input Text:**
```
Kursi dengan 4 kaki, dudukan persegi 40x40 cm, tinggi 45 cm
```

**Generated Output:**
- Dimensions: 0.40m × 0.40m × 0.45m
- 2D Views: Square seat with 4 legs at corners
- 3D Model: Seat platform with 4 cylindrical legs (no backrest)
- Files: `chair_demo.{dxf,svg,stl,obj,mtl}`

**2D Output (SVG):**

![Chair 2D](demo_output/chair_demo.svg)

**3D Output:**

![Chair 3D Animation](demo_output/gifs/chair_demo.gif)

The 3D model files are available in `demo_output/`:
- `chair_demo.stl` - Binary STL for 3D printing (27 KB)
- `chair_demo.obj` - Text-based 3D model (17 KB, 819 lines)

To view 3D models:
- Use online viewers: [3D Viewer Online](https://3dviewer.net/) or [ViewSTL](https://www.viewstl.com/)
- Desktop software: Blender, MeshLab, FreeCAD
- 3D printing slicers: Cura, PrusaSlicer

### 2. Room (Ruangan dengan Pintu dan Jendela)

**Input Text:**
```
Ruangan ukuran 4x5 meter, dengan 1 pintu di sisi barat dan 1 jendela di sisi utara
```

**Generated Output:**
- Dimensions: 4.0m × 5.0m × 3.0m (height)
- 2D Views: 
  - Top: Door on west wall, window on north wall
  - Front: North wall view showing centered window
- 3D Model: Complete room with walls, door (2.0m height), and window
- Files: `room_demo.{dxf,svg,stl,obj,mtl}`

**2D Output (SVG):**

![Room 2D](demo_output/room_demo.svg)

**3D Output:**

![Room 3D Animation](demo_output/gifs/room_demo.gif)

3D model files in `demo_output/`:
- `room_demo.stl` - Complete room with walls, door (2.0m height), window (11 KB)
- `room_demo.obj` - Text format with materials (7.7 KB)

### 3. Round Dining Table (Meja Makan Bundar)

**Input Text:**
```
Meja makan lingkaran diameter 120 cm dengan 4 kaki, tinggi 75 cm
```

**Generated Output:**
- Dimensions: Ø 1.20m × 0.75m (height)
- 2D Views: Circle with 4 legs positioned at 90° intervals
- Leg Distance Label: "Leg to edge distance: 18 cm"
- 3D Model: Circular cylinder tabletop with 4 cylindrical legs
- Files: `round_dining_table.{dxf,svg,stl,obj,mtl}`

**2D Output (SVG):**

![Round Table 2D](demo_output/round_dining_table.svg)

**3D Output:**

![Round Table 3D Animation](demo_output/gifs/round_dining_table.gif)

3D model files in `demo_output/`:
- `round_dining_table.stl` - Circular cylinder tabletop with 4 legs (32 KB)
- `round_dining_table.obj` - Circular geometry (20 KB)

### 4. Three-Seat Sofa (Sofa 3 Dudukan)

**Input Text:**
```
Sofa 3 dudukan dengan sandaran dan lengan, panjang 200 cm lebar 90 cm tinggi 85 cm
```

**Generated Output:**
- Dimensions: 2.00m × 0.90m × 0.85m
- 2D Views: Top and front showing armrests (12%), backrest (20%), and 3 seats with rounded corners
- 3D Model: Base + 3 separate seat cushions (with gaps) + backrest + armrests, all with smooth rounded edges
- Files: `three_seat_sofa.{dxf,svg,stl,obj,mtl}`

**2D Output (SVG):**

![Sofa 2D](demo_output/three_seat_sofa.svg)

**3D Output:**

![Sofa 3D Animation](demo_output/gifs/three_seat_sofa.gif)

3D model files in `demo_output/`:
- `three_seat_sofa.stl` - Rounded edges, 182 vertices (17 KB)
- `three_seat_sofa.obj` - Geometry with Laplacian smoothing (11 KB)

*Note: The 3D model uses single subdivision and Laplacian smoothing (3 iterations) to match the rounded corners in 2D (rx=3, ry=3). Backrest is positioned directly on top of the seat base, matching 2D proportions.*

### 5. Wardrobe (Lemari Pakaian 2 Pintu)

**Input Text:**
```
Lemari pakaian 2 pintu, ukuran 120x60 cm, tinggi 200 cm
```

**Generated Output:**
- Dimensions: 1.20m × 0.60m × 2.00m
- 2D Views: 
  - Top: Rectangular outline with 4 legs at corners
  - Front: 2 doors with gold handles pointing toward center
- 3D Model: Cabinet structure with walls, 2 doors, handles, and support legs
- Files: `wardrobe.{dxf,svg,stl,obj,mtl}`

**2D Output (SVG):**

![Wardrobe 2D](demo_output/wardrobe.svg)

**3D Output:**

![Wardrobe 3D Animation](demo_output/gifs/wardrobe.gif)

3D model files in `demo_output/`:
- `wardrobe.stl` - Cabinet with doors, handles, and legs (12 KB)
- `wardrobe.obj` - Detailed door and handle structures (8.5 KB)

### 6. Modern House (Rumah Modern dengan Garasi)

**Input Text:**
```
Rumah modern 10x12 meter dengan garasi, 2 kamar tidur, tinggi 3.5 meter
```

**Generated Output:**
- Dimensions: 10.0m × 12.0m × 3.5m
- 2D Views: 
  - Top: Main house (75%) + garage (25%), 2 bedrooms + living area, 4 windows on side walls
  - Front: South wall with centered entrance door, garage on right side, flat modern roof
- 3D Model: Complete house structure with garage, flat roof, and main entrance
- Files: `modern_house.{dxf,svg,stl,obj,mtl}`

**2D Output (SVG):**

![Modern House 2D](demo_output/modern_house.svg)

**3D Output:**

![Modern House 3D Animation](demo_output/gifs/modern_house.gif)

3D model files in `demo_output/`:
- `modern_house.stl` - Complete house with garage and flat roof (11 KB)
- `modern_house.obj` - Full architectural structure (7.7 KB)

## Output Structure

```
demo_output/
├── chair_demo.dxf
├── chair_demo.svg
├── chair_demo.stl
├── chair_demo.obj
├── chair_demo.mtl
├── room_demo.{dxf,svg,stl,obj,mtl}
├── round_dining_table.{dxf,svg,stl,obj,mtl}
├── three_seat_sofa.{dxf,svg,stl,obj,mtl}
├── wardrobe.{dxf,svg,stl,obj,mtl}
└── modern_house.{dxf,svg,stl,obj,mtl}
```

## Viewing 3D Models

Since GitHub cannot directly render 3D models in README, I've converted all STL files to rotating GIF animations for easy preview. The original STL and OBJ files are available in the `demo_output/` directory.

To generate GIF animations:
```bash
python generate_3d_gifs.py
```

## System Architecture

### Components

```
CADpython/
├── demo.py              # Main demo runner and pipeline orchestrator
├── pdf_rag.py          # RAG processor with PDF knowledge base
├── cad_generator.py     # 2D CAD generation (DXF and SVG)
├── extruder_3d.py       # 3D model generation (STL and OBJ)
├── generate_3d_gifs.py  # 3D to GIF animation converter
├── pyproject.toml       # Project configuration and dependencies
├── demo_output/         # Generated CAD files
│   ├── *.{dxf,svg}     # 2D CAD files
│   ├── *.{stl,obj,mtl} # 3D model files
│   └── gifs/           # 3D GIF animations
└── rag_documents/       # PDF furniture standards database
```

### Component Responsibilities

| Component | Purpose |
|-----------|---------|
| `demo.py` | Orchestrates the entire pipeline, runs demonstration examples |
| `pdf_rag.py` | RAG system with text parsing, Indonesian-English translation, and dimension extraction |
| `cad_generator.py` | Creates 2D views (top and front) in DXF and SVG formats |
| `extruder_3d.py` | Generates 3D meshes in STL and OBJ/MTL formats |
| `generate_3d_gifs.py` | Converts STL files to rotating GIF animations for preview |

## Supported Object Types

| Type | Indonesian Term | Detected Features | 2D Support | 3D Support |
|------|----------------|-------------------|------------|------------|
| Chair | Kursi | Legs, seat shape | Yes | Yes |
| Table | Meja | Legs, circular/rectangular | Yes | Yes |
| Sofa | Sofa | Seats, armrests, backrest | Yes | Yes |
| Cabinet | Lemari | Doors, handles | Yes | Yes |
| Room | Ruangan | Doors, windows | Yes | Yes |
| House | Rumah | Garage, bedrooms, roof style | Yes | Yes |

## Key Features

### RAG (Retrieval-Augmented Generation)

The system uses PDF documents as the knowledge base:
- PDF files contain furniture dimension standards and architectural references
- **Translation**: Indonesian furniture terms (e.g., "kursi", "meja") are automatically translated to English
- **Retrieval**: Translated terms are used to search through PDF knowledge base using semantic similarity
- **Enhancement**: Retrieved standards are used to validate and enhance user-provided dimensions
- **Example**: When you input "meja makan", the system translates to "dining table", retrieves standard dimensions (75cm height, 150-180cm length), and uses these to validate your specifications

**How RAG Helps:**
1. **Input**: "Kursi dengan 4 kaki" (chair with 4 legs)
2. **Translation**: "kursi" → "chair"
3. **PDF Search**: Finds furniture standards with "chair" dimensions
4. **Enhancement**: Validates that 45cm seat height is standard (retrieved from PDF)
5. **Output**: Generates CAD with validated dimensions

**Location**: PDF knowledge base should be placed in the project directory. The system will automatically load and index them for RAG retrieval.

### AI/ML Technology Stack

**Sentence Transformer: `all-MiniLM-L6-v2`**
- **Purpose**: Semantic embedding for PDF document retrieval in RAG pipeline
- **Specs**: 384-dimensional embeddings, 256 token limit, CPU inference
- **Implementation**: Cosine similarity scoring for relevant chunk retrieval

**Parsing Architecture: Rule-Based (No LLM)**
- **Dimension extraction**: Regex pattern matching for Indonesian/English measurements
- **Feature detection**: Keyword-based parsing (`has_garage`, `doors`, `seats`, etc.)
- **Why no LLM**: CAD requires deterministic precision and reproducible outputs
- **Trade-off**: Limited to predefined patterns — cannot handle free-form natural language variations

**When LLM Would Help:**
- Handling ambiguous or conversational input: *"Saya mau meja yang agak besar"*
- Understanding context: *"Kursi untuk ruang makan keluarga 6 orang"*
- Extracting implicit requirements: *"Lemari untuk kamar anak kecil"*

**Current Limitation:** Input must follow structured patterns like `"panjang X cm lebar Y cm tinggi Z cm"` or `"diameter X cm"`

### 2D-3D Consistency

All models maintain strict consistency between 2D views and 3D models:
- **Round Table**: Rendered as circle in 2D SVG and cylinder in 3D mesh
- **Sofa**: Proportions (12% armrest, 20% backrest) consistent across all views
- **Room**: Door and window positions match between top view and front view
- **House**: Garage and window placements are consistent across perspectives

### Circular Shape Support

Circular furniture is detected and rendered:
```python
# Detection keywords: lingkaran, bulat, round, circular
# 2D Rendering: <circle> element in SVG
# 3D Rendering: Cylinder primitive in mesh
# Leg Positioning: Calculated at radius × 0.7 from center
```

## Technical Specifications

### Dimension Parsing

The system supports multiple dimension input formats:

```python
"40x40 cm"                          # Simple dimensions
"panjang 200 cm lebar 90 cm"        # Named dimensions (length, width)
"diameter 120 cm"                   # Circular diameter
"ukuran 4x5 meter tinggi 3 meter"   # Room-scale with height
```

### Feature Detection

Automatically extracts features from text:

```python
"4 kaki"         → legs: 4
"3 dudukan"      → seats: 3
"lingkaran"      → seat_shape: 'circular'
"2 pintu"        → doors: 2
"modern"         → style: 'modern'
"dengan garasi"  → has_garage: True
"dengan lengan"  → has_armrest: True
```

### 2D Rendering Specifications

**SVG Scale Factors:**
- Furniture: 100
- Rooms: 20
- Houses: 10

**Color Scheme:**
- Chairs/Sofas: Blue
- Tables: Green (with red legs for circular tables)
- Rooms: Yellow
- Houses: Coral
- Cabinets: Burlywood
- Handles: Gold

**Features:**
- Automatic dimension annotations
- Labeled components (doors, windows, rooms)
- Proportional representations
- Rounded corners for furniture (sofas, cushions) with rx=3, ry=3

### 3D Rendering Specifications

**Output Formats:**
- STL: Binary format for 3D printing
- OBJ: Text-based 3D model format
- MTL: Material definition file for OBJ

**Quality:**
- Surfaces with normals
- Subdivision and smoothing for rounded edges
- Circular tables with cylinder primitives
- Individual sofa cushions with gaps
- Architectural dimensions for rooms

## Programmatic Usage

```python
from demo import CADDemo

demo = CADDemo()
parsed = demo.parse_description("Meja kerja 150x80 cm dengan 4 laci, tinggi 75 cm")
files = demo.generate_cad(parsed, "custom_desk")

# Access generated files
print(files['dxf'])  # DXF file path
print(files['svg'])  # SVG file path
print(files['stl'])  # STL file path
print(files['obj'])  # OBJ file path
```

## Key Technical Details

### Circular Table Leg Positioning
- Legs placed at 70% of radius from center
- Red circles in 2D view
- Distance to edge calculated and labeled

### Multi-Seat Sofa Design
- Individual cushions with 2cm gaps
- Rounded corners (rx=3) in 2D and 3D
- Proportions: 12% armrests, 20% backrest depth
- Subdivision and Laplacian smoothing (3 iterations)

### Architectural Standards
- Room height: 3.0m
- Door height: 2.0m
- Wall representation above doors

## References

- [ezdxf Documentation](https://ezdxf.readthedocs.io/) - DXF file generation
- [svgwrite Documentation](https://svgwrite.readthedocs.io/) - SVG file generation
- [trimesh Documentation](https://trimsh.org/) - 3D mesh processing
- [Sentence Transformers](https://www.sbert.net/) - Text embedding for RAG

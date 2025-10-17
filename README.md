# Text to CAD Converter

A Python program that converts simple text descriptions into 2D CAD files (DXF, SVG) and 3D models (STL, OBJ).

## Key Features

- **Natural Text Input**: Simple descriptions in Indonesian/English
- **2D Output**: DXF (AutoCAD) and SVG files with top and front views
- **Readable SVG**: Optimized colors (blue lines, cyan dimensions, white text)
- **3D Output**: STL and OBJ models with realistic extrusion
- **Realistic Rooms**: Doors and windows with actual openings in 3D models
- **Auto Conversion**: Automatic meter to centimeter conversion
- **Multi-Object Support**: Chairs, tables, rooms, cabinets, shelves

## Quick Start

### 1. Install uv (Package Manager)

```bash
# Linux/Mac
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Install Dependencies

```bash
cd ggs_python
uv pip install -r requirements.txt
```

### 3. Run Examples

```bash
uv run python examples.py
```

Output will be saved in `examples_output/` folder with 3 sample objects × 4 formats (12 files total).

## Usage

### Command Line

```bash
# Basic usage (2D only)
uv run python main.py "Kursi makan dengan 4 kaki, dudukan 45x45 cm, tinggi 95 cm"

# Generate with 3D models
uv run python main.py "Meja kerja 140x70 cm, tinggi 75 cm" --3d

# Room with door and window
uv run python main.py "Ruangan 4x5 meter dengan pintu di barat dan jendela di utara" --3d -o my_room -n bedroom

# Custom output
uv run python main.py "Lemari 100x50x200 cm" -o furniture -n wardrobe --3d
```

### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--output` | `-o` | Output directory | `output` |
| `--name` | `-n` | File prefix | `design` |
| `--3d` | - | Generate 3D models | `False` |

### Python API

```python
from main import TextToCAD

converter = TextToCAD()
converter.process_description(
    "Kursi dengan 4 kaki, dudukan 40x40 cm, tinggi 45 cm",
    output_dir="output",
    generate_3d=True,
    filename_prefix="office_chair"
)
```

## Input Format

### Supported Objects

| Object | Keywords | Example |
|-------|----------|--------|
| Chair | `kursi`, `chair` | "Kursi makan dengan 4 kaki" |
| Table | `meja`, `table` | "Meja kerja 140x70 cm" |
| Room | `ruangan`, `room`, `kamar` | "Ruangan 4x5 meter" |
| Cabinet | `lemari`, `cabinet` | "Lemari 100x50x200 cm" |
| Shelf | `rak`, `shelf` | "Rak buku 80x30x180 cm" |

### Dimension Formats

```
✓ "40x40 cm"
✓ "4x5 meter"  
✓ "120x80x75 cm"
✓ "ukuran 4x5 meter, tinggi 3 meter"
✓ "lebar 80 cm, panjang 120 cm, tinggi 75 cm"
```

### Object Features

| Feature | Format | Example |
|-------|--------|--------|
| Legs | `{number} kaki` | "4 kaki", "6 kaki" |
| Door | `pintu di {position}` | "1 pintu di sisi barat" |
| Window | `jendela di {position}` | "2 jendela di utara" |
| Drawer | `{number} laci` | "3 laci" |

### Positions (For Doors/Windows)

```
Indonesian: utara, selatan, timur, barat
English: north, south, east, west
```

## Output Examples

### 1. Dining Chair
```bash
uv run python examples.py
```

**Input**: `"Kursi makan dengan 4 kaki, dudukan 42x42 cm, tinggi 90 cm"`

**Output Files**:
- `kursi_makan.dxf` - AutoCAD file
- `kursi_makan.svg` - SVG with readable colors
- `kursi_makan.stl` - 3D model for printing
- `kursi_makan.obj` - 3D model for rendering

**Features**:
- Top view: 42×42cm seat with 4 legs at corners
- Front view: Chair profile with backrest
- 3D model: Complete chair with seat, backrest, 4 cylindrical legs

### 2. Work Desk
**Input**: `"Meja kerja ukuran 140x70 cm, tinggi 75 cm"`

**Features**:
- Top view: 140×70cm table top with 4 legs
- 3D model: Table with top and 4 cylindrical legs

### 3. Room with Openings
**Input**: `"Ruangan 4x5 meter, tinggi 3 meter, dengan 1 pintu di barat dan 1 jendela di utara"`

**Features**:
- Top view: Room layout with door & window symbols
- 3D model: **4 walls with REAL OPENINGS**
  - Door: 90cm width, 85% room height
  - Window: 120cm width, 40% room height
  - Segmented walls to create realistic gaps

## Project Structure

```
ggs_python/
├── main.py              # CLI entry point
├── text_parser.py       # Parse text description → structured data
├── cad_generator.py     # Generate DXF/SVG (2D)
├── extruder_3d.py       # Generate STL/OBJ (3D)
├── examples.py          # 3 demonstration examples
├── README.md            # Documentation
├── requirements.txt     # Dependencies
├── .venv/               # Virtual environment (auto-created)
├── examples_output/     # Output from examples.py
└── output/              # Default output from main.py
```

## SVG Color Scheme

| Element | Color | Hex Code | Description |
|---------|-------|----------|------------|
| Object Lines | Blue | `#4A90E2` | Main design lines |
| Title Text | White | `white` | "TOP VIEW", "FRONT VIEW" |
| Dimensions | Cyan | `#00D9FF` | Dimension lines & text |

## Dependencies

```txt
ezdxf      # DXF file generation
svgwrite   # SVG file generation
trimesh    # 3D mesh processing
numpy-stl  # STL file generation
```

Install all with:
```bash
uv pip install -r requirements.txt
```

## Troubleshooting

### Error: "command not found: uv"
```bash
# Install uv first
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Error: "No module named 'ezdxf'"
```bash
# Install dependencies
uv pip install -r requirements.txt
```

### Output Files Not Generated
```bash
# Check if examples.py runs
uv run python examples.py

# Check output folder
ls -la examples_output/
```

### 3D Model Looks Strange
- Rooms: Use viewers that support transparency (e.g., MeshLab, Blender)
- Ensure input dimensions are reasonable
- Try running examples.py to see reference outputs

## Limitations

1. Simple text parser (does not support very complex descriptions)
2. Basic 3D models (no textures/materials)
3. Object features limited to predefined ones
4. No support for curved surfaces for all objects

## Future Development

- [ ] NLP parser for more natural descriptions
- [ ] Support for more furniture types
- [ ] Material and texture information
- [ ] Web-based GUI
- [ ] Export to other formats (STEP, IGES)
- [ ] Automatic geometry validation
- [ ] Real-time preview

## License

Open source project for educational purposes.

## Contributing

Contributions welcome! Feel free to open issues or pull requests.
#!/usr/bin/env python3

import os
import argparse
from text_parser import TextParser
from cad_generator import CADGenerator
from extruder_3d import Extruder3D


class TextToCAD:
    def __init__(self):
        self.parser = TextParser()
        self.cad_generator = CADGenerator()
        self.extruder = Extruder3D()

    def process_description(self, description: str, output_dir: str = "output", 
                          generate_3d: bool = False, filename_prefix: str = "design") -> None:
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        parsed_obj = self.parser.parse_description(description)
        
        print(f"Parsed object: {parsed_obj.object_type}")
        print(f"Dimensions: {parsed_obj.dimensions.width} x {parsed_obj.dimensions.length} x {parsed_obj.dimensions.height} cm")
        print(f"Features: {[f.name for f in parsed_obj.features]}")
        
        dxf_file = os.path.join(output_dir, f"{filename_prefix}.dxf")
        svg_file = os.path.join(output_dir, f"{filename_prefix}.svg")
        
        try:
            self.cad_generator.generate_dxf(parsed_obj, dxf_file)
            print(f"DXF file generated: {dxf_file}")
        except Exception as e:
            print(f"Error generating DXF: {e}")
        
        try:
            self.cad_generator.generate_svg(parsed_obj, svg_file)
            print(f"SVG file generated: {svg_file}")
        except Exception as e:
            print(f"Error generating SVG: {e}")
        
        if generate_3d:
            stl_file = os.path.join(output_dir, f"{filename_prefix}.stl")
            obj_file = os.path.join(output_dir, f"{filename_prefix}.obj")
            
            try:
                self.extruder.generate_stl(parsed_obj, stl_file)
                print(f"STL file generated: {stl_file}")
            except Exception as e:
                print(f"Error generating STL: {e}")
            
            try:
                self.extruder.generate_obj(parsed_obj, obj_file)
                print(f"OBJ file generated: {obj_file}")
            except Exception as e:
                print(f"Error generating OBJ: {e}")


def main():
    parser = argparse.ArgumentParser(description="Convert text description to CAD files")
    parser.add_argument("description", help="Text description of the object")
    parser.add_argument("-o", "--output", default="output", help="Output directory")
    parser.add_argument("-n", "--name", default="design", help="Output filename prefix")
    parser.add_argument("--3d", action="store_true", help="Generate 3D models (STL/OBJ)")
    
    args = parser.parse_args()
    
    converter = TextToCAD()
    converter.process_description(
        args.description, 
        args.output, 
        getattr(args, '3d'),
        args.name
    )


if __name__ == "__main__":
    main()
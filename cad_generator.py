"""
CAD Generator for creating DXF, SVG, and script files
"""

import ezdxf
import svgwrite
import math
from typing import List, Tuple
from pdf_rag import ParsedObject


class CADGenerator:
    """Generate CAD files from parsed objects"""
    
    def __init__(self):
        self.scale = 50
        self.margin = 20
        
        self.freecad_layers = {
            'parts': 'Parts',
            'dimensions': 'Dimensions', 
            'annotations': 'Annotations'
        }
    
    def generate_dxf(self, parsed_obj: ParsedObject, filename: str) -> None:
        """Generate DXF file optimized for FreeCAD"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        for layer_name in self.freecad_layers.values():
            doc.layers.new(name=layer_name)
        
        top_view_points = self._generate_top_view(parsed_obj)
        front_view_points = self._generate_front_view(parsed_obj)
        
        offset_x = parsed_obj.dimensions.width * self.scale + self.margin * 2
        
        self._draw_view_dxf(msp, top_view_points, self.margin, self.margin, "TOP VIEW", 'Parts')
        self._draw_view_dxf(msp, front_view_points, offset_x, self.margin, "FRONT VIEW", 'Parts')
        
        self._add_dimensions_dxf(msp, parsed_obj, self.margin, self.margin, "top")
        self._add_dimensions_dxf(msp, parsed_obj, offset_x, self.margin, "front")
        
        doc.saveas(filename)

    def generate_svg(self, parsed_obj: ParsedObject, filename: str) -> None:
        """Generate SVG file"""
        width = (parsed_obj.dimensions.width + parsed_obj.dimensions.length) * self.scale + self.margin * 4 + 100
        height = max(parsed_obj.dimensions.height, max(parsed_obj.dimensions.width, parsed_obj.dimensions.length)) * self.scale + self.margin * 3 + 80
        
        dwg = svgwrite.Drawing(filename, size=(f"{width}px", f"{height}px"))
        
        # Add black background
        dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="black"))
        
        top_view_points = self._generate_top_view(parsed_obj)
        front_view_points = self._generate_front_view(parsed_obj)
        
        offset_x = parsed_obj.dimensions.width * self.scale + self.margin * 2
        
        self._draw_view_svg(dwg, top_view_points, self.margin, self.margin, "TOP VIEW")
        self._draw_view_svg(dwg, front_view_points, offset_x, self.margin, "FRONT VIEW")
        
        self._add_dimensions_svg(dwg, parsed_obj, self.margin, self.margin, "top")
        self._add_dimensions_svg(dwg, parsed_obj, offset_x, self.margin, "front")
        
        dwg.save()

    def _generate_top_view(self, parsed_obj: ParsedObject) -> List[List[float]]:
        """Generate intelligent top view based on object type and features"""
        object_type = parsed_obj.object_type.lower()
        
        if object_type == "kursi":
            return self._generate_chair_top_view(parsed_obj)
        elif object_type == "meja":
            return self._generate_table_top_view(parsed_obj.dimensions.width * self.scale, parsed_obj.dimensions.length * self.scale)
        elif object_type == "sofa":
            return self._generate_sofa_top_view(parsed_obj.dimensions.width * self.scale, parsed_obj.dimensions.length * self.scale)
        elif object_type == "ruangan":
            return self._generate_room_top_view(parsed_obj.dimensions.width * self.scale, parsed_obj.dimensions.length * self.scale)
        elif object_type == "rumah":
            return self._generate_house_top_view(parsed_obj.dimensions.width * self.scale, parsed_obj.dimensions.length * self.scale)
        elif object_type == "lingkaran":
            return self._generate_circle_top_view(parsed_obj)
        else:
            return self._generate_generic_top_view(parsed_obj)

    def _generate_front_view(self, parsed_obj: ParsedObject) -> List[Tuple[float, float]]:
        """Generate realistic front view for different object types"""
        
        if parsed_obj.object_type == "kursi":
            return self._generate_chair_front_view()
        elif parsed_obj.object_type == "meja":
            return self._generate_table_front_view(parsed_obj)
        elif parsed_obj.object_type == "sofa":
            return self._generate_sofa_front_view(parsed_obj)
        elif parsed_obj.object_type == "ruangan":
            return self._generate_room_front_view(parsed_obj)
        elif parsed_obj.object_type == "rumah":
            return self._generate_house_front_view(parsed_obj)
        else:
            # Basic rectangle for unknown types
            width = parsed_obj.dimensions.width * self.scale
            height = parsed_obj.dimensions.height * self.scale
            return [(0, 0), (width, 0), (width, height), (0, height), (0, 0)]
    
    def _generate_chair_front_view(self) -> List[Tuple[float, float]]:
        """Generate chair front view showing profile with legs and backrest"""
        points = []
        
        # Actual chair dimensions (40x40cm seat, 45cm height)
        width = 0.40 * self.scale
        height = 0.45 * self.scale
        seat_height = 0.40 * self.scale  # Seat at 40cm from ground
        back_height = height
        seat_thickness = 0.04 * self.scale
        
        # Seat (horizontal rectangle)
        points.extend([
            (0, seat_height), (width, seat_height), 
            (width, seat_height + seat_thickness), (0, seat_height + seat_thickness), 
            (0, seat_height)
        ])
        
        # Backrest (vertical rectangle at back)
        points.append(None)  # Break line
        back_thickness = 0.02 * self.scale
        points.extend([
            (width - back_thickness, seat_height + seat_thickness), 
            (width, seat_height + seat_thickness),
            (width, back_height), 
            (width - back_thickness, back_height),
            (width - back_thickness, seat_height + seat_thickness)
        ])
        
        # Four legs (vertical lines)
        leg_inset = 0.03 * self.scale
        leg_positions_x = [leg_inset, width - leg_inset]  # Front and back legs
        
        for x in leg_positions_x:
            points.append(None)  # Break line
            # Left leg
            points.extend([(x, 0), (x, seat_height)])
            points.append(None)
            # Right leg  
            points.extend([(x + 0.35 * self.scale, 0), (x + 0.35 * self.scale, seat_height)])
        
        return points
    
    def _generate_table_front_view(self, parsed_obj: ParsedObject) -> List[Tuple[float, float]]:
        """Generate table front view"""
        points = []
        width = parsed_obj.dimensions.width * self.scale
        height = parsed_obj.dimensions.height * self.scale
        top_thickness = 0.05 * self.scale
        leg_thickness = 0.06 * self.scale
        
        # Table top
        points.extend([
            (0, height - top_thickness), (width, height - top_thickness),
            (width, height), (0, height), (0, height - top_thickness)
        ])
        
        # Four legs (two visible from front)
        leg_inset = 0.05 * self.scale
        for x in [leg_inset, width - leg_inset]:
            points.append(None)
            points.extend([
                (x, 0), (x, height - top_thickness),
                (x + leg_thickness, height - top_thickness), (x + leg_thickness, 0),
                (x, 0)
            ])
        
        return points
    
    def _generate_sofa_front_view(self, parsed_obj: ParsedObject) -> List[Tuple[float, float]]:
        """Generate sofa front view"""
        points = []
        width = parsed_obj.dimensions.width * self.scale
        height = parsed_obj.dimensions.height * self.scale
        seat_height = height * 0.4
        
        # Main body
        points.extend([
            (0, 0), (width, 0), (width, height), (0, height), (0, 0)
        ])
        
        # Seat line
        points.append(None)
        points.extend([(0, seat_height), (width, seat_height)])
        
        # Armrests profile
        arm_width = 0.15 * self.scale
        points.append(None)
        points.extend([(0, seat_height), (arm_width, height)])
        points.append(None)
        points.extend([(width - arm_width, height), (width, seat_height)])
        
        return points
    
    def _generate_room_front_view(self, parsed_obj: ParsedObject) -> List[Tuple[float, float]]:
        """Generate room front view (elevation)"""
        points = []
        width = parsed_obj.dimensions.width * self.scale
        height = parsed_obj.dimensions.height * self.scale
        
        # Wall outline
        points.extend([
            (0, 0), (width, 0), (width, height), (0, height), (0, 0)
        ])
        
        # Door (if on visible wall)
        door_width = 0.8 * self.scale
        door_height = 2.0 * self.scale
        door_x = width * 0.2  # Position door at 20% from left
        
        points.append(None)
        points.extend([
            (door_x, 0), (door_x, door_height),
            (door_x + door_width, door_height), (door_x + door_width, 0)
        ])
        
        return points
    
    def _generate_house_front_view(self, parsed_obj: ParsedObject) -> List[Tuple[float, float]]:
        """Generate house front view with roof"""
        points = []
        width = parsed_obj.dimensions.width * self.scale
        height = parsed_obj.dimensions.height * self.scale
        roof_height = height * 0.3
        
        # Main house structure
        points.extend([
            (0, 0), (width, 0), (width, height), (0, height), (0, 0)
        ])
        
        # Triangular roof
        points.append(None)
        points.extend([
            (0, height), (width/2, height + roof_height), (width, height)
        ])
        
        return points
    
    def _generate_chair_top_view(self, parsed_obj: ParsedObject) -> List[List[float]]:
        """Generate realistic chair top view: seat + 4 leg points"""
        width = parsed_obj.dimensions.width * self.scale
        length = parsed_obj.dimensions.length * self.scale
        
        # Main seat outline (rectangle)
        seat_points = [
            [-width/2, -length/2],
            [width/2, -length/2], 
            [width/2, length/2],
            [-width/2, length/2],
            [-width/2, -length/2]  # Close the rectangle
        ]
        
        # Add 4 leg points (small circles represented as points)
        leg_inset = 0.03 * self.scale  # 3cm from edge
        leg_points = [
            None,  # Separator
            [-width/2 + leg_inset, -length/2 + leg_inset],  # Front left leg
            None,  # Separator
            [width/2 - leg_inset, -length/2 + leg_inset],   # Front right leg  
            None,  # Separator
            [-width/2 + leg_inset, length/2 - leg_inset],   # Back left leg
            None,  # Separator
            [width/2 - leg_inset, length/2 - leg_inset]     # Back right leg
        ]
        
        return seat_points + leg_points
    
    def _generate_table_top_view(self, width: float, length: float) -> List:
        """Generate table top view showing surface and legs"""
        points = []
        
        # Table top outline
        points.extend([(0, 0), (width, 0), (width, length), (0, length), (0, 0)])
        
        # Four leg positions (larger than chair legs)
        leg_size = width * 0.06
        leg_inset = width * 0.05
        
        leg_positions = [
            (leg_inset, leg_inset),
            (width - leg_inset - leg_size, leg_inset),
            (leg_inset, length - leg_inset - leg_size),
            (width - leg_inset - leg_size, length - leg_inset - leg_size)
        ]
        
        for x, y in leg_positions:
            points.append(None)
            points.extend([
                (x, y), (x + leg_size, y), (x + leg_size, y + leg_size),
                (x, y + leg_size), (x, y)
            ])
            
        return points
    
    def _generate_sofa_top_view(self, width: float, length: float) -> List:
        """Generate sofa top view showing seat, back and arms"""
        points = []
        
        # Main body outline
        points.extend([(0, 0), (width, 0), (width, length), (0, length), (0, 0)])
        
        # Armrests (thick lines on sides)
        arm_width = width * 0.15
        
        # Left armrest
        points.append(None)
        points.extend([(0, 0), (arm_width, 0), (arm_width, length), (0, length)])
        
        # Right armrest  
        points.append(None)
        points.extend([(width - arm_width, 0), (width, 0), (width, length), (width - arm_width, length)])
        
        # Backrest (line at back)
        points.append(None)
        points.extend([(arm_width, length * 0.9), (width - arm_width, length * 0.9)])
        
        return points
    
    def _generate_room_top_view(self, parsed_obj, width: float, length: float) -> List:
        """Generate room top view with walls, door and window"""
        points = []
        wall_thickness = 20  # Scaled wall thickness
        
        # Outer walls
        points.extend([
            (-wall_thickness, -wall_thickness), 
            (width + wall_thickness, -wall_thickness),
            (width + wall_thickness, length + wall_thickness),
            (-wall_thickness, length + wall_thickness),
            (-wall_thickness, -wall_thickness)
        ])
        
        # Inner space
        points.append(None)
        points.extend([(0, 0), (width, 0), (width, length), (0, length), (0, 0)])
        
        # Door opening (west side - left wall)
        door_width = width * 0.2
        door_start = length * 0.4
        points.append(None)
        points.extend([(-wall_thickness, door_start), (0, door_start)])
        points.append(None)
        points.extend([(-wall_thickness, door_start + door_width), (0, door_start + door_width)])
        
        # Window opening (north side - top wall)  
        window_width = width * 0.3
        window_start = width * 0.35
        points.append(None)
        points.extend([(window_start, length), (window_start, length + wall_thickness)])
        points.append(None)
        points.extend([(window_start + window_width, length), (window_start + window_width, length + wall_thickness)])
        
        return points
    
    def _add_chair_features_2d(self, points: List, parsed_obj: ParsedObject, width: float, length: float):
        """Add object-specific features"""
        if parsed_obj.object_type == "kursi":
            self._add_chair_legs(points, width, length)
        elif parsed_obj.object_type == "meja":
            self._add_table_legs(points, width, length)
        elif parsed_obj.object_type == "ruangan":
            self._add_room_openings(points, parsed_obj, width, length)

    def _add_chair_legs(self, points: List, width: float, length: float):
        """Add chair legs in top view"""
        leg_size = 6 * self.scale / 50
        margin = 8 * self.scale / 50
        
        leg_positions = [
            (margin, margin),
            (width - margin - leg_size, margin),
            (width - margin - leg_size, length - margin - leg_size),
            (margin, length - margin - leg_size)
        ]
        
        for x, y in leg_positions:
            points.append(None)
            points.extend([
                (x, y), (x + leg_size, y), (x + leg_size, y + leg_size), 
                (x, y + leg_size), (x, y)
            ])

    def _add_table_legs(self, points: List, width: float, length: float):
        """Add table legs in top view"""
        leg_size = 8 * self.scale / 50
        margin = 12 * self.scale / 50
        
        leg_positions = [
            (margin, margin),
            (width - margin - leg_size, margin),
            (width - margin - leg_size, length - margin - leg_size),
            (margin, length - margin - leg_size)
        ]
        
        for x, y in leg_positions:
            points.append(None)
            points.extend([
                (x, y), (x + leg_size, y), (x + leg_size, y + leg_size),
                (x, y + leg_size), (x, y)
            ])

    def _add_room_openings(self, points: List, parsed_obj: ParsedObject, width: float, length: float):
        """Add room openings (doors, windows)"""
        for feature in parsed_obj.features:
            if feature.name == "pintu":
                door_width = 20 * self.scale / 50
                if "selatan" in feature.position or "south" in feature.position:
                    x_pos = width/2 - door_width/2
                    points.append(None)
                    points.extend([(x_pos, 0), (x_pos + door_width, 0)])
            
            elif feature.name == "jendela":
                window_width = 15 * self.scale / 50
                if "timur" in feature.position or "east" in feature.position:
                    y_pos = length/2 - window_width/2
                    points.append(None)
                    points.extend([(width, y_pos), (width, y_pos + window_width)])

    def _draw_view_dxf(self, msp, points: List, offset_x: float, offset_y: float, title: str, layer: str):
        """Draw view in DXF"""
        current_polyline = []
        
        for point in points:
            if point is None:
                if current_polyline:
                    msp.add_lwpolyline(current_polyline, dxfattribs={'layer': layer})
                    current_polyline = []
            else:
                x, y = point
                current_polyline.append((x + offset_x, y + offset_y))
        
        if current_polyline:
            msp.add_lwpolyline(current_polyline, dxfattribs={'layer': layer})
        
        text = msp.add_text(title, dxfattribs={'layer': 'Annotations'})
        text.set_placement((offset_x, offset_y - 15))

    def _draw_view_svg(self, dwg, points: List, offset_x: float, offset_y: float, title: str):
        """Draw view in SVG"""
        path_data = []
        
        for i, point in enumerate(points):
            if point is None:
                continue
            
            x, y = point
            x += offset_x
            y = offset_y + y
            
            if i == 0 or points[i-1] is None:
                path_data.append(f"M {x} {y}")
            else:
                path_data.append(f"L {x} {y}")
        
        if path_data:
            dwg.add(dwg.path(d=" ".join(path_data), stroke="#0080FF", fill="none", stroke_width=2))
        
        # Title with white color and better positioning
        dwg.add(dwg.text(title, insert=(offset_x, offset_y - 20), 
                        font_size="14px", fill="white", font_weight="bold"))

    def _add_dimensions_dxf(self, msp, parsed_obj: ParsedObject, offset_x: float, offset_y: float, view_type: str):
        """Add dimensions to DXF"""
        if view_type == "top":
            width_text = f"{parsed_obj.dimensions.width:.2f}m"
            length_text = f"{parsed_obj.dimensions.length:.2f}m"
            
            width_label = msp.add_text(width_text, dxfattribs={'layer': 'Dimensions'})
            width_label.set_placement((offset_x + parsed_obj.dimensions.width * self.scale / 2, offset_y - 30))
            
            length_label = msp.add_text(length_text, dxfattribs={'layer': 'Dimensions'})
            length_label.set_placement((offset_x - 50, offset_y + parsed_obj.dimensions.length * self.scale / 2))

    def _add_dimensions_svg(self, dwg, parsed_obj: ParsedObject, offset_x: float, offset_y: float, view_type: str):
        """Add dimensions to SVG with proper colors and spacing"""
        if view_type == "top":
            width_text = f"{parsed_obj.dimensions.width:.2f}m"
            length_text = f"{parsed_obj.dimensions.length:.2f}m"
            
            # Width dimension (below the shape, green color)
            dwg.add(dwg.text(width_text, 
                           insert=(offset_x + parsed_obj.dimensions.width * self.scale / 2, 
                                  offset_y + parsed_obj.dimensions.length * self.scale + 25),
                           font_size="12px", text_anchor="middle", fill="#00FF00", font_weight="bold"))
            
            # Length dimension (left side of shape, green color)  
            dwg.add(dwg.text(length_text,
                           insert=(offset_x - 40, offset_y + parsed_obj.dimensions.length * self.scale / 2),
                           font_size="12px", text_anchor="middle", fill="#00FF00", font_weight="bold"))

    def create_2d_views(self, parsed_data: dict, dxf_output: str, svg_output: str):
        """Create 2D views (top and front) for furniture or rooms"""
        furniture_type = parsed_data['type']
        dimensions = parsed_data['dimensions']
        features = parsed_data.get('features', {})
        
        if not dimensions:
            # Default dimensions based on type
            if furniture_type == 'chair':
                dimensions = self._get_default_chair_dimensions()
            elif furniture_type == 'table':
                dimensions = self._get_default_table_dimensions()
            elif furniture_type == 'room':
                dimensions = self._get_default_room_dimensions()
            elif furniture_type == 'house':
                dimensions = self._get_default_house_dimensions()
            else:
                dimensions = type('Dimensions', (), {'width': 1.0, 'length': 1.0, 'height': 0.8})()
        
        # Create DXF file
        self._create_dxf_views(furniture_type, dimensions, features, dxf_output)
        
        # Create SVG file
        self._create_svg_views(furniture_type, dimensions, features, svg_output)
    
    def _get_default_chair_dimensions(self):
        """Default chair dimensions (40x40x45cm)"""
        return type('Dimensions', (), {'width': 0.40, 'length': 0.40, 'height': 0.45})()
    
    def _get_default_table_dimensions(self):
        """Default table dimensions (80x120x75cm)"""
        return type('Dimensions', (), {'width': 0.80, 'length': 1.20, 'height': 0.75})()
    
    def _get_default_room_dimensions(self):
        """Default room dimensions (4x5x3m)"""
        return type('Dimensions', (), {'width': 4.0, 'length': 5.0, 'height': 3.0})()
    
    def _get_default_house_dimensions(self):
        """Default house dimensions (8x10x3.5m)"""
        return type('Dimensions', (), {'width': 8.0, 'length': 10.0, 'height': 3.5})()
    
    def _create_dxf_views(self, furniture_type: str, dimensions, features: dict, output_file: str):
        """Create DXF with top and front views"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        # Create layers
        doc.layers.new(name='TOP_VIEW', dxfattribs={'color': 1})  # Red
        doc.layers.new(name='FRONT_VIEW', dxfattribs={'color': 2})  # Yellow
        doc.layers.new(name='DIMENSIONS', dxfattribs={'color': 3})  # Green
        
        scale = 100  # 1 unit = 1cm in DXF
        
        # TOP VIEW (left side)
        top_offset_x = 0
        top_offset_y = 0
        
        if furniture_type == 'chair':
            self._draw_chair_top_view_dxf(msp, dimensions, features, scale, top_offset_x, top_offset_y)
        elif furniture_type == 'table':
            self._draw_table_top_view_dxf(msp, dimensions, features, scale, top_offset_x, top_offset_y)
        elif furniture_type == 'room':
            self._draw_room_top_view_dxf(msp, dimensions, features, scale, top_offset_x, top_offset_y)
        elif furniture_type == 'house':
            self._draw_house_top_view_dxf(msp, dimensions, features, scale, top_offset_x, top_offset_y)
        
        # FRONT VIEW (right side)
        front_offset_x = (dimensions.width * scale) + 200  # 2cm gap
        front_offset_y = 0
        
        if furniture_type == 'chair':
            self._draw_chair_front_view_dxf(msp, dimensions, features, scale, front_offset_x, front_offset_y)
        elif furniture_type == 'table':
            self._draw_table_front_view_dxf(msp, dimensions, features, scale, front_offset_x, front_offset_y)
        elif furniture_type == 'room':
            self._draw_room_front_view_dxf(msp, dimensions, features, scale, front_offset_x, front_offset_y)
        elif furniture_type == 'house':
            self._draw_house_front_view_dxf(msp, dimensions, features, scale, front_offset_x, front_offset_y)
        
        # Add labels
        text1 = msp.add_text("TOP VIEW", dxfattribs={'layer': 'DIMENSIONS'})
        text1.set_placement((top_offset_x, top_offset_y + dimensions.length * scale + 20))
        
        text2 = msp.add_text("FRONT VIEW", dxfattribs={'layer': 'DIMENSIONS'})
        text2.set_placement((front_offset_x, front_offset_y + dimensions.height * scale + 20))
        
        doc.saveas(output_file)
    
    def _draw_chair_top_view_dxf(self, msp, dimensions, features, scale, offset_x, offset_y):
        """Draw chair top view in DXF"""
        width = dimensions.width * scale
        length = dimensions.length * scale
        
        # Seat rectangle
        msp.add_lwpolyline([
            (offset_x, offset_y), (offset_x + width, offset_y),
            (offset_x + width, offset_y + length), (offset_x, offset_y + length), (offset_x, offset_y)
        ], dxfattribs={'layer': 'TOP_VIEW'})
        
        # 4 leg points
        margin = 5
        for pos in [(offset_x + margin, offset_y + margin), (offset_x + width - margin, offset_y + margin),
                   (offset_x + width - margin, offset_y + length - margin), (offset_x + margin, offset_y + length - margin)]:
            msp.add_circle(pos, 2, dxfattribs={'layer': 'TOP_VIEW'})
    
    def _draw_chair_front_view_dxf(self, msp, dimensions, features, scale, offset_x, offset_y):
        """Draw chair front view in DXF"""
        width = dimensions.width * scale
        height = dimensions.height * scale
        seat_height = height * 0.5
        
        # Seat line
        msp.add_line((offset_x, offset_y + seat_height), (offset_x + width, offset_y + seat_height), dxfattribs={'layer': 'FRONT_VIEW'})
        # Legs
        margin = 5
        msp.add_line((offset_x + margin, offset_y), (offset_x + margin, offset_y + seat_height), dxfattribs={'layer': 'FRONT_VIEW'})
        msp.add_line((offset_x + width - margin, offset_y), (offset_x + width - margin, offset_y + seat_height), dxfattribs={'layer': 'FRONT_VIEW'})
        # Backrest
        msp.add_lwpolyline([
            (offset_x, offset_y + seat_height), (offset_x, offset_y + height), 
            (offset_x + width, offset_y + height), (offset_x + width, offset_y + seat_height)
        ], dxfattribs={'layer': 'FRONT_VIEW'})
    
    def _draw_table_top_view_dxf(self, msp, dimensions, features, scale, offset_x, offset_y):
        """Draw table top view in DXF"""
        width = dimensions.width * scale
        length = dimensions.length * scale
        
        # Table surface
        msp.add_lwpolyline([
            (offset_x, offset_y), (offset_x + width, offset_y),
            (offset_x + width, offset_y + length), (offset_x, offset_y + length), (offset_x, offset_y)
        ], dxfattribs={'layer': 'TOP_VIEW'})
        
        # 4 legs at corners
        margin = 10
        for pos in [(offset_x + margin, offset_y + margin), (offset_x + width - margin, offset_y + margin),
                   (offset_x + width - margin, offset_y + length - margin), (offset_x + margin, offset_y + length - margin)]:
            msp.add_circle(pos, 3, dxfattribs={'layer': 'TOP_VIEW'})
    
    def _draw_table_front_view_dxf(self, msp, dimensions, features, scale, offset_x, offset_y):
        """Draw table front view in DXF"""
        width = dimensions.width * scale
        height = dimensions.height * scale
        
        # Table top (thick line)
        msp.add_line((offset_x, offset_y + height - 5), (offset_x + width, offset_y + height - 5), dxfattribs={'layer': 'FRONT_VIEW'})
        msp.add_line((offset_x, offset_y + height), (offset_x + width, offset_y + height), dxfattribs={'layer': 'FRONT_VIEW'})
        # Legs
        margin = 10
        msp.add_line((offset_x + margin, offset_y), (offset_x + margin, offset_y + height - 5), dxfattribs={'layer': 'FRONT_VIEW'})
        msp.add_line((offset_x + width - margin, offset_y), (offset_x + width - margin, offset_y + height - 5), dxfattribs={'layer': 'FRONT_VIEW'})
    
    def _draw_room_top_view_dxf(self, msp, dimensions, features, scale, offset_x, offset_y):
        """Draw room top view in DXF"""
        width = dimensions.width * scale
        length = dimensions.length * scale
        
        # Room outline
        msp.add_lwpolyline([
            (offset_x, offset_y), (offset_x + width, offset_y),
            (offset_x + width, offset_y + length), (offset_x, offset_y + length), (offset_x, offset_y)
        ], dxfattribs={'layer': 'TOP_VIEW'})
        
        # Door (gap in west wall)
        num_doors = features.get('doors', 0) or 0
        if num_doors > 0:
            door_width = 80
            door_y = offset_y + length/2 - door_width/2
            msp.add_line((offset_x, door_y), (offset_x, door_y + door_width), dxfattribs={'layer': 'FRONT_VIEW', 'color': 4})
        
        # Window (mark on north wall)
        num_windows = features.get('windows', 0) or 0
        if num_windows > 0:
            window_width = 120
            window_x = offset_x + width/2 - window_width/2
            msp.add_line((window_x, offset_y + length), (window_x + window_width, offset_y + length), dxfattribs={'layer': 'FRONT_VIEW', 'color': 5})
    
    def _draw_room_front_view_dxf(self, msp, dimensions, features, scale, offset_x, offset_y):
        """Draw room front view in DXF"""
        width = dimensions.width * scale
        height = dimensions.height * scale
        
        # Room outline
        msp.add_lwpolyline([
            (offset_x, offset_y), (offset_x + width, offset_y),
            (offset_x + width, offset_y + height), (offset_x, offset_y + height), (offset_x, offset_y)
        ], dxfattribs={'layer': 'FRONT_VIEW'})
        
        # Window
        num_windows = features.get('windows', 0) or 0
        if num_windows > 0:
            window_width, window_height = 120, 100
            window_x = offset_x + width/2 - window_width/2
            window_y = offset_y + height/2 - window_height/2
            msp.add_lwpolyline([
                (window_x, window_y), (window_x + window_width, window_y),
                (window_x + window_width, window_y + window_height), (window_x, window_y + window_height), (window_x, window_y)
            ], dxfattribs={'layer': 'FRONT_VIEW', 'color': 5})
    
    def _create_svg_views(self, furniture_type: str, dimensions, features: dict, output_file: str):
        """Create SVG with colored top and front views"""
        
        # Better scale calculation based on furniture type
        if furniture_type in ['house']:
            scale = 15   # Houses
        elif furniture_type in ['room']:
            scale = 30  # Rooms  
        else:  # furniture (chairs, tables)
            scale = 150  # Much larger furniture for better visibility
            
        margin = 80
        text_height = 60
        dimension_space = 80
        
        # Calculate proper SVG dimensions with correct orientation
        if furniture_type == 'chair':
            top_view_width = dimensions.length * scale
            top_view_height = dimensions.width * scale
            front_view_width = dimensions.width * scale
            front_view_height = dimensions.height * scale
        elif furniture_type == 'sofa':
            # Sofa: length (2.0m) is horizontal width, width (0.9m) is depth
            top_view_width = dimensions.length * scale
            top_view_height = dimensions.width * scale
            front_view_width = dimensions.length * scale
            front_view_height = dimensions.height * scale
        else:
            top_view_width = dimensions.width * scale
            top_view_height = dimensions.length * scale
            front_view_width = dimensions.width * scale
            front_view_height = dimensions.height * scale
        
        # SVG canvas size with generous spacing
        view_spacing = 120
        svg_width = top_view_width + front_view_width + (margin * 2) + view_spacing + dimension_space
        svg_height = max(top_view_height, front_view_height) + (margin * 2) + text_height + dimension_space + 80
        
        dwg = svgwrite.Drawing(output_file, size=(f'{svg_width}px', f'{svg_height}px'), profile='tiny')
        
        # Background
        dwg.add(dwg.rect((0, 0), (svg_width, svg_height), fill='white', stroke='black'))
        
        # Top view (left side)
        top_x = margin
        top_y = margin + text_height
        
        self._draw_furniture_svg(dwg, furniture_type, dimensions, features, scale, top_x, top_y, 'top')
        
        # Front view (right side)  
        front_x = margin + top_view_width + view_spacing
        front_y = margin + text_height
        
        self._draw_furniture_svg(dwg, furniture_type, dimensions, features, scale, front_x, front_y, 'front')
        
        # Clear labels in English with proper font size
        dwg.add(dwg.text('TOP VIEW', insert=(top_x, margin + 35), 
                        fill='black', font_size='16px', font_weight='bold'))
        dwg.add(dwg.text('FRONT VIEW', insert=(front_x, margin + 35), 
                        fill='black', font_size='16px', font_weight='bold'))
        
        # Dimensions text: L × W × H format
        dim_y = top_y + max(top_view_height, front_view_height) + 50
        
        if dimensions.length >= dimensions.width:
            length_val, width_val = dimensions.length, dimensions.width
        else:
            length_val, width_val = dimensions.width, dimensions.length
        
        dim_text = f'Dimensions: {length_val:.2f}m × {width_val:.2f}m × {dimensions.height:.2f}m'
        dwg.add(dwg.text(dim_text, insert=(margin, dim_y), fill='red', font_size='14px', font_weight='bold'))
        
        # Add dimension lines for both views
        if furniture_type == 'chair':
            self._add_dimension_lines_svg(dwg, top_x, top_y, top_view_width, top_view_height, 
                                        dimensions.length, dimensions.width, scale)
            self._add_dimension_lines_svg(dwg, front_x, front_y, front_view_width, front_view_height,
                                        dimensions.width, dimensions.height, scale)
        elif furniture_type == 'sofa':
            # Sofa: length is horizontal, width is depth
            self._add_dimension_lines_svg(dwg, top_x, top_y, top_view_width, top_view_height, 
                                        dimensions.length, dimensions.width, scale)
            self._add_dimension_lines_svg(dwg, front_x, front_y, front_view_width, front_view_height,
                                        dimensions.length, dimensions.height, scale)
        else:
            self._add_dimension_lines_svg(dwg, top_x, top_y, top_view_width, top_view_height, 
                                        dimensions.width, dimensions.length, scale)
            self._add_dimension_lines_svg(dwg, front_x, front_y, front_view_width, front_view_height,
                                        dimensions.width, dimensions.height, scale)
        
        dwg.save(pretty=True, indent=2)
    
    def _add_dimension_lines_svg(self, dwg, x, y, width, height, real_width, real_length, scale):
        """Add dimension lines to SVG"""
        offset = 15
        line_extend = 8
        
        # Width dimension (bottom)
        line_y = y + height + offset
        dwg.add(dwg.line((x, line_y), (x + width, line_y), stroke='red', stroke_width=1.5))
        dwg.add(dwg.line((x, line_y - line_extend), (x, line_y + line_extend), stroke='red', stroke_width=1.5))
        dwg.add(dwg.line((x + width, line_y - line_extend), (x + width, line_y + line_extend), stroke='red', stroke_width=1.5))
        dwg.add(dwg.text(f'{real_width:.2f}m', insert=(x + width/2 - 15, line_y + 18), fill='red', font_size='11px'))
        
        # Length dimension (right side)
        line_x = x + width + offset
        dwg.add(dwg.line((line_x, y), (line_x, y + height), stroke='red', stroke_width=1.5))
        dwg.add(dwg.line((line_x - line_extend, y), (line_x + line_extend, y), stroke='red', stroke_width=1.5))
        dwg.add(dwg.line((line_x - line_extend, y + height), (line_x + line_extend, y + height), stroke='red', stroke_width=1.5))
        
        # Rotated text for length
        text_elem = dwg.text(f'{real_length:.2f}m', insert=(line_x + 10, y + height/2 + 5), fill='red', font_size='11px')
        text_elem.rotate(-90, (line_x + 10, y + height/2))
        dwg.add(text_elem)
        
    def _draw_furniture_svg(self, dwg, furniture_type, dimensions, features, scale, x, y, view):
        """Draw furniture in SVG for specified view"""
        if furniture_type == 'chair':
            if view == 'top':
                # Simple seat rectangle (square)
                width, length = dimensions.width * scale, dimensions.length * scale
                dwg.add(dwg.rect((x, y), (width, length), 
                               fill='lightblue', stroke='blue', stroke_width=2))
                
                # 4 legs at corners (exact positions)
                leg_size = 3
                margin = 5  # 5px from edge
                leg_positions = [
                    (x + margin, y + margin),                      # Top-left
                    (x + width - margin, y + margin),              # Top-right  
                    (x + width - margin, y + length - margin),     # Bottom-right
                    (x + margin, y + length - margin)              # Bottom-left
                ]
                
                for pos in leg_positions:
                    dwg.add(dwg.circle(pos, leg_size, fill='brown', stroke='black', stroke_width=1))
                
                # Simple label
                dwg.add(dwg.text('SEAT', insert=(x + width/2 - 10, y + length/2 + 2), 
                               fill='black', font_size='10px', font_weight='bold'))
                    
            else:  # front view - legs should match dimension lines exactly
                width, height = dimensions.width * scale, dimensions.height * scale
                
                # Seat (thin horizontal rectangle at top)
                seat_height = 4
                seat_y = y  # Seat at the very top
                dwg.add(dwg.rect((x, seat_y), (width, seat_height), 
                               fill='lightblue', stroke='blue', stroke_width=2))
                
                # 2 visible legs (front legs only) - FULL HEIGHT from bottom to seat
                margin = 5  # Same as top view
                leg_width = 3
                
                # Left leg - from bottom (y + height) to seat bottom (seat_y + seat_height)
                dwg.add(dwg.line((x + margin, y + height), (x + margin, seat_y + seat_height), 
                               stroke='brown', stroke_width=leg_width))
                
                # Right leg - from bottom (y + height) to seat bottom (seat_y + seat_height)
                dwg.add(dwg.line((x + width - margin, y + height), (x + width - margin, seat_y + seat_height), 
                               stroke='brown', stroke_width=leg_width))
                
                # Simple labels
                dwg.add(dwg.text('SEAT', insert=(x + width/2 - 10, seat_y - 5), 
                               fill='black', font_size='9px', font_weight='bold'))
                dwg.add(dwg.text('LEGS', insert=(x + 2, y + height - 5), 
                               fill='brown', font_size='8px', font_weight='bold'))
        
        elif furniture_type == 'table':
            is_circular = features.get('seat_shape') == 'circular'
            
            if view == 'top':
                width, length = dimensions.width * scale, dimensions.length * scale
                
                if is_circular:
                    # Draw circular table top
                    radius = width / 2
                    center_x = x + radius
                    center_y = y + radius
                    dwg.add(dwg.circle((center_x, center_y), radius, 
                                     fill='lightgreen', stroke='green', stroke_width=2))
                    
                    # Add "CIRCULAR" label
                    dwg.add(dwg.text('Ø', insert=(center_x - 5, center_y + 5), 
                                   fill='black', font_size='20px', font_weight='bold'))
                    
                    num_legs = int(features.get('legs', 4) or 4)
                    leg_radius = radius * 0.7
                    edge_distance = radius - leg_radius
                    for i in range(num_legs):
                        angle = (2 * math.pi * i / num_legs) - (math.pi / 2)
                        leg_x = center_x + leg_radius * math.cos(angle)
                        leg_y = center_y + leg_radius * math.sin(angle)
                        dwg.add(dwg.circle((leg_x, leg_y), 5, fill='red', stroke='darkred', stroke_width=2))
                    
                    actual_distance_cm = edge_distance / scale * 100
                    dwg.add(dwg.text(f'Leg to edge distance: {actual_distance_cm:.0f} cm', 
                                   insert=(center_x - 55, y - 15), 
                                   fill='red', font_size='9px', font_weight='bold'))
                else:
                    dwg.add(dwg.rect((x, y), (width, length), 
                                   fill='lightgreen', stroke='green', stroke_width=2))
                    margin = 10
                    for pos in [(x + margin, y + margin), (x + width - margin, y + margin),
                               (x + width - margin, y + length - margin), (x + margin, y + length - margin)]:
                        dwg.add(dwg.circle(pos, 4, fill='brown', stroke='black'))
                        
            else:  # front view
                width, height = dimensions.width * scale, dimensions.height * scale
                
                # Table top (thin horizontal bar) - same for circular and rectangular
                dwg.add(dwg.rect((x, y), (width, 8), 
                               fill='lightgreen', stroke='green', stroke_width=2))
                
                # Legs
                num_legs = int(features.get('legs', 4) or 4)
                # For 4-leg table, show 2 legs at sides
                margin = 10
                leg_positions = [margin, width - margin]
                
                for leg_x in leg_positions:
                    dwg.add(dwg.line((x + leg_x, y + 8), (x + leg_x, y + height), 
                                   stroke='brown', stroke_width=4))
        
        elif furniture_type == 'room':
            if view == 'top':
                # Room outline (persegi panjang 4x5)
                width, length = dimensions.width * scale, dimensions.length * scale
                dwg.add(dwg.rect((x, y), (width, length), fill='lightyellow', stroke='black', stroke_width=3))
                
                # Door symbol (gap + door swing)
                num_doors = features.get('doors', 0) or 0
                if num_doors > 0:
                    door_width = 30  # 80cm door scaled
                    door_y = y + length/2 - door_width/2
                    
                    # Door opening (gap in west wall)
                    dwg.add(dwg.line((x, door_y), (x, door_y + door_width), stroke='white', stroke_width=6))
                    dwg.add(dwg.line((x, door_y), (x, door_y + door_width), stroke='red', stroke_width=2, stroke_dasharray='3,3'))
                    
                    # Door swing arc
                    dwg.add(dwg.path(d=f'M {x} {door_y} A {door_width} {door_width} 0 0 1 {x + door_width} {door_y + door_width}', 
                                   stroke='red', fill='none', stroke_width=1, stroke_dasharray='2,2'))
                    
                    # Door label
                    dwg.add(dwg.text('PINTU', insert=(x - 40, door_y + door_width/2), fill='red', font_size='10px', font_weight='bold'))
                
                # Window symbol
                num_windows = features.get('windows', 0) or 0
                if num_windows > 0:
                    window_width = 40  # 120cm window scaled
                    window_x = x + width/2 - window_width/2
                    
                    # Window opening
                    dwg.add(dwg.line((window_x, y), (window_x + window_width, y), stroke='white', stroke_width=6))
                    dwg.add(dwg.line((window_x, y), (window_x + window_width, y), stroke='blue', stroke_width=3))
                    
                    # Window frame
                    dwg.add(dwg.rect((window_x, y - 3), (window_width, 6), fill='lightblue', stroke='blue', stroke_width=1))
                    
                    # Window label
                    dwg.add(dwg.text('JENDELA', insert=(window_x + 5, y - 10), fill='blue', font_size='10px', font_weight='bold'))
                    
            else:  # front view - shows NORTH wall (where window is in top view)
                width, height = dimensions.width * scale, dimensions.height * scale
                dwg.add(dwg.rect((x, y), (width, height), fill='lightyellow', stroke='black', stroke_width=3))
                
                # Window in front view (north wall - matches top view)
                num_windows = features.get('windows', 0) or 0
                if num_windows > 0:
                    window_width, window_height = 40, 30
                    window_x = x + width/2 - window_width/2  # Center of north wall
                    window_y = y + height/2 - window_height/2  # Middle height
                    dwg.add(dwg.rect((window_x, window_y), (window_width, window_height), 
                                   fill='lightblue', stroke='blue', stroke_width=2))
                    
                    # Window cross
                    dwg.add(dwg.line((window_x + window_width/2, window_y), (window_x + window_width/2, window_y + window_height), 
                                   stroke='blue', stroke_width=1))
                    dwg.add(dwg.line((window_x, window_y + window_height/2), (window_x + window_width, window_y + window_height/2), 
                                   stroke='blue', stroke_width=1))
                    
                    # Window label
                    dwg.add(dwg.text('JENDELA', insert=(window_x + 5, window_y - 5), 
                                   fill='blue', font_size='8px', font_weight='bold'))
                
                # Note: Door is on WEST wall (left side in top view), not visible in NORTH front view
                # Add label to clarify
                dwg.add(dwg.text('NORTH WALL VIEW', insert=(x + 5, y + height - 5), 
                               fill='gray', font_size='7px', font_style='italic'))
        
        # Simple house type drawing
        elif furniture_type == 'house':
            has_garage = features.get('has_garage', False)
            is_modern = features.get('style') == 'modern'
            num_bedrooms = int(features.get('bedrooms', 2) or 2)
            
            if view == 'top':
                width, length = dimensions.width * scale, dimensions.length * scale
                
                # Main house body
                main_width = width * 0.75 if has_garage else width
                dwg.add(dwg.rect((x, y), (main_width, length), 
                               fill='wheat', stroke='darkred', stroke_width=2))
                
                # Garage (if exists) - positioned at BACK/SOUTH side (aligned with entrance)
                if has_garage:
                    garage_width = width * 0.25
                    garage_length_2d = length * 0.5
                    garage_y_start = y + length - garage_length_2d  # Start from back (south)
                    dwg.add(dwg.rect((x + main_width, garage_y_start), (garage_width, garage_length_2d), 
                                   fill='lightgray', stroke='darkred', stroke_width=2))
                    # Garage door (at the back/south side)
                    dwg.add(dwg.rect((x + main_width + 2, y + length - 2), (garage_width - 4, 4), 
                                   fill='gray', stroke='black', stroke_width=1))
                    dwg.add(dwg.text('GARAGE', insert=(x + main_width + 5, garage_y_start + 20), 
                                   fill='black', font_size='7px', font_weight='bold'))
                
                # Room divisions (bedrooms)
                if num_bedrooms >= 2:
                    # Living area (bottom 40%)
                    living_y = y + length * 0.6
                    dwg.add(dwg.line((x, living_y), (x + main_width, living_y), 
                                   stroke='darkred', stroke_width=1, stroke_dasharray='3,3'))
                    dwg.add(dwg.text('LIVING', insert=(x + main_width/2 - 15, y + length * 0.8), 
                                   fill='darkred', font_size='8px'))
                    
                    # Bedrooms (top 60%, divided)
                    bedroom_div_x = x + main_width/2
                    dwg.add(dwg.line((bedroom_div_x, y), (bedroom_div_x, living_y), 
                                   stroke='darkred', stroke_width=1, stroke_dasharray='3,3'))
                    dwg.add(dwg.text('BR1', insert=(x + main_width/4 - 8, y + length*0.3), 
                                   fill='darkred', font_size='8px'))
                    dwg.add(dwg.text('BR2', insert=(x + main_width*0.75 - 8, y + length*0.3), 
                                   fill='darkred', font_size='8px'))
                
                # Main entrance
                door_width = 15
                door_x = x + main_width/2 - door_width/2
                dwg.add(dwg.rect((door_x, y + length - 2), (door_width, 4), 
                               fill='brown', stroke='black', stroke_width=1))
                dwg.add(dwg.text('ENTRANCE', insert=(door_x - 10, y + length + 12), 
                               fill='brown', font_size='7px', font_weight='bold'))
                
                # Windows in top view (distributed on left and right walls)
                num_windows = int(features.get('windows', 4) or 4)  # Default 4 if not specified
                windows_per_side = num_windows // 2
                
                if windows_per_side > 0:
                    window_size = 12
                    window_spacing = length / (windows_per_side + 1)
                    
                    for i in range(windows_per_side):
                        window_y = y + window_spacing * (i + 1)
                        
                        # Left wall windows (west side)
                        dwg.add(dwg.rect((x - 2, window_y - window_size/2), (4, window_size), 
                                       fill='lightblue', stroke='blue', stroke_width=1))
                        
                        # Right wall windows (east side)
                        dwg.add(dwg.rect((x + main_width - 2, window_y - window_size/2), (4, window_size), 
                                       fill='lightblue', stroke='blue', stroke_width=1))
                
            else:  # front view
                width, height = dimensions.width * scale, dimensions.height * scale
                
                # Main house body
                main_width = width * 0.7 if has_garage else width
                dwg.add(dwg.rect((x, y), (main_width, height), 
                               fill='wheat', stroke='darkred', stroke_width=2))
                
                # Roof
                if is_modern:
                    # Flat/minimal slope roof
                    roof_height = 10
                    dwg.add(dwg.polygon([(x - 5, y), (x + main_width + 5, y), 
                                       (x + main_width, y - roof_height), (x, y - roof_height)], 
                                      fill='darkslategray', stroke='black', stroke_width=1))
                else:
                    # Traditional triangular roof
                    roof_height = 20
                    dwg.add(dwg.polygon([(x - 5, y), (x + main_width/2, y - roof_height), 
                                       (x + main_width + 5, y)], 
                                      fill='brown', stroke='darkred', stroke_width=2))
                
                # Garage (if exists)
                if has_garage:
                    garage_width = width * 0.3
                    garage_height = height * 0.65
                    dwg.add(dwg.rect((x + main_width, y + height - garage_height), 
                                   (garage_width, garage_height), 
                                   fill='lightgray', stroke='darkred', stroke_width=2))
                    # Garage door with panels
                    for i in range(5):
                        panel_y = y + height - garage_height + (i * garage_height / 5)
                        dwg.add(dwg.line((x + main_width + 2, panel_y), 
                                       (x + main_width + garage_width - 2, panel_y), 
                                       stroke='gray', stroke_width=1))
                
                # NO WINDOWS on front wall - windows are on side walls (visible in top view)
                # Main door (centered on front wall)
                door_width, door_height = 15, 30
                door_x = x + main_width/2 - door_width/2  # Centered on main house
                door_y = y + height - door_height
                dwg.add(dwg.rect((door_x, door_y), (door_width, door_height), 
                               fill='saddlebrown', stroke='black', stroke_width=2))
                # Door handle
                dwg.add(dwg.circle((door_x + door_width - 3, door_y + door_height/2), 2, 
                               fill='gold', stroke='black'))
        
        elif furniture_type == 'sofa':
            if view == 'top':
                width, length = dimensions.length * scale, dimensions.width * scale
                
                armrest_width = width * 0.12
                seat_width = width - (2 * armrest_width)
                backrest_depth = length * 0.2
                seat_depth = length - backrest_depth
                corner_radius = 3
                
                # Backrest (thin rectangle at back with rounded top corners)
                dwg.add(dwg.rect((x, y), (width, backrest_depth), 
                               fill='darkgray', stroke='black', stroke_width=2,
                               rx=corner_radius, ry=corner_radius))
                
                # Left armrest (rounded outer corners)
                dwg.add(dwg.rect((x, y + backrest_depth), (armrest_width, seat_depth), 
                               fill='gray', stroke='black', stroke_width=2,
                               rx=corner_radius, ry=corner_radius))
                
                # Seat cushions (rounded cushions for comfort look)
                num_seats = int(features.get('seats', 2) or 2)
                cushion_width = seat_width / num_seats
                for i in range(num_seats):
                    cushion_x = x + armrest_width + (i * cushion_width) + 2
                    dwg.add(dwg.rect((cushion_x, y + backrest_depth + 3), 
                                   (cushion_width - 4, seat_depth - 6), 
                                   fill='lightcoral', stroke='darkred', stroke_width=1,
                                   rx=3, ry=3))
                
                # Right armrest (rounded outer corners)
                dwg.add(dwg.rect((x + width - armrest_width, y + backrest_depth), 
                               (armrest_width, seat_depth), 
                               fill='gray', stroke='black', stroke_width=2,
                               rx=corner_radius, ry=corner_radius))
                
                # Labels
                dwg.add(dwg.text('SOFA', insert=(x + width/2 - 12, y + length/2), 
                               fill='black', font_size='10px', font_weight='bold'))
                    
            else:  # front view
                # Front view: use length (2.0m) as horizontal width
                width, height = dimensions.length * scale, dimensions.height * scale
                
                # Sofa proportions matching top view
                armrest_width_ratio = 0.12
                seat_height_ratio = 0.45
                backrest_height_ratio = 0.55
                armrest_height_ratio = 0.7
                
                # Rounded corner radius - matching 3D geometry (0.03m radius = subtle rounding)
                corner_radius = 3
                
                # Backrest (upper part, narrower than full width, with rounded top corners)
                backrest_width = width * (1 - 2 * armrest_width_ratio)
                backrest_x = x + width * armrest_width_ratio
                backrest_height = height * backrest_height_ratio
                dwg.add(dwg.rect((backrest_x, y), (backrest_width, backrest_height), 
                               fill='darkgray', stroke='black', stroke_width=2,
                               rx=corner_radius, ry=corner_radius))
                
                # Seat (full width, rounded front corners)
                seat_height = height * seat_height_ratio
                dwg.add(dwg.rect((x, y + backrest_height), (width, seat_height), 
                               fill='lightcoral', stroke='darkred', stroke_width=2,
                               rx=3, ry=3))
                
                # Left armrest (rounded corners)
                armrest_height = height * armrest_height_ratio
                dwg.add(dwg.rect((x, y + height - armrest_height), (width * armrest_width_ratio, armrest_height), 
                               fill='gray', stroke='black', stroke_width=2,
                               rx=corner_radius, ry=corner_radius))
                
                # Right armrest (rounded corners)
                dwg.add(dwg.rect((x + width * (1 - armrest_width_ratio), y + height - armrest_height), 
                               (width * armrest_width_ratio, armrest_height), 
                               fill='gray', stroke='black', stroke_width=2,
                               rx=corner_radius, ry=corner_radius))
                
                # Labels
                dwg.add(dwg.text('BACK', insert=(x + width/2 - 12, y + backrest_height/2 + 5), 
                               fill='white', font_size='8px', font_weight='bold'))
                dwg.add(dwg.text('SEAT', insert=(x + width/2 - 12, y + height - seat_height/2 + 5), 
                               fill='black', font_size='8px', font_weight='bold'))
        
        elif furniture_type == 'cabinet':
            # Wardrobe/cabinet with doors
            if view == 'top':
                width, length = dimensions.width * scale, dimensions.length * scale
                
                # Cabinet body
                dwg.add(dwg.rect((x, y), (width, length), 
                               fill='burlywood', stroke='saddlebrown', stroke_width=2))
                
                # Door divisions
                num_doors = int(features.get('doors', 2) or 2)
                door_width = width / num_doors
                for i in range(1, num_doors):
                    door_x = x + (i * door_width)
                    dwg.add(dwg.line((door_x, y), (door_x, y + length), 
                                   stroke='saddlebrown', stroke_width=1, stroke_dasharray='3,3'))
                
                # NO handles in top view (removed yellow circles)
                
                # Label
                dwg.add(dwg.text('CABINET', insert=(x + width/2 - 18, y + length/2), 
                               fill='black', font_size='9px', font_weight='bold'))
                    
            else:  # front view
                width, height = dimensions.width * scale, dimensions.height * scale
                
                # Cabinet body
                dwg.add(dwg.rect((x, y), (width, height), 
                               fill='burlywood', stroke='saddlebrown', stroke_width=3))
                
                # Door divisions
                num_doors = int(features.get('doors', 2) or 2)
                door_width = width / num_doors
                for i in range(1, num_doors):
                    door_x = x + (i * door_width)
                    dwg.add(dwg.line((door_x, y), (door_x, y + height), 
                                   stroke='saddlebrown', stroke_width=2))
                
                # Door handles - positioned at center of each door, pointing inward
                for i in range(num_doors):
                    # Handle on the inner edge of each door (pointing to center)
                    if i < num_doors / 2:
                        # Left door(s) - handle on right side
                        handle_x = x + (i + 1) * door_width - door_width * 0.2
                    else:
                        # Right door(s) - handle on left side
                        handle_x = x + i * door_width + door_width * 0.2
                    
                    handle_y = y + height / 2
                    dwg.add(dwg.rect((handle_x - 2, handle_y - 8), (4, 16), 
                                   fill='gold', stroke='black', stroke_width=1))
                
                # Legs (4 small legs at bottom)
                leg_height = 8
                for i in [0.15, 0.85]:
                    for j in range(num_doors):
                        leg_x = x + (j * door_width) + door_width * i
                        dwg.add(dwg.rect((leg_x - 3, y + height), (6, leg_height), 
                                       fill='saddlebrown', stroke='black'))
        
        else:  # generic furniture
            if view == 'top':
                width, length = dimensions.width * scale, dimensions.length * scale
                dwg.add(dwg.rect((x, y), (width, length), 
                               fill='lightgray', stroke='gray', stroke_width=2))
                    
            else:  # front view
                width, height = dimensions.width * scale, dimensions.height * scale
                dwg.add(dwg.rect((x, y), (width, height), 
                               fill='lightgray', stroke='gray', stroke_width=2))
    
    def _draw_house_top_view_dxf(self, msp, dimensions, features, scale, offset_x, offset_y):
        """Draw house top view in DXF"""
        width = dimensions.width * scale
        length = dimensions.length * scale
        
        # House outline
        msp.add_lwpolyline([
            (offset_x, offset_y), (offset_x + width, offset_y),
            (offset_x + width, offset_y + length), (offset_x, offset_y + length), (offset_x, offset_y)
        ], dxfattribs={'layer': 'TOP_VIEW'})
        
        # Room divisions
        msp.add_line((offset_x + width/3, offset_y), (offset_x + width/3, offset_y + length), dxfattribs={'layer': 'TOP_VIEW'})
        msp.add_line((offset_x, offset_y + length/2), (offset_x + width, offset_y + length/2), dxfattribs={'layer': 'TOP_VIEW'})
        
        # Main entrance
        door_width = 30
        door_x = offset_x + width/2 - door_width/2
        msp.add_line((door_x, offset_y), (door_x + door_width, offset_y), dxfattribs={'layer': 'FRONT_VIEW', 'color': 6})
    
    def _draw_house_front_view_dxf(self, msp, dimensions, features, scale, offset_x, offset_y):
        """Draw house front view in DXF"""
        width = dimensions.width * scale
        height = dimensions.height * scale
        
        # House outline
        msp.add_lwpolyline([
            (offset_x, offset_y), (offset_x + width, offset_y),
            (offset_x + width, offset_y + height), (offset_x, offset_y + height), (offset_x, offset_y)
        ], dxfattribs={'layer': 'FRONT_VIEW'})
        
        # Roof triangle
        roof_height = 30
        msp.add_lwpolyline([
            (offset_x, offset_y), (offset_x + width/2, offset_y - roof_height), (offset_x + width, offset_y)
        ], dxfattribs={'layer': 'FRONT_VIEW'})
        
        # Windows
        window_width, window_height = 40, 30
        # Left window
        msp.add_lwpolyline([
            (offset_x + width/4 - window_width/2, offset_y + height/3),
            (offset_x + width/4 + window_width/2, offset_y + height/3),
            (offset_x + width/4 + window_width/2, offset_y + height/3 + window_height),
            (offset_x + width/4 - window_width/2, offset_y + height/3 + window_height),
            (offset_x + width/4 - window_width/2, offset_y + height/3)
        ], dxfattribs={'layer': 'FRONT_VIEW', 'color': 5})
        
        # Right window
        msp.add_lwpolyline([
            (offset_x + 3*width/4 - window_width/2, offset_y + height/3),
            (offset_x + 3*width/4 + window_width/2, offset_y + height/3),
            (offset_x + 3*width/4 + window_width/2, offset_y + height/3 + window_height),
            (offset_x + 3*width/4 - window_width/2, offset_y + height/3 + window_height),
            (offset_x + 3*width/4 - window_width/2, offset_y + height/3)
        ], dxfattribs={'layer': 'FRONT_VIEW', 'color': 5})
        
        # Main door
        door_width, door_height = 25, 50
        msp.add_lwpolyline([
            (offset_x + width/2 - door_width/2, offset_y + height),
            (offset_x + width/2 + door_width/2, offset_y + height),
            (offset_x + width/2 + door_width/2, offset_y + height - door_height),
            (offset_x + width/2 - door_width/2, offset_y + height - door_height),
            (offset_x + width/2 - door_width/2, offset_y + height)
        ], dxfattribs={'layer': 'FRONT_VIEW', 'color': 6})
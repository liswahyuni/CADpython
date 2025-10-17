from typing import List, Tuple
from text_parser import ParsedObject
import ezdxf
import svgwrite


class CADGenerator:
    def __init__(self):
        self.scale = 2.0  # Better scale for visibility
        self.margin = 100  # More margin for better spacing

    def generate_dxf(self, parsed_obj: ParsedObject, filename: str) -> None:
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        top_view_points = self._generate_top_view(parsed_obj)
        front_view_points = self._generate_front_view(parsed_obj)
        
        offset_x = parsed_obj.dimensions.width * self.scale + self.margin * 2
        
        self._draw_view_dxf(msp, top_view_points, self.margin, self.margin, "TOP VIEW")
        self._draw_view_dxf(msp, front_view_points, offset_x, self.margin, "FRONT VIEW")
        
        # Add dimensions
        self._add_dimensions_dxf(msp, parsed_obj, self.margin, self.margin, "top")
        self._add_dimensions_dxf(msp, parsed_obj, offset_x, self.margin, "front")
        
        doc.saveas(filename)

    def generate_svg(self, parsed_obj: ParsedObject, filename: str) -> None:
        width = (parsed_obj.dimensions.width + parsed_obj.dimensions.length) * self.scale + self.margin * 4 + 100  # Extra space for dimensions
        height = max(parsed_obj.dimensions.height, max(parsed_obj.dimensions.width, parsed_obj.dimensions.length)) * self.scale + self.margin * 3 + 80  # Extra space for dimensions
        
        dwg = svgwrite.Drawing(filename, size=(f"{width}px", f"{height}px"))
        
        top_view_points = self._generate_top_view(parsed_obj)
        front_view_points = self._generate_front_view(parsed_obj)
        
        offset_x = parsed_obj.dimensions.width * self.scale + self.margin * 2
        
        self._draw_view_svg(dwg, top_view_points, self.margin, self.margin, "TOP VIEW")
        self._draw_view_svg(dwg, front_view_points, offset_x, self.margin, "FRONT VIEW")
        
        # Add dimensions
        self._add_dimensions_svg(dwg, parsed_obj, self.margin, self.margin, "top")
        self._add_dimensions_svg(dwg, parsed_obj, offset_x, self.margin, "front")
        
        dwg.save()

    def _generate_top_view(self, parsed_obj: ParsedObject) -> List[Tuple[float, float]]:
        points = []
        width = parsed_obj.dimensions.width * self.scale
        length = parsed_obj.dimensions.length * self.scale
        
        # Main outline
        points.extend([
            (0, 0), (width, 0), (width, length), (0, length), (0, 0)
        ])
        
        # Add features based on object type
        if parsed_obj.object_type == "kursi":
            # Add chair legs at the corners (more realistic positioning)
            leg_size = 6 * self.scale  # Leg size
            corner_margin = 3 * self.scale  # Small margin from absolute corners
            leg_positions = [
                (corner_margin, corner_margin),  # Top-left corner
                (width - corner_margin - leg_size, corner_margin),  # Top-right corner
                (width - corner_margin - leg_size, length - corner_margin - leg_size),  # Bottom-right corner
                (corner_margin, length - corner_margin - leg_size)  # Bottom-left corner
            ]
            
            kaki_count = len([f for f in parsed_obj.features if f.name == "kaki"])
            for i, (x, y) in enumerate(leg_positions):
                if i < kaki_count:
                    # Start a new path for each leg
                    points.extend([None])  # Path separator
                    points.extend([
                        (x, y),
                        (x + leg_size, y),
                        (x + leg_size, y + leg_size),
                        (x, y + leg_size),
                        (x, y)
                    ])
                    
        elif parsed_obj.object_type == "meja":
            # Add table legs at the corners
            leg_size = 4 * self.scale  # Table leg size (smaller than chair legs)
            corner_margin = 5 * self.scale  # Margin from corners
            leg_positions = [
                (corner_margin, corner_margin),  # Top-left corner
                (width - corner_margin - leg_size, corner_margin),  # Top-right corner
                (width - corner_margin - leg_size, length - corner_margin - leg_size),  # Bottom-right corner
                (corner_margin, length - corner_margin - leg_size)  # Bottom-left corner
            ]
            
            # Always draw 4 table legs
            for x, y in leg_positions:
                # Start a new path for each leg
                points.extend([None])  # Path separator
                points.extend([
                    (x, y),
                    (x + leg_size, y),
                    (x + leg_size, y + leg_size),
                    (x, y + leg_size),
                    (x, y)
                ])
                    
        elif parsed_obj.object_type == "ruangan":
            # Add doors and windows as openings in walls
            for feature in parsed_obj.features:
                if feature.name == "pintu":
                    door_width = 20 * self.scale
                    if "barat" in feature.position or "west" in feature.position:
                        # Break in left wall
                        points.extend([None, (0, length/2 - door_width/2), (0, length/2 + door_width/2)])
                    elif "timur" in feature.position or "east" in feature.position:
                        # Break in right wall
                        points.extend([None, (width, length/2 - door_width/2), (width, length/2 + door_width/2)])
                    elif "utara" in feature.position or "north" in feature.position:
                        # Break in top wall
                        points.extend([None, (width/2 - door_width/2, length), (width/2 + door_width/2, length)])
                    else:
                        # Break in bottom wall
                        points.extend([None, (width/2 - door_width/2, 0), (width/2 + door_width/2, 0)])
                        
                elif feature.name == "jendela":
                    window_width = 15 * self.scale
                    if "utara" in feature.position or "north" in feature.position:
                        points.extend([None, (width/2 - window_width/2, length), (width/2 + window_width/2, length)])
                    elif "selatan" in feature.position or "south" in feature.position:
                        points.extend([None, (width/2 - window_width/2, 0), (width/2 + window_width/2, 0)])
                    elif "barat" in feature.position or "west" in feature.position:
                        points.extend([None, (0, length/2 - window_width/2), (0, length/2 + window_width/2)])
                    else:
                        points.extend([None, (width, length/2 - window_width/2), (width, length/2 + window_width/2)])
            
        return points

    def _generate_front_view(self, parsed_obj: ParsedObject) -> List[Tuple[float, float]]:
        points = []
        width = parsed_obj.dimensions.width * self.scale
        height = parsed_obj.dimensions.height * self.scale
        
        if parsed_obj.object_type == "kursi":
            seat_height = height * 0.4  # Seat at 40% from bottom (60% from top)
            seat_thickness = 6.0 * self.scale
            
            # Draw seat (horizontal surface) - measured from BOTTOM
            points.extend([
                (0, height - seat_height - seat_thickness), (width, height - seat_height - seat_thickness), 
                (width, height - seat_height), (0, height - seat_height), (0, height - seat_height - seat_thickness)
            ])
            
            # Draw backrest (at the BACK of chair) - goes UP from seat
            back_width = 6.0 * self.scale
            points.extend([None])  # Path separator
            points.extend([
                (width - back_width, height - seat_height), (width, height - seat_height), 
                (width, 0), (width - back_width, 0), (width - back_width, height - seat_height)
            ])
            
            # Draw legs - from BOTTOM (height) to seat level
            leg_width = 8.0 * self.scale
            kaki_count = len([f for f in parsed_obj.features if f.name == "kaki"])
            
            if kaki_count >= 2:
                # Left front leg (from bottom to seat)
                points.extend([None])
                points.extend([
                    (0, height), (leg_width, height), 
                    (leg_width, height - seat_height), (0, height - seat_height), (0, height)
                ])
                
                # Right front leg (from bottom to seat)
                points.extend([None])
                points.extend([
                    (width - leg_width, height), (width, height), 
                    (width, height - seat_height), (width - leg_width, height - seat_height), (width - leg_width, height)
                ])
                    
        elif parsed_obj.object_type == "meja":
            # Draw table top
            table_top_thickness = 4.0 * self.scale
            table_top_height = height * 0.9  # Table top near the top
            
            points.extend([
                (0, height - table_top_height - table_top_thickness), (width, height - table_top_height - table_top_thickness), 
                (width, height - table_top_height), (0, height - table_top_height), (0, height - table_top_height - table_top_thickness)
            ])
            
            # Draw table legs - from bottom to table top
            leg_width = 6.0 * self.scale
            
            # Left leg
            points.extend([None])
            points.extend([
                (leg_width, height), (leg_width * 2, height), 
                (leg_width * 2, height - table_top_height), (leg_width, height - table_top_height), (leg_width, height)
            ])
            
            # Right leg  
            points.extend([None])
            points.extend([
                (width - leg_width * 2, height), (width - leg_width, height), 
                (width - leg_width, height - table_top_height), (width - leg_width * 2, height - table_top_height), (width - leg_width * 2, height)
            ])
                    
        elif parsed_obj.object_type == "ruangan":
            # Draw room walls
            points.extend([
                (0, 0), (width, 0), (width, height), (0, height), (0, 0)
            ])
            
            # Add doors and windows
            for feature in parsed_obj.features:
                if feature.name == "pintu":
                    door_width = 20 * self.scale
                    door_height = height * 0.8
                    x_pos = width/2 - door_width/2
                    points.extend([None])  # Path separator
                    points.extend([
                        (x_pos, 0), (x_pos + door_width, 0), 
                        (x_pos + door_width, door_height), (x_pos, door_height), (x_pos, 0)
                    ])
                    
                elif feature.name == "jendela":
                    window_width = 15 * self.scale
                    window_height = height * 0.4
                    window_y = height * 0.3
                    x_pos = width/2 - window_width/2
                    points.extend([None])  # Path separator
                    points.extend([
                        (x_pos, window_y), (x_pos + window_width, window_y), 
                        (x_pos + window_width, window_y + window_height), 
                        (x_pos, window_y + window_height), (x_pos, window_y)
                    ])
        else:
            # Generic box shape
            points.extend([
                (0, 0), (width, 0), (width, height), (0, height), (0, 0)
            ])
            
        return points

    def _draw_view_dxf(self, msp, points: List[Tuple[float, float]], offset_x: float, offset_y: float, title: str) -> None:
        if not points:
            return
        
        # Split points by None separators into individual paths
        paths = []
        current_path = []
        
        for point in points:
            if point is None:
                if current_path:
                    paths.append(current_path)
                    current_path = []
            else:
                current_path.append(point)
        
        if current_path:
            paths.append(current_path)
        
        # Draw each path
        for path in paths:
            for i in range(len(path) - 1):
                start = (path[i][0] + offset_x, path[i][1] + offset_y)
                end = (path[i+1][0] + offset_x, path[i+1][1] + offset_y)
                msp.add_line(start, end)
        
        msp.add_text(title, dxfattribs={'height': 8}).set_placement((offset_x, offset_y - 20))

    def _draw_view_svg(self, dwg, points: List[Tuple[float, float]], offset_x: float, offset_y: float, title: str) -> None:
        if not points:
            return
        
        # Split points by None separators into individual paths
        paths = []
        current_path = []
        
        for point in points:
            if point is None:
                if current_path:
                    paths.append(current_path)
                    current_path = []
            else:
                current_path.append(point)
        
        if current_path:
            paths.append(current_path)
        
        # Draw each path
        for path in paths:
            if len(path) >= 2:
                path_data = f"M {path[0][0] + offset_x} {path[0][1] + offset_y}"
                for point in path[1:]:
                    path_data += f" L {point[0] + offset_x} {point[1] + offset_y}"
                
                dwg.add(dwg.path(d=path_data, stroke='#4A90E2', fill='none', stroke_width=2))
        
        dwg.add(dwg.text(title, insert=(offset_x, offset_y - 20), 
                        font_size="14px", font_family="Arial", font_weight="bold", 
                        fill='white'))

    def _add_dimensions_svg(self, dwg, parsed_obj: ParsedObject, offset_x: float, offset_y: float, view_type: str) -> None:
        width = parsed_obj.dimensions.width * self.scale
        length = parsed_obj.dimensions.length * self.scale
        height = parsed_obj.dimensions.height * self.scale
        
        if view_type == "top":
            # Width dimension (horizontal)
            dwg.add(dwg.line(start=(offset_x, offset_y + length + 20), 
                           end=(offset_x + width, offset_y + length + 20), 
                           stroke='#00D9FF', stroke_width=1))
            dwg.add(dwg.text(f"{parsed_obj.dimensions.width} cm", 
                           insert=(offset_x + width/2, offset_y + length + 35), 
                           text_anchor="middle", font_size="10px", fill="#00D9FF"))
            
            # Length dimension (vertical)
            dwg.add(dwg.line(start=(offset_x + width + 20, offset_y), 
                           end=(offset_x + width + 20, offset_y + length), 
                           stroke='#00D9FF', stroke_width=1))
            dwg.add(dwg.text(f"{parsed_obj.dimensions.length} cm", 
                           insert=(offset_x + width + 35, offset_y + length/2), 
                           text_anchor="middle", font_size="10px", fill="#00D9FF", 
                           transform=f"rotate(-90, {offset_x + width + 35}, {offset_y + length/2})"))
                           
        elif view_type == "front":
            # Width dimension (horizontal)
            dwg.add(dwg.line(start=(offset_x, offset_y + height + 20), 
                           end=(offset_x + width, offset_y + height + 20), 
                           stroke='#00D9FF', stroke_width=1))
            dwg.add(dwg.text(f"{parsed_obj.dimensions.width} cm", 
                           insert=(offset_x + width/2, offset_y + height + 35), 
                           text_anchor="middle", font_size="10px", fill="#00D9FF"))
            
            # Height dimension (vertical)
            dwg.add(dwg.line(start=(offset_x + width + 20, offset_y), 
                           end=(offset_x + width + 20, offset_y + height), 
                           stroke='#00D9FF', stroke_width=1))
            dwg.add(dwg.text(f"{parsed_obj.dimensions.height} cm", 
                           insert=(offset_x + width + 35, offset_y + height/2), 
                           text_anchor="middle", font_size="10px", fill="#00D9FF",
                           transform=f"rotate(-90, {offset_x + width + 35}, {offset_y + height/2})"))

    def _add_dimensions_dxf(self, msp, parsed_obj: ParsedObject, offset_x: float, offset_y: float, view_type: str) -> None:
        width = parsed_obj.dimensions.width * self.scale
        length = parsed_obj.dimensions.length * self.scale
        height = parsed_obj.dimensions.height * self.scale
        
        if view_type == "top":
            # Width dimension
            msp.add_line((offset_x, offset_y + length + 20), (offset_x + width, offset_y + length + 20))
            msp.add_text(f"{parsed_obj.dimensions.width} cm", dxfattribs={'height': 6, 'color': 1}).set_placement((offset_x + width/2, offset_y + length + 25))
            
            # Length dimension
            msp.add_line((offset_x + width + 20, offset_y), (offset_x + width + 20, offset_y + length))
            msp.add_text(f"{parsed_obj.dimensions.length} cm", dxfattribs={'height': 6, 'color': 1, 'rotation': 90}).set_placement((offset_x + width + 25, offset_y + length/2))
                           
        elif view_type == "front":
            # Width dimension
            msp.add_line((offset_x, offset_y + height + 20), (offset_x + width, offset_y + height + 20))
            msp.add_text(f"{parsed_obj.dimensions.width} cm", dxfattribs={'height': 6, 'color': 1}).set_placement((offset_x + width/2, offset_y + height + 25))
            
            # Height dimension
            msp.add_line((offset_x + width + 20, offset_y), (offset_x + width + 20, offset_y + height))
            msp.add_text(f"{parsed_obj.dimensions.height} cm", dxfattribs={'height': 6, 'color': 1, 'rotation': 90}).set_placement((offset_x + width + 25, offset_y + height/2))
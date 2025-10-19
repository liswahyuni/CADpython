"""
3D Extruder for generating STL and OBJ files
"""

import trimesh
import math
import numpy as np
from pdf_rag import ParsedObject


class Extruder3D:
    """Generate 3D files from parsed objects"""
    
    def __init__(self):
        pass
    
    def generate_stl(self, parsed_obj: ParsedObject, filename: str) -> None:
        """Generate STL file"""
        mesh = self._create_mesh(parsed_obj)
        mesh.export(filename)
    
    def generate_obj_with_mtl(self, parsed_obj: ParsedObject, filename: str) -> None:
        """Generate OBJ file with MTL material"""
        mesh = self._create_mesh(parsed_obj)
        
        # Create material
        material_name = f"{parsed_obj.object_type}_material"
        material = self._create_material(parsed_obj)
        
        # Export with material
        try:
            if hasattr(mesh.visual, 'material'):
                mesh.visual.material.name = material_name
        except Exception:
            # Create material visual if not exists
            mesh.visual = trimesh.visual.create_visual(material_name=material_name)
        
        mesh.export(filename)
        
        # Create MTL file
        mtl_filename = filename.replace('.obj', '.mtl')
        self._create_mtl_file(mtl_filename, material_name, material)
    
    def _create_mesh(self, parsed_obj: ParsedObject) -> trimesh.Trimesh:
        """Create realistic 3D furniture mesh"""
        width = parsed_obj.dimensions.width
        length = parsed_obj.dimensions.length  
        height = parsed_obj.dimensions.height
        
        # Get features if available
        features = getattr(parsed_obj, 'features', {})
        
        # Create objects based on type
        if parsed_obj.object_type == "lingkaran":
            return self._create_circular_mesh(width, length, height, parsed_obj.diameter)
        elif parsed_obj.object_type == "kursi":
            return self._create_chair_mesh(width, length, height)
        elif parsed_obj.object_type == "meja":
            return self._create_table_mesh(width, length, height, features)
        elif parsed_obj.object_type == "lemari":
            return self._create_cabinet_mesh(width, length, height, features)
        elif parsed_obj.object_type == "sofa":
            return self._create_sofa_mesh(width, length, height, features)
        elif parsed_obj.object_type == "ruangan":
            return self._create_room_mesh(width, length, height)
        elif parsed_obj.object_type == "rumah":
            return self._create_house_mesh(width, length, height, features)
        else:
            # Fallback to simple box
            return trimesh.creation.box(extents=[width, length, height])
    
    def _create_chair_mesh(self, width: float, length: float, height: float, features: dict = None) -> trimesh.Trimesh:
        """Create a simple chair mesh - NO BACKREST (matching 2D)"""
        if features is None:
            features = {}
            
        meshes = []
        
        # Seat only (no backrest)
        seat_height = height * 0.45
        seat_thickness = 0.05
        seat = trimesh.creation.box(
            extents=[width, length, seat_thickness],
            transform=trimesh.transformations.translation_matrix([0, 0, seat_height])
        )
        meshes.append(seat)
        
        # 4 legs
        leg_thickness = 0.04
        leg_positions = [
            [width/2 - 0.05, length/2 - 0.05, seat_height/2],
            [-width/2 + 0.05, length/2 - 0.05, seat_height/2],
            [-width/2 + 0.05, -length/2 + 0.05, seat_height/2],
            [width/2 - 0.05, -length/2 + 0.05, seat_height/2]
        ]
        
        for pos in leg_positions:
            leg = trimesh.creation.box(
                extents=[leg_thickness, leg_thickness, seat_height],
                transform=trimesh.transformations.translation_matrix(pos)
            )
            meshes.append(leg)
        
        return trimesh.util.concatenate(meshes)
    
    def _create_table_mesh(self, width: float, length: float, height: float, features: dict = None) -> trimesh.Trimesh:
        """Create realistic table mesh - circular or rectangular"""
        if features is None:
            features = {}
        
        is_circular = features.get('seat_shape') == 'circular'
        top_thickness = 0.05
        leg_thickness = 0.06
        
        if is_circular:
            radius = width / 2
            top = trimesh.creation.cylinder(radius=radius, height=top_thickness)
            top.apply_translation([0, 0, height - top_thickness/2])
            
            leg_height = height - top_thickness
            legs = []
            num_legs = features.get('legs', 4)
            leg_radius_from_center = radius * 0.7
            
            for i in range(num_legs):
                angle = (2 * math.pi * i / num_legs) - (math.pi / 2)
                leg_x = leg_radius_from_center * math.cos(angle)
                leg_y = leg_radius_from_center * math.sin(angle)
                
                leg = trimesh.creation.cylinder(radius=leg_thickness/2, height=leg_height)
                leg.apply_translation([leg_x, leg_y, leg_height/2])
                legs.append(leg)
            
            return trimesh.util.concatenate([top] + legs)
        else:
            # Rectangular table top
            top = trimesh.creation.box(extents=[width, length, top_thickness])
            top.apply_translation([0, 0, height - top_thickness/2])
            
            # Four legs at corners
            leg_height = height - top_thickness
            legs = []
            positions = [
                [-width/2 + leg_thickness/2, -length/2 + leg_thickness/2],
                [width/2 - leg_thickness/2, -length/2 + leg_thickness/2],
                [-width/2 + leg_thickness/2, length/2 - leg_thickness/2],
                [width/2 - leg_thickness/2, length/2 - leg_thickness/2]
            ]
            
            for x, y in positions:
                leg = trimesh.creation.box(extents=[leg_thickness, leg_thickness, leg_height])
                leg.apply_translation([x, y, leg_height/2])
                legs.append(leg)
            
            return trimesh.util.concatenate([top] + legs)
    
    def _create_cabinet_mesh(self, width: float, length: float, height: float, features: dict = None) -> trimesh.Trimesh:
        """Create realistic cabinet/wardrobe mesh with doors and handles"""
        if features is None:
            features = {}
        
        wall_thickness = 0.02
        num_doors = features.get('doors', 2)
        
        meshes = []
        
        # Back wall
        back = trimesh.creation.box(extents=[width, wall_thickness, height])
        back.apply_translation([0, length/2 - wall_thickness/2, 0])
        meshes.append(back)
        
        # Left wall
        left = trimesh.creation.box(extents=[wall_thickness, length, height])
        left.apply_translation([-width/2 + wall_thickness/2, 0, 0])
        meshes.append(left)
        
        # Right wall
        right = trimesh.creation.box(extents=[wall_thickness, length, height])
        right.apply_translation([width/2 - wall_thickness/2, 0, 0])
        meshes.append(right)
        
        # Top
        top = trimesh.creation.box(extents=[width, length, wall_thickness])
        top.apply_translation([0, 0, height/2 - wall_thickness/2])
        meshes.append(top)
        
        # Bottom
        bottom = trimesh.creation.box(extents=[width, length, wall_thickness])
        bottom.apply_translation([0, 0, -height/2 + wall_thickness/2])
        meshes.append(bottom)
        
        # Doors (at front)
        door_thickness = 0.015
        door_width = width / num_doors
        door_height = height - 0.1
        
        for i in range(num_doors):
            door_x = -width/2 + door_width/2 + i * door_width
            door = trimesh.creation.box(extents=[door_width - 0.01, door_thickness, door_height])
            door.apply_translation([door_x, -length/2 + door_thickness/2, 0])
            meshes.append(door)
            
            # Door handle (small cylinder)
            handle_radius = 0.01
            handle_height = 0.08
            # Left doors: handle on right side, Right doors: handle on left side
            if i < num_doors / 2:
                # Left door - handle on right
                handle_x = door_x + door_width/2 - 0.05
            else:
                handle_x = door_x - door_width/2 + 0.05
            
            handle = trimesh.creation.cylinder(radius=handle_radius, height=handle_height)
            rotation_matrix = trimesh.transformations.rotation_matrix(np.pi/2, [1, 0, 0])
            handle.apply_transform(rotation_matrix)
            handle.apply_translation([handle_x, -length/2 - 0.02, 0])
            meshes.append(handle)
        
        # Legs (4 small legs at bottom corners)
        leg_radius = 0.015
        leg_height = 0.05
        leg_positions = [
            [-width/2 + 0.05, -length/2 + 0.05],
            [width/2 - 0.05, -length/2 + 0.05],
            [-width/2 + 0.05, length/2 - 0.05],
            [width/2 - 0.05, length/2 - 0.05]
        ]
        
        for x, y in leg_positions:
            leg = trimesh.creation.cylinder(radius=leg_radius, height=leg_height)
            leg.apply_translation([x, y, -height/2 - leg_height/2])
            meshes.append(leg)
        
        return trimesh.util.concatenate(meshes)
    
    def _create_sofa_mesh(self, width: float, length: float, height: float, features: dict = None) -> trimesh.Trimesh:
        """Create a realistic sofa with backrest, armrests, and seat cushions"""
        if features is None:
            features = {}
        num_seats = int(features.get('seats', 2) or 2)
        
        # Sofa orientation: length horizontal, width depth
        sofa_width = length
        sofa_depth = width
        
        # Sofa proportions (realistic)
        seat_height = height * 0.45
        backrest_height = height * 0.55
        armrest_height = height * 0.45
        backrest_thickness = sofa_depth * 0.2
        armrest_width = sofa_width * 0.12
        
        meshes = []
        
        # Base/Seat (wide, low platform)
        seat_mesh = self._create_rounded_box([sofa_width, sofa_depth, seat_height])
        seat_mesh.apply_translation([0, 0, seat_height/2])
        meshes.append(seat_mesh)
        
        # Backrest (thin wall at back)
        backrest_mesh = self._create_rounded_box([sofa_width, backrest_thickness, backrest_height])
        backrest_mesh.apply_translation([0, -sofa_depth/2 + backrest_thickness/2, seat_height + backrest_height/2])
        meshes.append(backrest_mesh)
        
        # Left armrest
        left_armrest = self._create_rounded_box([armrest_width, sofa_depth - backrest_thickness, armrest_height])
        left_armrest.apply_translation([-sofa_width/2 + armrest_width/2, backrest_thickness/2, seat_height + armrest_height/2])
        meshes.append(left_armrest)
        
        # Right armrest
        right_armrest = self._create_rounded_box([armrest_width, sofa_depth - backrest_thickness, armrest_height])
        right_armrest.apply_translation([sofa_width/2 - armrest_width/2, backrest_thickness/2, seat_height + armrest_height/2])
        meshes.append(right_armrest)
        
        # Seat cushions (individual cushions between armrests)
        cushion_width = (sofa_width - 2 * armrest_width) / num_seats
        cushion_depth = sofa_depth - backrest_thickness
        cushion_height = seat_height * 0.15
        
        for i in range(num_seats):
            cushion_x = -sofa_width/2 + armrest_width + cushion_width/2 + i * cushion_width
            cushion_mesh = self._create_rounded_box([cushion_width * 0.95, cushion_depth * 0.95, cushion_height])
            cushion_mesh.apply_translation([cushion_x, backrest_thickness/2, seat_height + cushion_height/2])
            meshes.append(cushion_mesh)
        
        return trimesh.util.concatenate(meshes)
    
    def _create_rounded_box(self, extents, radius=0.01):
        """Create box with subtle rounded edges"""
        box = trimesh.creation.box(extents=extents)
        subdivided = box.subdivide()
        smoothed = trimesh.smoothing.filter_laplacian(subdivided, iterations=1, lamb=0.2)
        return smoothed
    
    def _create_circular_mesh(self, width: float, length: float, height: float, diameter: float = None) -> trimesh.Trimesh:
        """Create circular/cylindrical mesh"""
        if diameter:
            radius = diameter / 2
        else:
            radius = min(width, length) / 2
        
        # Create cylinder
        return trimesh.creation.cylinder(radius=radius, height=height)
    
    def _create_room_mesh(self, width: float, length: float, height: float, features: dict = None) -> trimesh.Trimesh:
        """Create room with walls, door and window clearly visible (NO ventilation above door)"""
        if features is None:
            features = {}
            
        wall_thickness = 0.2
        
        # Create individual walls instead of hollow box for better door/window visibility
        meshes = []
        
        # Floor
        floor = trimesh.creation.box(extents=[width + 2*wall_thickness, length + 2*wall_thickness, 0.1])
        floor.apply_translation([0, 0, -height/2])
        meshes.append(floor)
        
        # Ceiling
        ceiling = trimesh.creation.box(extents=[width + 2*wall_thickness, length + 2*wall_thickness, 0.1])
        ceiling.apply_translation([0, 0, height/2 - 0.05])
        meshes.append(ceiling)
        
        # East wall (full)
        east_wall = trimesh.creation.box(extents=[wall_thickness, length, height])
        east_wall.apply_translation([width/2 + wall_thickness/2, 0, 0])
        meshes.append(east_wall)
        
        # South wall (full)
        south_wall = trimesh.creation.box(extents=[width, wall_thickness, height])
        south_wall.apply_translation([0, -length/2 - wall_thickness/2, 0])
        meshes.append(south_wall)
        
        # West wall with door opening (realistic door height - 2.0m)
        door_width = 0.8
        door_height = 2.0  # Standard door height
        
        # West wall parts (beside and ABOVE door)
        # Wall left of door
        wall_left = trimesh.creation.box(extents=[wall_thickness, (length - door_width)/2, height])
        wall_left.apply_translation([-width/2 - wall_thickness/2, -length/4 - door_width/4, 0])
        meshes.append(wall_left)
        
        # Wall right of door
        wall_right = trimesh.creation.box(extents=[wall_thickness, (length - door_width)/2, height])
        wall_right.apply_translation([-width/2 - wall_thickness/2, length/4 + door_width/4, 0])
        meshes.append(wall_right)
        
        # Wall ABOVE door (from top of door to ceiling)
        wall_above_door_height = height - door_height
        if wall_above_door_height > 0:
            wall_above_door = trimesh.creation.box(extents=[wall_thickness, door_width, wall_above_door_height])
            wall_above_door.apply_translation([-width/2 - wall_thickness/2, 0, height/2 - wall_above_door_height/2])
            meshes.append(wall_above_door)
        
        # Door frame
        door_frame_thickness = 0.05
        # Door frame top (at door height, not ceiling)
        door_frame_top = trimesh.creation.box(extents=[door_frame_thickness, door_width + 0.1, 0.1])
        door_frame_top.apply_translation([-width/2 - wall_thickness/2, 0, -height/2 + door_height])
        meshes.append(door_frame_top)
        
        # Door frame sides (door height only)
        door_frame_left = trimesh.creation.box(extents=[door_frame_thickness, 0.05, door_height])
        door_frame_left.apply_translation([-width/2 - wall_thickness/2, -door_width/2, -height/2 + door_height/2])
        meshes.append(door_frame_left)
        
        door_frame_right = trimesh.creation.box(extents=[door_frame_thickness, 0.05, door_height])
        door_frame_right.apply_translation([-width/2 - wall_thickness/2, door_width/2, -height/2 + door_height/2])
        meshes.append(door_frame_right)
        
        # North wall with window opening
        window_width = 1.2
        window_height = 1.0
        window_from_floor = 1.0
        
        # North wall parts (beside and above/below window)
        # Wall left of window
        wall_left_window = trimesh.creation.box(extents=[(width - window_width)/2, wall_thickness, height])
        wall_left_window.apply_translation([-(width + window_width)/4, length/2 + wall_thickness/2, 0])
        meshes.append(wall_left_window)
        
        # Wall right of window
        wall_right_window = trimesh.creation.box(extents=[(width - window_width)/2, wall_thickness, height])
        wall_right_window.apply_translation([(width + window_width)/4, length/2 + wall_thickness/2, 0])
        meshes.append(wall_right_window)
        
        # Wall below window
        wall_below_window = trimesh.creation.box(extents=[window_width, wall_thickness, window_from_floor])
        wall_below_window.apply_translation([0, length/2 + wall_thickness/2, -height/2 + window_from_floor/2])
        meshes.append(wall_below_window)
        
        # Wall above window
        wall_above_window_height = height - window_from_floor - window_height
        if wall_above_window_height > 0:
            wall_above_window = trimesh.creation.box(extents=[window_width, wall_thickness, wall_above_window_height])
            wall_above_window.apply_translation([0, length/2 + wall_thickness/2, height/2 - wall_above_window_height/2])
            meshes.append(wall_above_window)
        
        # Window frame
        window_frame_thickness = 0.03
        # Window frame - vertical parts
        window_frame_left = trimesh.creation.box(extents=[0.05, window_frame_thickness, window_height])
        window_frame_left.apply_translation([-window_width/2, length/2 + wall_thickness/2, window_from_floor + window_height/2 - height/2])
        meshes.append(window_frame_left)
        
        window_frame_right = trimesh.creation.box(extents=[0.05, window_frame_thickness, window_height])
        window_frame_right.apply_translation([window_width/2, length/2 + wall_thickness/2, window_from_floor + window_height/2 - height/2])
        meshes.append(window_frame_right)
        
        # Window frame - horizontal parts
        window_frame_top = trimesh.creation.box(extents=[window_width, window_frame_thickness, 0.05])
        window_frame_top.apply_translation([0, length/2 + wall_thickness/2, window_from_floor + window_height - height/2])
        meshes.append(window_frame_top)
        
        window_frame_bottom = trimesh.creation.box(extents=[window_width, window_frame_thickness, 0.05])
        window_frame_bottom.apply_translation([0, length/2 + wall_thickness/2, window_from_floor - height/2])
        meshes.append(window_frame_bottom)
        
        # Combine all meshes
        return trimesh.util.concatenate(meshes)
    
    def _create_house_mesh(self, width: float, length: float, height: float, features: dict = None) -> trimesh.Trimesh:
        """Create modern house with garage and flat roof (matching 2D)"""
        if features is None:
            features = {}
        
        wall_thickness = 0.3
        has_garage = features.get('has_garage', False)
        is_modern = features.get('style') == 'modern'
        
        meshes = []
        
        # Main house dimensions (75% if has garage)
        main_width = width * 0.75 if has_garage else width
        
        # Main house walls (hollow box)
        outer = trimesh.creation.box(extents=[main_width, length, height])
        inner = trimesh.creation.box(extents=[main_width - 2*wall_thickness, length - 2*wall_thickness, height - wall_thickness])
        inner.apply_translation([0, 0, wall_thickness/2])
        
        try:
            house_body = outer.difference(inner)
            # Center the main house on left side if has garage
            if has_garage:
                house_body.apply_translation([-(width - main_width)/2, 0, 0])
        except Exception:
            house_body = outer
            if has_garage:
                house_body.apply_translation([-(width - main_width)/2, 0, 0])
        
        meshes.append(house_body)
        
        # Garage (25% width, 50% length) - positioned at BACK/SOUTH side (same as 2D)
        if has_garage:
            garage_width = width * 0.25
            garage_length = length * 0.5
            garage_outer = trimesh.creation.box(extents=[garage_width, garage_length, height * 0.7])
            garage_inner = trimesh.creation.box(extents=[garage_width - 2*wall_thickness, garage_length - 2*wall_thickness, height * 0.7 - wall_thickness])
            garage_inner.apply_translation([0, 0, wall_thickness/2])
            
            try:
                garage_body = garage_outer.difference(garage_inner)
                # Position: right side (x), back/south half (y), lower height (z)
                garage_body.apply_translation([width/2 - garage_width/2, -length/2 + garage_length/2, -height*0.15])
            except Exception:
                garage_body = garage_outer
                garage_body.apply_translation([width/2 - garage_width/2, -length/2 + garage_length/2, -height*0.15])
            
            meshes.append(garage_body)
        
        # Roof (flat/modern or triangular)
        if is_modern:
            # Flat modern roof (thin slab slightly larger than house)
            roof_thickness = 0.15
            roof = trimesh.creation.box(extents=[main_width + 0.5, length + 0.5, roof_thickness])
            roof_offset = -(width - main_width)/2 if has_garage else 0
            roof.apply_translation([roof_offset, 0, height/2 + roof_thickness/2])
            meshes.append(roof)
        else:
            # Traditional triangular roof
            roof_height = height * 0.3
            roof_offset = -(width - main_width)/2 if has_garage else 0
            roof_vertices = [
                [-main_width/2 + roof_offset, -length/2, height/2],
                [main_width/2 + roof_offset, -length/2, height/2],
                [main_width/2 + roof_offset, length/2, height/2],
                [-main_width/2 + roof_offset, length/2, height/2],
                [roof_offset, -length/2, height/2 + roof_height],
                [roof_offset, length/2, height/2 + roof_height],
            ]
            
            roof_faces = [
                [0, 1, 4], [1, 2, 4], [2, 3, 5], [3, 0, 5], [4, 5, 1], [5, 4, 3]
            ]
            
            roof = trimesh.Trimesh(vertices=roof_vertices, faces=roof_faces)
            meshes.append(roof)
        
        # Main entrance door
        door_width = 0.9
        door_height = 2.0
        door_thickness = 0.05
        door_x_offset = -(width - main_width)/2 if has_garage else 0
        door = trimesh.creation.box(extents=[door_width, door_thickness, door_height])
        door.apply_translation([door_x_offset, -length/2 - wall_thickness/2, -height/2 + door_height/2])
        meshes.append(door)
        
        # Windows on side walls (distributed evenly on left and right walls)
        num_windows = int(features.get('windows', 4) or 4)  # Default 4 if not specified
        windows_per_side = num_windows // 2
        
        if windows_per_side > 0:
            window_width = 1.2
            window_height = 1.5
            window_thickness = 0.05
            window_z = height * 0.15
            window_spacing = length / (windows_per_side + 1)
            
            for i in range(windows_per_side):
                window_y = -length/2 + window_spacing * (i + 1)
                
                # Left wall windows
                left_window = trimesh.creation.box(extents=[window_thickness, window_width, window_height])
                left_x = -main_width/2 - wall_thickness/2
                if has_garage:
                    left_x -= (width - main_width)/2
                left_window.apply_translation([left_x, window_y, window_z])
                meshes.append(left_window)
                
                # Right wall windows
                right_window = trimesh.creation.box(extents=[window_thickness, window_width, window_height])
                right_x = main_width/2 + wall_thickness/2
                if has_garage:
                    right_x -= (width - main_width)/2
                right_window.apply_translation([right_x, window_y, window_z])
                meshes.append(right_window)
        
        return trimesh.util.concatenate(meshes)
    
    def _create_material(self, parsed_obj: ParsedObject) -> dict:
        """Create material properties"""
        materials = parsed_obj.materials if parsed_obj.materials else ["kayu"]
        
        material_colors = {
            "kayu": [0.6, 0.4, 0.2],
            "metal": [0.8, 0.8, 0.9],
            "plastik": [0.9, 0.9, 0.9],
            "kaca": [0.9, 0.9, 1.0],
            "beton": [0.7, 0.7, 0.7]
        }
        
        primary_material = materials[0]
        color = material_colors.get(primary_material, [0.6, 0.6, 0.6])
        
        return {
            "diffuse": color,
            "ambient": [c * 0.3 for c in color],
            "specular": [0.1, 0.1, 0.1]
        }
    
    def _create_mtl_file(self, filename: str, material_name: str, material: dict):
        """Create MTL material file"""
        content = f"""# Material file for {material_name}
newmtl {material_name}
Ka {material['ambient'][0]:.3f} {material['ambient'][1]:.3f} {material['ambient'][2]:.3f}
Kd {material['diffuse'][0]:.3f} {material['diffuse'][1]:.3f} {material['diffuse'][2]:.3f}
Ks {material['specular'][0]:.3f} {material['specular'][1]:.3f} {material['specular'][2]:.3f}
Ns 10.0
d 1.0
illum 2
"""
        
        with open(filename, 'w') as f:
            f.write(content)

    def create_3d_model(self, parsed_data: dict, stl_output: str, obj_output: str):
        """Create 3D models from parsed data"""
        furniture_type = parsed_data['type']
        dimensions = parsed_data['dimensions']
        features = parsed_data.get('features', {})
        
        if not dimensions:
            # Default dimensions based on type
            if furniture_type == 'chair':
                dimensions = type('Dimensions', (), {'width': 0.40, 'length': 0.40, 'height': 0.45})()
            elif furniture_type == 'table':
                dimensions = type('Dimensions', (), {'width': 0.80, 'length': 1.20, 'height': 0.75})()
            elif furniture_type == 'room':
                dimensions = type('Dimensions', (), {'width': 4.0, 'length': 5.0, 'height': 3.0})()
            else:
                dimensions = type('Dimensions', (), {'width': 1.0, 'length': 1.0, 'height': 0.8})()
        
        # Create mesh based on furniture type (pass features)
        mesh = self._create_mesh_from_type(furniture_type, dimensions, features)
        
        # Export STL
        mesh.export(stl_output)
        
        # Export OBJ with MTL
        obj_base = obj_output.replace('.obj', '')
        mesh.export(obj_output)
        
        # Create simple material based on furniture type
        if furniture_type == 'chair':
            material = {
                'ambient': [0.2, 0.1, 0.05], 'diffuse': [0.6, 0.4, 0.2], 'specular': [0.3, 0.3, 0.3]
            }
        elif furniture_type == 'table':
            material = {
                'ambient': [0.25, 0.2, 0.1], 'diffuse': [0.8, 0.6, 0.4], 'specular': [0.3, 0.3, 0.3]
            }
        elif furniture_type == 'room':
            material = {
                'ambient': [0.3, 0.3, 0.25], 'diffuse': [0.9, 0.9, 0.8], 'specular': [0.1, 0.1, 0.1]
            }
        else:
            material = {
                'ambient': [0.2, 0.2, 0.2], 'diffuse': [0.7, 0.7, 0.7], 'specular': [0.3, 0.3, 0.3]
            }
        
        self._create_mtl_file(f"{obj_base}.mtl", furniture_type, material)
    
    def _create_mesh_from_type(self, furniture_type: str, dimensions, features: dict = None):
        """Create mesh based on furniture type"""
        if features is None:
            features = {}
            
        width = dimensions.width
        length = dimensions.length
        height = dimensions.height
        
        if furniture_type == 'chair':
            return self._create_chair_mesh(width, length, height, features)
        elif furniture_type == 'table':
            return self._create_table_mesh(width, length, height, features)
        elif furniture_type == 'sofa':
            return self._create_sofa_mesh(width, length, height, features)
        elif furniture_type == 'cabinet':
            return self._create_cabinet_mesh(width, length, height, features)
        elif furniture_type == 'room':
            return self._create_room_mesh(width, length, height, features)
        elif furniture_type == 'house':
            return self._create_house_mesh(width, length, height, features)
        else:
            # Default: simple box
            return trimesh.creation.box(extents=[width, length, height])
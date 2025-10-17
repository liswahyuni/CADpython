from typing import List
from text_parser import ParsedObject
import trimesh


class Extruder3D:
    def __init__(self):
        self.default_thickness = 5.0

    def generate_stl(self, parsed_obj: ParsedObject, filename: str) -> None:
        meshes = []
        
        if parsed_obj.object_type == "kursi":
            meshes.extend(self._create_chair_3d(parsed_obj))
        elif parsed_obj.object_type == "meja":
            meshes.extend(self._create_table_3d(parsed_obj))
        elif parsed_obj.object_type == "ruangan":
            meshes.extend(self._create_room_3d(parsed_obj))
        else:
            meshes.extend(self._create_generic_3d(parsed_obj))
        
        if meshes:
            combined_mesh = trimesh.util.concatenate(meshes)
            combined_mesh.export(filename)

    def generate_obj(self, parsed_obj: ParsedObject, filename: str) -> None:
        meshes = []
        
        if parsed_obj.object_type == "kursi":
            meshes.extend(self._create_chair_3d(parsed_obj))
        elif parsed_obj.object_type == "meja":
            meshes.extend(self._create_table_3d(parsed_obj))
        elif parsed_obj.object_type == "ruangan":
            meshes.extend(self._create_room_3d(parsed_obj))
        else:
            meshes.extend(self._create_generic_3d(parsed_obj))
        
        if meshes:
            combined_mesh = trimesh.util.concatenate(meshes)
            combined_mesh.export(filename)

    def _create_chair_3d(self, parsed_obj: ParsedObject) -> List:
        meshes = []
        width = parsed_obj.dimensions.width
        length = parsed_obj.dimensions.length
        height = parsed_obj.dimensions.height
        
        seat_height = height * 0.6
        seat_thickness = 3.0
        
        seat = trimesh.creation.box(
            extents=[width, length, seat_thickness],
            transform=trimesh.transformations.translation_matrix([0, 0, seat_height])
        )
        meshes.append(seat)
        
        back_width = 3.0
        back = trimesh.creation.box(
            extents=[back_width, length, height - seat_height],
            transform=trimesh.transformations.translation_matrix([-width/2 + back_width/2, 0, seat_height + (height - seat_height)/2])
        )
        meshes.append(back)
        
        leg_count = len([f for f in parsed_obj.features if f.name == "kaki"])
        if leg_count == 0:
            leg_count = 4
            
        leg_radius = 2.0
        leg_positions = [
            [-width/2 + 5, -length/2 + 5, seat_height/2],
            [width/2 - 5, -length/2 + 5, seat_height/2],
            [width/2 - 5, length/2 - 5, seat_height/2],
            [-width/2 + 5, length/2 - 5, seat_height/2]
        ]
        
        for i in range(min(leg_count, 4)):
            leg = trimesh.creation.cylinder(
                radius=leg_radius,
                height=seat_height,
                transform=trimesh.transformations.translation_matrix(leg_positions[i])
            )
            meshes.append(leg)
        
        return meshes

    def _create_table_3d(self, parsed_obj: ParsedObject) -> List:
        meshes = []
        width = parsed_obj.dimensions.width
        length = parsed_obj.dimensions.length
        height = parsed_obj.dimensions.height
        
        # Table top
        top_thickness = 3.0
        table_top = trimesh.creation.box(
            extents=[width, length, top_thickness],
            transform=trimesh.transformations.translation_matrix([0, 0, height - top_thickness/2])
        )
        meshes.append(table_top)
        
        # 4 table legs
        leg_radius = 2.5
        leg_height = height - top_thickness
        leg_positions = [
            [-width/2 + 8, -length/2 + 8, leg_height/2],
            [width/2 - 8, -length/2 + 8, leg_height/2],
            [width/2 - 8, length/2 - 8, leg_height/2],
            [-width/2 + 8, length/2 - 8, leg_height/2]
        ]
        
        for pos in leg_positions:
            leg = trimesh.creation.cylinder(
                radius=leg_radius,
                height=leg_height,
                transform=trimesh.transformations.translation_matrix(pos)
            )
            meshes.append(leg)
        
        return meshes

    def _create_room_3d(self, parsed_obj: ParsedObject) -> List:
        meshes = []
        width = parsed_obj.dimensions.width
        length = parsed_obj.dimensions.length
        height = parsed_obj.dimensions.height
        wall_thickness = 10.0
        
        # Identifikasi posisi pintu dan jendela
        door_wall = None  # utara/selatan/timur/barat
        window_wall = None
        
        for feature in parsed_obj.features:
            if feature.name == "pintu":
                if "barat" in feature.position or "west" in feature.position:
                    door_wall = "barat"
                elif "timur" in feature.position or "east" in feature.position:
                    door_wall = "timur"
                elif "utara" in feature.position or "north" in feature.position:
                    door_wall = "utara"
                elif "selatan" in feature.position or "south" in feature.position:
                    door_wall = "selatan"
            elif feature.name == "jendela":
                if "barat" in feature.position or "west" in feature.position:
                    window_wall = "barat"
                elif "timur" in feature.position or "east" in feature.position:
                    window_wall = "timur"
                elif "utara" in feature.position or "north" in feature.position:
                    window_wall = "utara"
                elif "selatan" in feature.position or "south" in feature.position:
                    window_wall = "selatan"
        
        # Ukuran pintu dan jendela standar
        door_width = min(90, width * 0.3)  # Pintu standar 90cm
        door_height = height * 0.85  # Tinggi pintu 85% dari tinggi ruangan
        window_width = min(120, width * 0.4)  # Jendela standar 120cm
        window_height = height * 0.4  # Tinggi jendela 40% dari tinggi ruangan
        window_bottom = height * 0.35  # Jendela mulai 35% dari bawah
        
        # Buat dinding dengan bukaan untuk pintu/jendela
        # Dinding Utara (belakang, Y positif)
        if door_wall == "utara" or window_wall == "utara":
            meshes.extend(self._create_wall_with_opening(
                wall_extents=[width, wall_thickness, height],
                wall_position=[0, length/2, height/2],
                has_door=(door_wall == "utara"),
                has_window=(window_wall == "utara"),
                door_width=door_width,
                door_height=door_height,
                window_width=window_width,
                window_height=window_height,
                window_bottom=window_bottom,
                orientation="horizontal"
            ))
        else:
            meshes.append(trimesh.creation.box(
                extents=[width, wall_thickness, height],
                transform=trimesh.transformations.translation_matrix([0, length/2, height/2])
            ))
        
        # Dinding Selatan (depan, Y negatif)
        if door_wall == "selatan" or window_wall == "selatan":
            meshes.extend(self._create_wall_with_opening(
                wall_extents=[width, wall_thickness, height],
                wall_position=[0, -length/2, height/2],
                has_door=(door_wall == "selatan"),
                has_window=(window_wall == "selatan"),
                door_width=door_width,
                door_height=door_height,
                window_width=window_width,
                window_height=window_height,
                window_bottom=window_bottom,
                orientation="horizontal"
            ))
        else:
            meshes.append(trimesh.creation.box(
                extents=[width, wall_thickness, height],
                transform=trimesh.transformations.translation_matrix([0, -length/2, height/2])
            ))
        
        # Dinding Barat (kiri, X negatif)
        if door_wall == "barat" or window_wall == "barat":
            meshes.extend(self._create_wall_with_opening(
                wall_extents=[wall_thickness, length, height],
                wall_position=[-width/2, 0, height/2],
                has_door=(door_wall == "barat"),
                has_window=(window_wall == "barat"),
                door_width=door_width,
                door_height=door_height,
                window_width=window_width,
                window_height=window_height,
                window_bottom=window_bottom,
                orientation="vertical"
            ))
        else:
            meshes.append(trimesh.creation.box(
                extents=[wall_thickness, length, height],
                transform=trimesh.transformations.translation_matrix([-width/2, 0, height/2])
            ))
        
        # Dinding Timur (kanan, X positif)
        if door_wall == "timur" or window_wall == "timur":
            meshes.extend(self._create_wall_with_opening(
                wall_extents=[wall_thickness, length, height],
                wall_position=[width/2, 0, height/2],
                has_door=(door_wall == "timur"),
                has_window=(window_wall == "timur"),
                door_width=door_width,
                door_height=door_height,
                window_width=window_width,
                window_height=window_height,
                window_bottom=window_bottom,
                orientation="vertical"
            ))
        else:
            meshes.append(trimesh.creation.box(
                extents=[wall_thickness, length, height],
                transform=trimesh.transformations.translation_matrix([width/2, 0, height/2])
            ))
        
        # Floor
        floor = trimesh.creation.box(
            extents=[width, length, wall_thickness],
            transform=trimesh.transformations.translation_matrix([0, 0, wall_thickness/2])
        )
        meshes.append(floor)
        
        return meshes
    
    def _create_wall_with_opening(self, wall_extents, wall_position, has_door, has_window,
                                   door_width, door_height, window_width, window_height,
                                   window_bottom, orientation):
        """Membuat dinding dengan bukaan pintu/jendela menggunakan segmen-segmen box"""
        meshes = []
        wall_w, wall_d, wall_h = wall_extents
        pos_x, pos_y, pos_z = wall_position
        
        if orientation == "horizontal":
            # Dinding horizontal (utara/selatan), opening di tengah sumbu X
            
            if has_door:
                # Segmen kiri pintu
                left_width = (wall_w - door_width) / 2
                if left_width > 5:
                    left_wall = trimesh.creation.box(
                        extents=[left_width, wall_d, wall_h],
                        transform=trimesh.transformations.translation_matrix([
                            pos_x - wall_w/2 + left_width/2, pos_y, pos_z
                        ])
                    )
                    meshes.append(left_wall)
                
                # Segmen kanan pintu
                right_wall = trimesh.creation.box(
                    extents=[left_width, wall_d, wall_h],
                    transform=trimesh.transformations.translation_matrix([
                        pos_x + wall_w/2 - left_width/2, pos_y, pos_z
                    ])
                )
                meshes.append(right_wall)
                
                # Segmen atas pintu
                top_height = wall_h - door_height
                if top_height > 5:
                    top_wall = trimesh.creation.box(
                        extents=[door_width, wall_d, top_height],
                        transform=trimesh.transformations.translation_matrix([
                            pos_x, pos_y, pos_z + wall_h/2 - top_height/2
                        ])
                    )
                    meshes.append(top_wall)
            
            elif has_window:
                # Segmen bawah jendela
                bottom_height = window_bottom
                if bottom_height > 5:
                    bottom_wall = trimesh.creation.box(
                        extents=[wall_w, wall_d, bottom_height],
                        transform=trimesh.transformations.translation_matrix([
                            pos_x, pos_y, pos_z - wall_h/2 + bottom_height/2
                        ])
                    )
                    meshes.append(bottom_wall)
                
                # Segmen atas jendela
                top_height = wall_h - window_bottom - window_height
                if top_height > 5:
                    top_wall = trimesh.creation.box(
                        extents=[wall_w, wall_d, top_height],
                        transform=trimesh.transformations.translation_matrix([
                            pos_x, pos_y, pos_z + wall_h/2 - top_height/2
                        ])
                    )
                    meshes.append(top_wall)
                
                # Segmen kiri jendela
                left_width = (wall_w - window_width) / 2
                if left_width > 5:
                    left_wall = trimesh.creation.box(
                        extents=[left_width, wall_d, window_height],
                        transform=trimesh.transformations.translation_matrix([
                            pos_x - wall_w/2 + left_width/2, pos_y, 
                            pos_z - wall_h/2 + window_bottom + window_height/2
                        ])
                    )
                    meshes.append(left_wall)
                
                # Segmen kanan jendela
                right_wall = trimesh.creation.box(
                    extents=[left_width, wall_d, window_height],
                    transform=trimesh.transformations.translation_matrix([
                        pos_x + wall_w/2 - left_width/2, pos_y,
                        pos_z - wall_h/2 + window_bottom + window_height/2
                    ])
                )
                meshes.append(right_wall)
        
        else:  # vertical orientation (timur/barat)
            # Dinding vertikal (timur/barat), opening di tengah sumbu Y
            
            if has_door:
                # Segmen depan pintu
                front_length = (wall_d - door_width) / 2
                if front_length > 5:
                    front_wall = trimesh.creation.box(
                        extents=[wall_w, front_length, wall_h],
                        transform=trimesh.transformations.translation_matrix([
                            pos_x, pos_y - wall_d/2 + front_length/2, pos_z
                        ])
                    )
                    meshes.append(front_wall)
                
                # Segmen belakang pintu
                back_wall = trimesh.creation.box(
                    extents=[wall_w, front_length, wall_h],
                    transform=trimesh.transformations.translation_matrix([
                        pos_x, pos_y + wall_d/2 - front_length/2, pos_z
                    ])
                )
                meshes.append(back_wall)
                
                # Segmen atas pintu
                top_height = wall_h - door_height
                if top_height > 5:
                    top_wall = trimesh.creation.box(
                        extents=[wall_w, door_width, top_height],
                        transform=trimesh.transformations.translation_matrix([
                            pos_x, pos_y, pos_z + wall_h/2 - top_height/2
                        ])
                    )
                    meshes.append(top_wall)
            
            elif has_window:
                # Segmen bawah jendela
                bottom_height = window_bottom
                if bottom_height > 5:
                    bottom_wall = trimesh.creation.box(
                        extents=[wall_w, wall_d, bottom_height],
                        transform=trimesh.transformations.translation_matrix([
                            pos_x, pos_y, pos_z - wall_h/2 + bottom_height/2
                        ])
                    )
                    meshes.append(bottom_wall)
                
                # Segmen atas jendela
                top_height = wall_h - window_bottom - window_height
                if top_height > 5:
                    top_wall = trimesh.creation.box(
                        extents=[wall_w, wall_d, top_height],
                        transform=trimesh.transformations.translation_matrix([
                            pos_x, pos_y, pos_z + wall_h/2 - top_height/2
                        ])
                    )
                    meshes.append(top_wall)
                
                # Segmen depan jendela
                front_length = (wall_d - window_width) / 2
                if front_length > 5:
                    front_wall = trimesh.creation.box(
                        extents=[wall_w, front_length, window_height],
                        transform=trimesh.transformations.translation_matrix([
                            pos_x, pos_y - wall_d/2 + front_length/2,
                            pos_z - wall_h/2 + window_bottom + window_height/2
                        ])
                    )
                    meshes.append(front_wall)
                
                # Segmen belakang jendela
                back_wall = trimesh.creation.box(
                    extents=[wall_w, front_length, window_height],
                    transform=trimesh.transformations.translation_matrix([
                        pos_x, pos_y + wall_d/2 - front_length/2,
                        pos_z - wall_h/2 + window_bottom + window_height/2
                    ])
                )
                meshes.append(back_wall)
        
        return meshes

    def _create_generic_3d(self, parsed_obj: ParsedObject) -> List:
        width = parsed_obj.dimensions.width
        length = parsed_obj.dimensions.length
        height = parsed_obj.dimensions.height
        
        box = trimesh.creation.box(
            extents=[width, length, height],
            transform=trimesh.transformations.translation_matrix([0, 0, height/2])
        )
        
        return [box]
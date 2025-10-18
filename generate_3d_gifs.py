import os
import trimesh
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter


def render_rotating_gif(stl_path: str, output_gif: str, frames: int = 36, resolution: tuple = (800, 600)):
    print(f"Loading {stl_path}...")
    mesh = trimesh.load(stl_path)
    
    mesh.vertices -= mesh.center_mass
    max_dimension = max(mesh.extents)
    scale = 2.0 / max_dimension
    mesh.apply_scale(scale)
    
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')
    
    vertices = mesh.vertices
    faces = mesh.faces
    
    def update(frame):
        ax.clear()
        
        angle = 2 * np.pi * frame / frames
        rotation = trimesh.transformations.rotation_matrix(angle, [0, 0, 1])
        rotated_vertices = trimesh.transform_points(vertices, rotation)
        
        ax.plot_trisurf(
            rotated_vertices[:, 0], 
            rotated_vertices[:, 1], 
            rotated_vertices[:, 2],
            triangles=faces,
            color='lightblue',
            edgecolor='gray',
            linewidth=0.1,
            alpha=0.9
        )
        
        max_range = 1.2
        ax.set_xlim([-max_range, max_range])
        ax.set_ylim([-max_range, max_range])
        ax.set_zlim([-max_range, max_range])
        ax.set_box_aspect([1, 1, 1])
        ax.set_axis_off()
        
        return ax,
    
    print(f"Rendering {frames} frames...")
    anim = FuncAnimation(fig, update, frames=frames, interval=100, blit=False)
    
    print(f"Saving GIF to {output_gif}...")
    writer = PillowWriter(fps=10)
    anim.save(output_gif, writer=writer, dpi=100)
    plt.close(fig)
    
    file_size = os.path.getsize(output_gif) / 1024
    print(f"Created {output_gif} ({file_size:.1f} KB)\n")


def main():
    output_dir = "demo_output"
    gif_dir = os.path.join(output_dir, "gifs")
    os.makedirs(gif_dir, exist_ok=True)
    
    # List of objects to render
    objects = [
        ("chair_demo", "Chair (4 legs)"),
        ("round_dining_table", "Round Dining Table"),
        ("three_seat_sofa", "Three-Seat Sofa"),
        ("wardrobe", "Wardrobe (2 doors)"),
        ("room_demo", "Room (door & window)"),
        ("modern_house", "Modern House (with garage)")
    ]
    
    print("=" * 60)
    print("3D to GIF Animation Generator")
    print("=" * 60)
    print()
    
    for obj_name, description in objects:
        stl_path = os.path.join(output_dir, f"{obj_name}.stl")
        gif_path = os.path.join(gif_dir, f"{obj_name}.gif")
        
        if not os.path.exists(stl_path):
            print(f"Skipping {obj_name}: STL not found")
            continue
        
        print(f"Processing: {description}")
        try:
            render_rotating_gif(stl_path, gif_path, frames=36)
        except Exception as e:
            print(f"Error rendering {obj_name}: {e}\n")
    
    print("=" * 60)
    print("All GIF animations generated!")
    print(f"Output directory: {gif_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()

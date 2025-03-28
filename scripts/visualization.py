import os

import bpy
from mathutils import Vector  # Add this import


def clear_scene():
    # Clear existing mesh objects
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def setup_camera(objects):
    # Create camera
    bpy.ops.object.camera_add()
    camera = bpy.context.active_object

    # Calculate the center point and bounds of all objects
    min_x = min_y = min_z = float("inf")
    max_x = max_y = max_z = float("-inf")

    for obj in objects:
        bounds = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        for point in bounds:
            min_x = min(min_x, point.x)
            max_x = max(max_x, point.x)
            min_y = min(min_y, point.y)
            max_y = max(max_y, point.y)
            min_z = min(min_z, point.z)
            max_z = max(max_z, point.z)

    center = Vector(
        ((max_x + min_x) / 2, (max_y + min_y) / 2, (max_z + min_z) / 2)
    )

    # Position camera
    distance = max((max_x - min_x), (max_y - min_y), (max_z - min_z)) * 2
    camera.location = center + Vector((distance, -distance, distance))

    # Point camera to center of objects
    direction = center - camera.location
    rot_quat = direction.to_track_quat("-Z", "Y")
    camera.rotation_euler = rot_quat.to_euler()

    return camera


def setup_lighting():
    # Create light
    bpy.ops.object.light_add(type="SUN")
    light = bpy.context.active_object
    light.location = (5, 5, 10)
    light.data.energy = 5


def render_scene(output_path):
    # Set up render settings
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.filepath = output_path

    # Render
    bpy.ops.render.render(write_still=True)


def process_glb_pairs(folder1, folder2, output_folder):
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Get GLB files from both folders
    files1 = {f for f in os.listdir(folder1) if f.endswith(".glb")}
    files2 = {f for f in os.listdir(folder2) if f.endswith(".glb")}

    # Find common files
    common_files = files1.intersection(files2)

    for file in common_files:
        # Clear the scene
        clear_scene()

        # Import both GLB files
        path1 = os.path.join(folder1, file)
        path2 = os.path.join(folder2, file)

        bpy.ops.import_scene.gltf(filepath=path1)
        # Move first model to the left
        for obj in bpy.context.selected_objects:
            obj.location.x -= 2

        bpy.ops.import_scene.gltf(filepath=path2)
        # Move second model to the right
        for obj in bpy.context.selected_objects:
            obj.location.x += 2

        # Setup camera
        camera = setup_camera(
            [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
        )
        bpy.context.scene.camera = camera

        # Setup lighting
        setup_lighting()

        # Render and save
        output_path = os.path.join(
            output_folder, f"comparison_{os.path.splitext(file)[0]}.png"
        )
        render_scene(output_path)


# Usage
folder1 = "benchmark_output"
folder2 = "benchmark_output_new"
output_folder = "visualization_output"

process_glb_pairs(folder1, folder2, output_folder)

import os

import bpy
from mathutils import Vector


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def setup_camera(objects):
    bpy.ops.object.camera_add()
    camera = bpy.context.active_object

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

    # Reduced distance factor (was 3, now 1.5) to bring camera closer
    distance = max((max_x - min_x), (max_y - min_y), (max_z - min_z)) * 1.5
    camera.location = center + Vector((distance, -distance, distance))

    direction = center - camera.location
    rot_quat = direction.to_track_quat("-Z", "Y")
    camera.rotation_euler = rot_quat.to_euler()

    return camera


def setup_lighting():
    bpy.ops.object.light_add(type="SUN")
    light = bpy.context.active_object
    light.location = (5, 5, 10)
    light.data.energy = 5


def render_scene(output_path):
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.filepath = output_path

    # Increase render resolution for better quality
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080

    bpy.ops.render.render(write_still=True)


def process_glb_triplets(folder1, folder2, folder3, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    files1 = {f for f in os.listdir(folder1) if f.endswith(".glb")}
    files2 = {f for f in os.listdir(folder2) if f.endswith(".glb")}
    files3 = {f for f in os.listdir(folder3) if f.endswith(".glb")}

    common_files = files1.intersection(files2).intersection(files3)

    for file in common_files:
        clear_scene()

        path1 = os.path.join(folder1, file)
        path2 = os.path.join(folder2, file)
        path3 = os.path.join(folder3, file)

        # Import and position first model (left)
        bpy.ops.import_scene.gltf(filepath=path1)
        for obj in bpy.context.selected_objects:
            obj.location.x -= 3  # Reduced spacing (was 4)

        # Import and position second model (center)
        bpy.ops.import_scene.gltf(filepath=path2)
        # Center model stays at default position

        # Import and position third model (right)
        bpy.ops.import_scene.gltf(filepath=path3)
        for obj in bpy.context.selected_objects:
            obj.location.x += 3  # Reduced spacing (was 4)

        camera = setup_camera(
            [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
        )
        bpy.context.scene.camera = camera

        setup_lighting()

        output_path = os.path.join(
            output_folder, f"comparison_{os.path.splitext(file)[0]}.png"
        )
        render_scene(output_path)


# Usage
folder1 = "benchmark_output"
folder2 = "benchmark_output_new"
folder3 = "benchmark_output_finetuned"
output_folder = "visualization_output"

process_glb_triplets(folder1, folder2, folder3, output_folder)

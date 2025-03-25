import os
import sys

import bpy

force_continue = True
temp_directory = None
# Parse arguments
for current_argument in sys.argv:
    if force_continue:
        if current_argument == "--":
            force_continue = False
        continue
    # First argument after -- is the input file
    # Second argument after -- is the temp directory
    if temp_directory is None:
        temp_directory = current_argument
        continue
    root, current_extension = os.path.splitext(current_argument)
    current_basename = os.path.basename(root)
    if (
        current_extension != ".abc"
        and current_extension != ".blend"
        and current_extension != ".dae"
        and current_extension != ".fbx"
        and current_extension != ".obj"
        and current_extension != ".ply"
        and current_extension != ".stl"
        and current_extension != ".usd"
        and current_extension != ".usda"
        and current_extension != ".usdc"
        and current_extension != ".wrl"
        and current_extension != ".x3d"
    ):
        continue

    # Add this after the imports section
    def enable_required_addons():
        # Get preferences
        preferences = bpy.context.preferences
        addon_prefs = preferences.addons
        # Try to enable built-in addons
        try:
            bpy.ops.preferences.addon_enable(module="obj")
        except Exception as e:
            print(f"Warning: Could not enable OBJ addon: {e}")

    def import_obj(filepath):
        try:
            # First attempt - try direct import
            bpy.ops.import_scene.obj(filepath=filepath)
        except Exception as e:
            print(f"First import attempt failed: {e}")
            try:
                # Second attempt - try manual import
                bpy.ops.wm.obj_import(filepath=filepath)
            except Exception as e:
                print(f"Second import attempt failed: {e}")
                return False
        # Verify if anything was imported
        if len(bpy.data.objects) <= 1:  # Only default cube or nothing
            print("Warning: No objects were imported")
            return False
        # If we reached here, import was successful
        print(f"Successfully imported {len(bpy.data.objects)} objects")
        # Delete default cube if it exists
        for obj in bpy.data.objects:
            if obj.name.startswith("Cube"):
                bpy.data.objects.remove(obj, do_unlink=True)
        return True

    # In your main loop, replace the OBJ import section with:
    if current_extension == ".obj":
        if not import_obj(current_argument):
            print("Failed to import OBJ file")
            continue
        # Center and adjust view to imported objects
        for obj in bpy.data.objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = bpy.data.objects[0]
        bpy.ops.object.select_all(action="SELECT")

    # Apply X scale to all objects before export
    print("Recaling the mesh...")
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            # Store the original location
            original_location = obj.location.copy()

            # Apply the rescale
            obj.scale.x *= 18
            obj.scale.y *= 18
            obj.scale.z *= 18

            # Make the scale transformation permanent while preserving origin
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

            # Restore the original location
            obj.location = original_location

            print(f"Rescaled object while preserving origin: {obj.name}")

    # Move all objects X units down along the Z axis
    # for obj in bpy.data.objects:
    #     if obj.type == "MESH":
    #         obj.location.z -= 0.8
    #         print(f"Moved object down: {obj.name}")

    export_file = os.path.join(temp_directory, current_basename + ".gltf")
    print("Writing: '" + export_file + "'")
    bpy.ops.export_scene.gltf(filepath=export_file)

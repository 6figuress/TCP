#!/bin/bash
if [ "$#" = 2 ]
then
    blender -b -P scripts/obj_gltf.py -- "$2" "$1"
else
    echo To glTF 2.0 converter.
    echo Supported file formats: .obj
    echo
    echo "obj_gltf.sh [filename] [temp_directory]"
fi

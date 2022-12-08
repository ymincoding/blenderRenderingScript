
import argparse
import bpy
import json
import numpy as np
import os
import sys

# proportion of chest-size and length for each type of cloths
hoodie_prop = (0.3732, 0.758)
jacket_prop = (0.3792, 0.8949)
longsleeve_prop = (0.3253, 0.9225)
shirt_prop = (0.3657, 0.9474)
tshirt_prop = (0.6936, 0.9949)

def get_camera():
    for collection in bpy.data.collections:
        for object in collection.objects:
            if object.type == 'CAMERA':
                return object
    return None

#-----------------------------------------------------------------------------------------------------------------------

def find_smplx():
    for object in bpy.data.objects:
        if 'SMPLX-mesh' in object.name:
            return object
    return None

#-----------------------------------------------------------------------------------------------------------------------

def get_body_measurements(npy_path:str):
    assert os.path.exists(npy_path), 'Body measurement file {} does not exist.'.format(npy_path)

    body_measurements = np.load(npy_path)
    # For the test, just return first 50 measurements
    return body_measurements[:50]

#-----------------------------------------------------------------------------------------------------------------------

def set_body_measurement(measurement):
    assert len(measurement) == 2, 'Wrong body parameter. It should have height and weight.'

    bpy.data.window_managers['WinMan'].smplx_tool.smplx_height = measurement[0]
    bpy.data.window_managers['WinMan'].smplx_tool.smplx_weight = measurement[1]
    
    smplx_mesh = find_smplx()
    assert smplx_mesh != None, "There is no smplx object in blender file."
    
    bpy.context.view_layer.objects.active = smplx_mesh
    bpy.ops.object.smplx_measurements_to_shape()

#-----------------------------------------------------------------------------------------------------------------------

def find_cloth():
    for object in bpy.data.objects:
        if object.modifiers.find('SimplyCloth') != -1:
            return object
    return None

#-----------------------------------------------------------------------------------------------------------------------

def extract_cloth_size(cloth_type:str, output_dir:str):
    bpy.context.scene.frame_set(0)
    cloth = find_cloth()
    assert cloth != None, "There is no cloth object in blender file."

    dimensions = cloth.dimensions

    if cloth_type == 'hoodie':
        cloth_prop = hoodie_prop
    elif cloth_type == 'jacket':
        cloth_prop = jacket_prop
    elif cloth_type == 'longsleeve':
        cloth_prop = longsleeve_prop
    elif cloth_type == 'shirt':
        cloth_prop = shirt_prop
    elif cloth_type == 'tshirt':
        cloth_prop = tshirt_prop 

    data = {'size':[
                        {
                            'chest': dimensions.x * cloth_prop[0],
                            'length': dimensions.z * cloth_prop[1]
                        }
                    ]
            }

    data_json = json.dumps(data, indent=4)
    with open(os.path.join(output_dir, cloth_type + '.json'), 'w') as outfile:
        outfile.write(data_json)
    return

#-----------------------------------------------------------------------------------------------------------------------

def render_image(output_dir:str, output_name:str):
    for i in range(60):
        bpy.context.scene.frame_set(i + 1)

    # bpy.ops.render.render(animation=True)
    bpy.context.scene.render.image_settings.file_format = 'JPEG'
    bpy.context.scene.render.filepath = os.path.join(output_dir, output_name)
    bpy.ops.render.render(write_still=True)
    
#-----------------------------------------------------------------------------------------------------------------------

def run(args):
    print("Blender Script runs")

    if not os.path.exists(args.output_dir):
        os.mkdir(args.output_dir)

    camera = get_camera()
    assert camera != None, "There is no camera in blender file."

    body_sizes = get_body_measurements(args.body_measurement)

    print("Number of measures: ", len(body_sizes))
    count = 0
    for size in body_sizes:
        print(size)
        set_body_measurement(size)
        print("Height: ", bpy.data.window_managers['WinMan'].smplx_tool.smplx_height)
        print("Weight: ", bpy.data.window_managers['WinMan'].smplx_tool.smplx_weight)
        render_image(args.output_dir, args.cloth_type + str(count))
        extract_cloth_size(args.cloth_type, args.output_dir)
        count += 1

#=======================================================================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--cloth_type',
                        required=True,
                        help='Cloth type among 5 types')
    parser.add_argument('--body_measurement',
                        required=True,
                        help='Body measurements for smpl model as an npy file')
    parser.add_argument('--output_dir', 
                        required=True, 
                        help='Output directory to save the results')

    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    run(args)

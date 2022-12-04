
import argparse
import bpy
import json
import numpy as np
import os
import sys

def get_camera():
    for collection in bpy.data.collections:
        for object in collection.objects:
            if object.type == 'CAMERA':
                return object
    return None

#-----------------------------------------------------------------------------------------------------------------------

def get_body_measurement(npy_path:str):
    assert os.path.exists(npy_path), 'Body measurement file {} does not exist.'.format(npy_path)

    body_measurements = np.load(npy_path)
    return body_measurements[0]

#-----------------------------------------------------------------------------------------------------------------------

def set_body_measurement(measurement):
    assert len(measurement) == 2, 'Wrong body parameter. It should have height and weight.'

    bpy.data.window_managers['WinMan'].smplx_tool.smplx_height = measurement[0]
    bpy.data.window_managers['WinMan'].smplx_tool.smplx_weight = measurement[1]

#-----------------------------------------------------------------------------------------------------------------------

def find_cloth():
    for object in bpy.data.objects:
        if object.modifiers.find('SimplyCloth') != -1:
            return object
    return None

#-----------------------------------------------------------------------------------------------------------------------

def extract_cloth_size(cloth:object, output_dir:str):
    bpy.context.scene.frame_set(0)
    dimensions = cloth.dimensions

    data = {'size':[
                        {
                            'x': dimensions.x,
                            'y': dimensions.y,
                            'z': dimensions.z
                        }
                    ]
            }

    data_json = json.dumps(data, indent=4)
    with open(os.path.join(output_dir, cloth.name + '.json'), 'w') as outfile:
        outfile.write(data_json)
    return

#-----------------------------------------------------------------------------------------------------------------------

def render_image(output_dir:str):
    bpy.context.scene.frame_set(200)
    bpy.context.scene.render.image_settings.file_format = 'JPEG'
    bpy.context.scene.render.filepath = os.path.join(output_dir, 'output')
    bpy.ops.render.render(write_still=True)
    
#-----------------------------------------------------------------------------------------------------------------------

def run(args):
    print("Hello Blender Script")
    if not os.path.exists(args.output_dir):
        os.mkdir(args.output_dir)

    camera = get_camera()
    assert camera != None, "There is no camera in blender file."

    body_size = get_body_measurement(args.body_measurement)
    set_body_measurement(body_size)

    cloth = find_cloth()
    assert cloth != None, "There is no cloth object in blender file."

    extract_cloth_size(cloth, args.output_dir)

    render_image(args.output_dir)

#=======================================================================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--body_measurement',
                        required=True,
                        help='Body measurements for smpl model as an npy file')
    parser.add_argument('--output_dir', 
                        required=True, 
                        help='Output directory to save the results')

    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    run(args)

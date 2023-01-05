
import argparse
import bpy
import json
import numpy as np
import os
import random
import sys

class Config:
    def __init__(self):
        pass

#-----------------------------------------------------------------------------------------------------------------------

def parse_configuration(config_file):
    try:
        with open(config_file) as configuration:
            models = json.load(configuration)
    except:
        print('Failed to open configuration file {}.'.format(config_file))
        exit()
    
    arguments = models['Arguments'][0]
    config = Config()
    config.cloth_type = arguments['cloth_type']
    config.body_measurement = arguments['body_measurement']
    config.rendering_frame = arguments['rendering_frame']
    config.length_ratio = arguments['length_ratio']
    config.min_chest = arguments['min_chest']
    config.max_chest = arguments['max_chest']
    config.cloth_prop = [arguments['chest_proportion'], arguments['length_proportion']]
    config.output_dir_input = os.path.join(arguments['output_dir'], 'input')
    config.output_dir_measurement = os.path.join(arguments['output_dir'], 'measurement')
    config.output_dir_gt = os.path.join(arguments['output_dir'], 'groundtruth')

    return config

#-----------------------------------------------------------------------------------------------------------------------

def validate_configuration(config):
    assert os.path.exists(config.body_measurement), 'Body measurement file {} does not exist.'.format(config.body_measurement)

    if not os.path.exists(config.output_dir_input):
        os.makedirs(config.output_dir_input)

    if not os.path.exists(config.output_dir_measurement):
        os.makedirs(config.output_dir_measurement)

    if not os.path.exists(config.output_dir_gt):
        os.makedirs(config.output_dir_gt)

#-----------------------------------------------------------------------------------------------------------------------

def get_main_camera():
    for collection in bpy.data.collections:
        for object in collection.objects:
            if object.type == 'CAMERA':
                if 'input' not in object.name:
                    return object
    return None

#-----------------------------------------------------------------------------------------------------------------------

def get_input_camera():
    for collection in bpy.data.collections:
        for object in collection.objects:
            if object.type == 'CAMERA':
                if 'input' in object.name:
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
    return body_measurements

#-----------------------------------------------------------------------------------------------------------------------

def set_body_measurement(measurement):
    bpy.data.window_managers['WinMan'].smplx_tool.smplx_height = measurement[0]
    bpy.data.window_managers['WinMan'].smplx_tool.smplx_weight = measurement[1]
    
    smplx_mesh = find_smplx()
    assert smplx_mesh != None, "There is no smplx object in blender file."
    
    bpy.context.view_layer.objects.active = smplx_mesh
    bpy.ops.object.smplx_measurements_to_shape()

#-----------------------------------------------------------------------------------------------------------------------

def find_main_cloth():
    for object in bpy.data.objects:
        if object.modifiers.find('SimplyCloth') != -1 and 'input' not in object.name:
            return object
    return None

#-----------------------------------------------------------------------------------------------------------------------

def find_input_cloth():
    for object in bpy.data.objects:
        if object.modifiers.find('SimplyCloth') != -1 and 'input' in object.name:
            return object
    return None

#-----------------------------------------------------------------------------------------------------------------------

def pickRandomSize(min_chest, max_chest):
    return random.uniform(min_chest, max_chest)

#-----------------------------------------------------------------------------------------------------------------------

def set_cloth_size(cloth, chest_circumference, length_ratio, length_variation, cloth_prop):
    bpy.context.scene.frame_set(0)

    chest_half = chest_circumference / 2 * 0.01

    dimension_x = chest_half / cloth_prop[0]
    dimension_y = cloth.dimensions.y
    dimension_z = chest_circumference / length_ratio / cloth_prop[1] * 0.01

    cloth.dimensions = [dimension_x, dimension_y, dimension_z + dimension_z * length_variation]

#-----------------------------------------------------------------------------------------------------------------------

def save_size_info(size, cloth, cloth_prop, output_dir:str, output_name:str):
    bpy.context.scene.frame_set(0)

    dimensions = cloth.dimensions
    data = {'body':[
                        {
                            'height': size[0],
                            'weight': size[1]
                        }
                    ],
            'size':[
                        {
                            'chest': dimensions.x * cloth_prop[0],
                            'length': dimensions.z * cloth_prop[1]
                        }
                    ]
            }

    data_json = json.dumps(data, indent=4)
    with open(os.path.join(output_dir, output_name + '.json'), 'w') as outfile:
        outfile.write(data_json)
    return

#-----------------------------------------------------------------------------------------------------------------------

def render_image(frame:int, camera_main, camera_input, output_dir_gt:str, output_dir_input:str, output_name:str):
    for i in range(frame + 1):
        bpy.context.scene.frame_set(i)

    bpy.context.scene.render.image_settings.file_format = 'JPEG'

    bpy.context.scene.camera = camera_main
    bpy.context.scene.render.filepath = os.path.join(output_dir_gt, output_name)
    bpy.ops.render.render(write_still=True)

    bpy.context.scene.camera = camera_input
    bpy.context.scene.render.filepath = os.path.join(output_dir_input, output_name)
    bpy.ops.render.render(write_still=True)

#-----------------------------------------------------------------------------------------------------------------------

def run(args):
    config_file = bpy.path.abspath(args.config_file)
    assert os.path.exists(config_file), print("configuration file {} does not exist.".format(config_file))

    config = parse_configuration(config_file)
    validate_configuration(config)

    print("Blender Script runs")

    camera_main = get_main_camera()
    camera_input = get_input_camera()
    assert camera_main != None and camera_input != None, "There is no camera in blender file."

    body_sizes = get_body_measurements(config.body_measurement)

    print("Number of measures: ", len(body_sizes))

    for i in range(1):
        # scaler = 1 + 0.1 * i

        cloth_main = find_main_cloth()
        cloth_input = find_input_cloth()
        assert cloth_main != None and cloth_input != None, "There is no cloth object in blender file."

        count = 0
        for size in body_sizes:
            randomSize = pickRandomSize(config.min_chest, config.max_chest)
            length_variation = random.uniform(-0.1, 0.1)
            print("RandomSize: ", randomSize)
            set_cloth_size(cloth_main, randomSize, config.length_ratio, length_variation, config.cloth_prop)
            set_cloth_size(cloth_input, randomSize, config.length_ratio, length_variation, config.cloth_prop)
            save_size_info(size, cloth_main, config.cloth_prop, config.output_dir_measurement, config.cloth_type + "_" + str(count))

            print(size)
            set_body_measurement(size)
            # print("Height: ", bpy.data.window_managers['WinMan'].smplx_tool.smplx_height)
            # print("Weight: ", bpy.data.window_managers['WinMan'].smplx_tool.smplx_weight)

            # if size[1] >= 80 and size[1] < 90:
            #     y_scaler = 1.05
            # elif size[1] >= 90:
            #     y_scaler = 1.1
            # else:
            #     y_scaler = 1
            # cloth_scale[1] *= y_scaler
            # set_cloth_size(cloth, cloth_scale)

            # print("Cloth_scale: ", cloth_scale)
            render_image(config.rendering_frame, 
                        camera_main, camera_input, 
                        config.output_dir_gt, config.output_dir_input, 
                        config.cloth_type + "_" + str(count))
            # cloth_scale[1] /= y_scaler
            count += 1

#=======================================================================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file',
                        required=True,
                        help='Configuration file')

    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    run(args)


import argparse
import bpy
import json
import numpy as np
import os
import random
import sys

# proportion of chest-size and length for each type of cloths
hoodie_prop = (0.3732, 0.758)
jacket_prop = (0.3792, 0.8949)
longsleeve_prop = (0.3253, 0.9225)
shirt_prop = (0.3657, 0.9474)
tshirt_prop = (0.6639, 0.9721)

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
    config.output_dir = arguments['output_dir']
    return config

#-----------------------------------------------------------------------------------------------------------------------

def validate_configuration(config):
    clothing_type = ['hoodie', 'jacket', 'longsleeve', 'shirt', 'tshirt']
    assert config.cloth_type in clothing_type, 'Undefined cloth type {}'.format(config.cloth_type)
    
    assert os.path.exists(config.body_measurement), 'Body measurement file {} does not exist.'.format(config.body_measurement)

    if not os.path.exists(config.output_dir):
        os.makedirs(config.output_dir)

#-----------------------------------------------------------------------------------------------------------------------

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
    return body_measurements

#-----------------------------------------------------------------------------------------------------------------------

def set_body_measurement(measurement):
    # assert len(measurement) == 2, 'Wrong body parameter. It should have height and weight.'

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

def pickRandomSize(min_chest, max_chest):
    return random.uniform(min_chest, max_chest)

#-----------------------------------------------------------------------------------------------------------------------

def set_cloth_size(cloth, cloth_type:str, chest_circumference, length_ratio):
    bpy.context.scene.frame_set(0)

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

    chest_half = chest_circumference / 2 * 0.01
    length_variation = random.uniform(-0.1, 0.1)

    dimension_x = chest_half / cloth_prop[0]
    dimension_y = cloth.dimensions.y
    dimension_z = chest_circumference / length_ratio / cloth_prop[1] * 0.01

    cloth.dimensions = [dimension_x, dimension_y, dimension_z + dimension_z * length_variation]

#-----------------------------------------------------------------------------------------------------------------------

def save_size_info(size, cloth, cloth_type:str, output_dir:str, output_name:str):
    bpy.context.scene.frame_set(0)

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

def render_image(frame:int, output_dir:str, output_name:str):
    for i in range(frame + 1):
        bpy.context.scene.frame_set(i)

    bpy.context.scene.render.image_settings.file_format = 'JPEG'
    bpy.context.scene.render.filepath = os.path.join(output_dir, output_name)
    bpy.ops.render.render(write_still=True)
    
#-----------------------------------------------------------------------------------------------------------------------

def run(args):
    config_file = bpy.path.abspath(args.config_file)
    assert os.path.exists(config_file), print("configuration file {} does not exist.".format(config_file))

    config = parse_configuration(config_file)
    validate_configuration(config)

    print("Blender Script runs")

    camera = get_camera()
    assert camera != None, "There is no camera in blender file."

    body_sizes = get_body_measurements(config.body_measurement)

    print("Number of measures: ", len(body_sizes))

    for i in range(1):
        # scaler = 1 + 0.1 * i

        cloth = find_cloth()
        assert cloth != None, "There is no cloth object in blender file."

        count = 0
        for size in body_sizes:
            randomSize = pickRandomSize(config.min_chest, config.max_chest)
            print("RandomSize: ", randomSize)
            set_cloth_size(cloth, config.cloth_type, randomSize, config.length_ratio)
            save_size_info(size, cloth, config.cloth_type, config.output_dir, config.cloth_type + "_" + str(count))

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
            render_image(config.rendering_frame, config.output_dir, config.cloth_type + "_" + str(count))
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

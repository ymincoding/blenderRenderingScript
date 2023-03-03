
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
    config.gender = arguments['gender']
    config.rendering_frame = arguments['rendering_frame']
    config.pose_frame = arguments['pose_frame']
    config.length_ratio = arguments['length_ratio']
    config.min_chest = arguments['min_chest']
    config.max_chest = arguments['max_chest']
    config.cloth_prop = [arguments['chest_proportion'], arguments['length_proportion']]
    if 'longsleeve' in config.cloth_type or 'blazer' in config.cloth_type:
        config.cloth_prop.append(arguments['sleeve_proportion'])

    config.output_dir_input = os.path.join(arguments['output_dir'], 'input')
    config.output_dir_measurement = os.path.join(arguments['output_dir'], 'measurement')
    config.output_dir_gt = os.path.join(arguments['output_dir'], 'groundtruth')

    return config

#-----------------------------------------------------------------------------------------------------------------------

def validate_configuration(config):
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

def find_smplx_mesh():
    for object in bpy.data.objects:
        if 'SMPLX-mesh' in object.name:
            return object
    return None

#-----------------------------------------------------------------------------------------------------------------------

def find_smplx():
    for object in bpy.data.objects:
        if 'SMPLX' in object.name and 'mesh' not in object.name:
            return object
    return None

#-----------------------------------------------------------------------------------------------------------------------

def set_body_measurement(measurement):
    bpy.data.window_managers['WinMan'].smplx_tool.smplx_height = measurement[0]
    bpy.data.window_managers['WinMan'].smplx_tool.smplx_weight = measurement[1]
    
    smplx_mesh = find_smplx_mesh()
    assert smplx_mesh != None, "There is no smplx object in blender file."
    
    bpy.context.view_layer.objects.active = smplx_mesh
    bpy.ops.object.smplx_measurements_to_shape()

#-----------------------------------------------------------------------------------------------------------------------

def set_pose(frame):
    smplx = find_smplx()
    assert smplx != None, "There is no smplx object in blender file."
    
    bpy.context.view_layer.objects.active = smplx
    
    shoulder_angle = random.uniform(0.3, 0.7)
    hip_angle = random.uniform(0, 0.1)

    smplx.pose.bones["left_shoulder"].rotation_quaternion[3] = -shoulder_angle
    smplx.pose.bones["right_shoulder"].rotation_quaternion[3] = shoulder_angle
    smplx.pose.bones["left_hip"].rotation_quaternion[3] = hip_angle
    smplx.pose.bones["right_hip"].rotation_quaternion[3] = -hip_angle

    smplx.pose.bones["left_shoulder"].keyframe_insert(data_path="rotation_quaternion", frame=frame)
    smplx.pose.bones["right_shoulder"].keyframe_insert(data_path="rotation_quaternion", frame=frame)
    smplx.pose.bones["left_hip"].keyframe_insert(data_path="rotation_quaternion", frame=frame)
    smplx.pose.bones["right_hip"].keyframe_insert(data_path="rotation_quaternion", frame=frame)

    bpy.context.scene.frame_set(0)
    smplx.pose.bones["left_shoulder"].rotation_quaternion[3] = 0
    smplx.pose.bones["right_shoulder"].rotation_quaternion[3] = 0
    smplx.pose.bones["left_hip"].rotation_quaternion[3] = 0
    smplx.pose.bones["right_hip"].rotation_quaternion[3] = 0

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

def pickRandomClothSize(min_chest, max_chest):
    return round(random.uniform(min_chest, max_chest), 2)

#-----------------------------------------------------------------------------------------------------------------------

def pickRandomBodySize(gender):
    while True:
        if gender == 'female':
            height = round(random.gauss(1.65, 0.05), 2)
            weight = round(random.gauss(60, 10), 2)

            if height < 1.4 or height > 1.8 or weight < 40 or weight > 120:
                continue

        elif gender == 'male':
            height = round(random.gauss(1.75, 0.1), 2)
            weight = round(random.gauss(75, 10), 2)

            if height < 1.5 or height > 2 or weight < 47 or weight > 150:
                continue
        
        return [height, weight]

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

    if 'tshirt' in output_name or 'dress' in output_name:
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
    else:
        data = {'body':[
                            {
                                'height': size[0],
                                'weight': size[1]
                            }
                        ],
                'size':[
                            {
                                'chest': dimensions.x * cloth_prop[0],
                                'length': dimensions.z * cloth_prop[1],
                                'sleeve': dimensions.x * cloth_prop[2]
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
    # bpy.ops.screen.animation_manager(mode="BAKEALLFROMCACHE")
    # bpy.context.scene.frame_set(frame)

    bpy.context.scene.render.image_settings.file_format = 'PNG'

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

    cloth_main = find_main_cloth()
    cloth_input = find_input_cloth()
    assert cloth_main != None and cloth_input != None, "There is no cloth object in blender file."

    count = 0
    for i in range(2000):
        clothSize = pickRandomClothSize(config.min_chest, config.max_chest)
        print("RandomSize: ", clothSize)
        length_variation = round(random.uniform(-0.1, 0.1), 2)

        bodySize = pickRandomBodySize(config.gender)
        print(bodySize)

        set_cloth_size(cloth_main, clothSize, config.length_ratio, length_variation, config.cloth_prop)
        set_cloth_size(cloth_input, clothSize, config.length_ratio, length_variation, config.cloth_prop)
        save_size_info(bodySize, cloth_main, config.cloth_prop, config.output_dir_measurement, config.cloth_type + "_" + str(count))

        set_body_measurement(bodySize)
        set_pose(config.pose_frame)

        render_image(config.rendering_frame, 
                    camera_main, camera_input, 
                    config.output_dir_gt, config.output_dir_input, 
                    config.cloth_type + "_" + str(count))
        count += 1

#=======================================================================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file',
                        required=True,
                        help='Configuration file')

    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    run(args)

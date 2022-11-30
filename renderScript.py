
import argparse
import bpy
import os
import sys

def get_camera():
    for collection in bpy.data.collections:
        for object in collection.objects:
            if object.type == 'CAMERA':
                return object
    return None

#-----------------------------------------------------------------------------------------------------------------------

def render_image(output_dir:str):
    bpy.context.scene.frame_set(200)
    bpy.context.scene.render.image_settings.file_format = 'JPEG'
    bpy.context.scene.render.filepath = os.path.join(output_dir, 'output')
    bpy.ops.render.render(write_still=True)
    
#-----------------------------------------------------------------------------------------------------------------------

def run(args):
    print("Hello Blender Script")

    camera = get_camera()
    assert camera != None, "There is no camera in blender file."

    if not os.path.exists(args.output_dir):
        os.mkdir(args.output_dir)
    render_image(args.output_dir)

#=======================================================================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_dir', 
                        required=True, 
                        help='Output directory to save the results')
    
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    run(args)

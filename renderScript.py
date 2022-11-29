
import bpy

def get_camera():
    for collection in bpy.data.collections:
        for object in collection.objects:
            if object.type == 'CAMERA':
                return object
    return None

def render_image(output_path:str):
    bpy.context.scene.frame_set(200)
    bpy.context.scene.render.image_settings.file_format = 'JPEG'
    bpy.context.scene.render.filepath = output_path
    print("Output path: ", bpy.context.scene.render.filepath)
    bpy.ops.render.render(write_still=True)
    
#-----------------------------------------------------------------------------------------------------------------------

def run():
    print("Hello Blender Script")

    camera = get_camera()
    assert camera != None, "There is no camera in blender file."

    output_path = "D:\Yunmin\TUK\WS22_23\Thesis\src\output"
    render_image(output_path)

#=======================================================================================================================

if __name__ == "__main__":
    run()

bl_info = {
    "name": "BlenvyGreetings",
    "author": "Your Name or Team",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Blenvy Tab",
    "description": "A Blender addon for managing Bevy components",
    "category": "3D View",
}

from .registry import registry

def register():
    print("Registering BlenvyGreetings addon")
    registry.register()

def unregister():
    registry.unregister()

if __name__ == "__main__":
    register()
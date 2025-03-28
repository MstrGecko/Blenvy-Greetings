def register():
    from . import operators
    from . import panels
    operators.register()
    panels.register()

def unregister():
    from . import operators
    from . import panels
    operators.unregister()
    panels.unregister()
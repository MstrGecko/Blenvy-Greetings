from bpy.props import StringProperty

def process_unit_struct(registry, definition, update, nesting_long_names, depth=0, processed_types=None):
    long_name = definition["long_name"]
    nesting_long_names = nesting_long_names + [long_name]
    # Unit structs typically have no fields, so we return an empty annotations dict
    __annotations__ = {}
    # Optionally, add a placeholder to indicate it's a unit struct
    __annotations__["unit_struct_placeholder"] = StringProperty(default="Unit Struct")
    return __annotations__
from bpy.props import (StringProperty)
from . import process_component
import logging

def process_structs(registry, definition, properties, update, nesting_long_names, depth=0, processed_types=None):
    value_types_defaults = registry.value_types_defaults
    blender_property_mapping = registry.blender_property_mapping
    type_infos = registry.type_infos
    long_name = definition["long_name"]

    __annotations__ = {}
    default_values = {}
    nesting_long_names = nesting_long_names + [long_name]

    logging.debug(f"Processing struct {long_name} with properties: {properties}")

    # Handle empty structs
    if not properties:
        __annotations__["placeholder"] = StringProperty(default="Empty Struct")
        logging.debug(f"Generated placeholder annotations for empty struct {long_name}: {__annotations__}")
        return __annotations__

    for property_name in properties.keys():
        ref_name = properties[property_name]["type"]["$ref"].replace("#/$defs/", "")
        
        if ref_name in type_infos:
            original = type_infos[ref_name]
            original_long_name = original["long_name"]
            is_value_type = original_long_name in value_types_defaults
            value = value_types_defaults[original_long_name] if is_value_type else None
            default_values[property_name] = value

            if is_value_type:
                if original_long_name in blender_property_mapping:
                    blender_property_def = blender_property_mapping[original_long_name]
                    blender_property = blender_property_def["type"](
                        **blender_property_def["presets"],  # we inject presets first
                        name=property_name,
                        default=value,
                        update=update
                    )
                    __annotations__[property_name] = blender_property
            else:
                original_long_name = original["long_name"]
                (sub_component_group, _) = process_component.process_component(
                    registry, original, update, {"nested": True, "long_name": original_long_name},
                    nesting_long_names+[property_name]
                )
                __annotations__[property_name] = sub_component_group
        else:
            # component not found in type_infos, generating placeholder
            __annotations__[property_name] = StringProperty(default="Struct N/A")
            registry.add_missing_typeInfo(ref_name)
            registry.add_invalid_component(nesting_long_names[0])

    logging.debug(f"Generated annotations for struct {long_name}: {__annotations__}")
    return __annotations__
import json
import bpy

from .conversions_from_prop_group import property_group_value_to_custom_property_value
from .process_component import process_component
from .utils import update_calback_helper
from ..utils import get_selected_item

import logging

print("DEBUG: Loading updated prop_groups.py with logging import")

## main callback function, fired whenever any property changes, no matter the nesting level
def update_component(self, context, definition, component_name):
    registry = bpy.context.window_manager.components_registry
    
    current_object_or_collection = get_selected_item(context)
    update_disabled = current_object_or_collection["__disable__update"] if "__disable__update" in current_object_or_collection else False
    update_disabled = registry.disable_all_object_updates or update_disabled # global settings
    if update_disabled:
        return
    components_in_object = current_object_or_collection.components_meta.components
    component_meta =  next(filter(lambda component: component["long_name"] == component_name, components_in_object), None)

    if component_meta is not None:
        property_group_name = registry.get_propertyGroupName_from_longName(component_name)
        property_group = getattr(component_meta, property_group_name)
        # we use our helper to set the values
        previous = json.loads(current_object_or_collection['bevy_components'])
        previous[component_name] = property_group_value_to_custom_property_value(property_group, definition, registry, None)
        current_object_or_collection['bevy_components'] = json.dumps(previous)


def generate_propertyGroups_for_components():
    registry = bpy.context.window_manager.components_registry
    if not registry.has_type_infos():
        registry.load_type_infos()

    type_infos = registry.type_infos

    # Process types under "$defs"
    if "$defs" in type_infos:
        for type_name, definition in type_infos["$defs"].items():
            logging.debug(f"Processing $defs type: {type_name}")
            process_component(registry, definition, update_calback_helper(definition, update_component, type_name), {"nested": False}, nesting_long_names=[])

    # Process types under "components"
    if "components" in type_infos:
        for type_name, definition in type_infos["components"].items():
            logging.debug(f"Processing component type: {type_name}")
            process_component(registry, definition, update_calback_helper(definition, update_component, type_name), {"nested": False}, nesting_long_names=[])

    # If we had to add any wrapper types on the fly, process them now
    registry.process_custom_types()
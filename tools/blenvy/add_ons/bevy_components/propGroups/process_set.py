# add_ons/bevy_components/components/propGroups/process_set.py
from bpy.props import (StringProperty, IntProperty, CollectionProperty)
from .utils import generate_wrapper_propertyGroup
from . import process_component
from .process_list import extract_item_type  # Import extract_item_type from process_list.py
import logging

logging.basicConfig(level=logging.DEBUG)

def process_set(registry, definition, items, update, nesting_long_names, depth=0, processed_types=None):
    if nesting_long_names is None:
        nesting_long_names = []
    if processed_types is None:
        processed_types = set()
    
    logging.debug(f"process_set: depth={depth}, definition={definition}, nesting_long_names={nesting_long_names}")
    if depth > 10:
        logging.error(f"Maximum recursion depth exceeded: {nesting_long_names}")
        return {}

    # Validate the $ref path
    if "items" not in definition or "type" not in definition["items"] or "$ref" not in definition["items"]["type"]:
        logging.error(f"Invalid $ref structure in definition: {definition}")
        return {}
    
    value_types_defaults = registry.value_types_defaults 
    type_infos = registry.type_infos

    long_name = definition["long_name"]
    ref_name = definition["items"]["type"]["$ref"].replace("#/$defs/", "")
    
    # Check for self-referential $ref (Bevy 0.15 issue)
    if ref_name == long_name:
        # Extract the item type from long_name instead of following the $ref
        item_type = extract_item_type(long_name)
        if not item_type:
            logging.error(f"Failed to extract item type from self-referential set: {long_name}")
            return {}
        ref_name = item_type
        logging.debug(f"Self-referential $ref detected for {long_name}, extracted item type: {ref_name}")
    
    # Check for circular references
    if ref_name in processed_types:
        logging.warning(f"Circular reference detected for type {ref_name} in nesting_long_names={nesting_long_names}")
        return {}
    
    processed_types.add(ref_name)
    
    # Validate item_definition
    if ref_name not in type_infos:
        logging.error(f"Type {ref_name} not found in type_infos")
        return {}
    
    nesting_long_names = nesting_long_names + [long_name]
    
    item_definition = type_infos[ref_name]
    item_long_name = item_definition["long_name"]
    is_item_value_type = item_long_name in value_types_defaults

    property_group_class = None
    # If the content of the set is a unit type, we need to generate a fake wrapper
    if is_item_value_type:
        property_group_class = generate_wrapper_propertyGroup(long_name, item_long_name, f"#/$defs/{ref_name}", registry, update, nesting_long_names=nesting_long_names)
    else:
        (_, set_content_group_class) = process_component.process_component(registry, item_definition, update, {"nested": True, "long_name": item_long_name}, nesting_long_names=nesting_long_names, depth=depth + 1, processed_types=processed_types)
        property_group_class = set_content_group_class

    if property_group_class is None:
        logging.error(f"Failed to generate property group class for {long_name}")
        return {}

    item_collection = CollectionProperty(type=property_group_class)

    item_long_name = item_long_name if not is_item_value_type else "wrapper_" + item_long_name
    __annotations__ = {
        "set": item_collection,
        "set_index": IntProperty(name="Index for set", default=0, update=update),
        "long_name": StringProperty(default=item_long_name)
    }

    return __annotations__
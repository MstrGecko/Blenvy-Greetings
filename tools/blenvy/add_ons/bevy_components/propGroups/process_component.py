# add_ons/bevy_components/components/propGroups/process_component.py
from .process_list import process_list
from .process_set import process_set
from .process_structs import process_structs
from .process_tuples import process_tuples
from .process_unit_struct import process_unit_struct
from .process_enum import process_enums
from .utils import create_property_group_name
import bpy
import logging

print("DEBUG: Loading updated process_component.py with Tuple and Value handlers")

logging.basicConfig(level=logging.DEBUG)

def process_component(registry, definition, update, options, nesting_long_names=None, depth=0, processed_types=None):
    if nesting_long_names is None:
        nesting_long_names = []
    if processed_types is None:
        processed_types = set()

    logging.debug(f"process_component: depth={depth}, definition={definition}, nesting_long_names={nesting_long_names}")
    if depth > 10:
        logging.error(f"Maximum recursion depth exceeded in process_component: {nesting_long_names}")
        return (None, None)

    if "long_name" not in definition:
        logging.error(f"Definition missing 'long_name': {definition}")
        return (None, None)

    long_name = definition["long_name"]
    if long_name in processed_types:
        logging.warning(f"Circular reference detected in process_component for type {long_name}")
        return (None, None)

    processed_types.add(long_name)
    type_info = definition.get("typeInfo", None)

    if type_info == "Struct":
        annotations = process_structs.process_structs(registry, definition, definition.get("properties", {}), update, nesting_long_names, depth + 1, processed_types)
    elif type_info == "Enum":
        annotations = process_enums.process_enums(registry, definition, update, nesting_long_names, depth + 1, processed_types)
    elif type_info == "TupleStruct" or type_info == "Tuple":
        logging.debug(f"Processing TupleStruct/Tuple type: {long_name}")
        annotations = process_tuples.process_tuples(registry, definition, definition.get("prefixItems", []), update, nesting_long_names, depth + 1, processed_types)
    elif type_info == "List":
        annotations = process_list.process_list(registry, definition, update, nesting_long_names, depth + 1, processed_types)
    elif type_info == "Value":
        logging.debug(f"Processing Value type: {long_name}")
        annotations = {"placeholder": bpy.props.StringProperty(default="Value Type")}
        logging.debug(f"Generated annotations for Value type {long_name}: {annotations}")
    else:
        logging.error(f"Unknown typeInfo {type_info} in definition: {definition}")
        return (None, None)

    if not annotations:
        logging.warning(f"No annotations generated for {long_name}")
        return (None, None)

    # Use long_name in nesting to ensure unique property group names
    nesting = {"long_name": long_name, "nested": options.get("nested", False)}
    (property_group_pointer, property_group_class) = registry.register_component_propertyGroup(nesting, {"__annotations__": annotations})
    logging.debug(f"Registered property group for {long_name}: {property_group_pointer}")

    return (property_group_pointer, property_group_class)
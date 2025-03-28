import os
import bpy
from bpy_types import (PropertyGroup)
from bpy.props import (StringProperty, BoolProperty, FloatProperty)
from ...settings import load_settings, upsert_settings, generate_complete_settings_dict, clear_settings

from .propGroups.prop_groups import generate_propertyGroups_for_components
from .components.metadata import ensure_metadata_for_all_items
from .utils import add_component_to_ui_list

import logging

# list of settings we do NOT want to save
settings_black_list = ['settings_save_enabled', 'watcher_active']

def save_settings(settings, context):
    if settings.settings_save_enabled:
        settings_dict = generate_complete_settings_dict(settings, ComponentsSettings, [])
        print("save settings", settings, context, settings_dict)
        upsert_settings(settings.settings_save_path, {key: settings_dict[key] for key in settings_dict.keys() if key not in settings_black_list}, overwrite=True)

# helper function to deal with timer
def toggle_watcher(self, context):
    if not self.watcher_enabled:
        try:
            bpy.app.timers.unregister(watch_schema)
        except Exception as error:
            pass
    else:
        self.watcher_active = True
        bpy.app.timers.register(watch_schema)
    save_settings(self, context)

def watch_schema():
    component_settings = bpy.context.window_manager.components_settings
    reloading_registry = False
    try:
        stamp = os.stat(component_settings.schema_path_full).st_mtime
        stamp = str(stamp)
        if stamp != component_settings.schemaTimeStamp and component_settings.schemaTimeStamp != "":
            print("FILE CHANGED !!", stamp, component_settings.schemaTimeStamp)
            bpy.app.timers.register(lambda: bpy.ops.blenvy.components_registry_reload(), first_interval=1)
            component_settings.schemaTimeStamp = stamp
            reloading_registry = True

        if component_settings.schemaTimeStamp == "":
            component_settings.schemaTimeStamp = stamp
    except Exception as error:
        pass

    return component_settings.watcher_poll_frequency if component_settings.watcher_enabled else None

def register():
    print("DEBUG: Registering settings module")
    bpy.utils.register_class(ComponentsSettings)
    # Start the schema watcher if enabled
    settings = bpy.context.window_manager.components_settings
    settings.start_schema_watcher()

def unregister():
    print("DEBUG: Unregistering settings module")
    bpy.utils.unregister_class(ComponentsSettings)

class ComponentsSettings(PropertyGroup):
    settings_save_path = ".blenvy_components_settings"  # where to store data in bpy.texts
    settings_save_enabled: BoolProperty(name="settings save enabled", default=True)  # type: ignore

    schema_path: StringProperty(
        name="schema path",
        description="path to the registry schema file (relative to the assets path)",
        default="registry.json",
        update=save_settings
    )  # type: ignore

    project_root_path: StringProperty(
        name="Project Root Path",
        description="Path to the project root",
        default="..",
        update=save_settings
    )  # type: ignore

    schema_path_full: StringProperty(
        name="schema full path",
        description="full path to the registry schema file",
        get=lambda self: os.path.abspath(os.path.join(self.project_root_path, self.schema_path))
    )  # type: ignore

    watcher_enabled: BoolProperty(name="Watcher_enabled", default=True, update=toggle_watcher)  # type: ignore
    watcher_active: BoolProperty(name="Flag for watcher status", default=False)  # type: ignore

    watcher_poll_frequency: FloatProperty(
        name="watcher poll frequency",
        description="frequency (s) at which to poll for changes to the registry file",
        min=1.0,
        max=10.0,
        default=1.0,
        update=save_settings
    )  # type: ignore

    schemaTimeStamp: StringProperty(
        name="last timestamp of schema file",
        description="",
        default="",
        update=save_settings
    )  # type: ignore

    component_selector: StringProperty(
        search=add_component_to_ui_list,
        description="component selector: only components present in the registry are accepted"
    )  # type: ignore

    source_component_selector: StringProperty(
        search=add_component_to_ui_list
    )  # type: ignore

    target_component_selector: StringProperty(
        search=add_component_to_ui_list
    )  # type: ignore

    @classmethod
    def register(cls):
        print("DEBUG: Registering ComponentsSettings on WindowManager")
        bpy.types.WindowManager.components_settings = bpy.props.PointerProperty(type=cls)

    @classmethod
    def unregister(cls):
        print("DEBUG: Unregistering ComponentsSettings from WindowManager")
        # Stop the watcher if it's running
        try:
            bpy.app.timers.unregister(watch_schema)
        except Exception as error:
            pass
        # Remove the components_settings property
        if hasattr(bpy.types.WindowManager, "components_settings"):
            del bpy.types.WindowManager.components_settings

    def load_settings(self):
        settings = load_settings(self.settings_save_path)
        print("component settings", settings)
        if settings is not None:
            self.settings_save_enabled = False  # we disable auto_saving of our settings
            try:
                for setting in settings:
                    setattr(self, setting, settings[setting])
            except:
                pass
            try:
                registry = bpy.context.components_registry
                registry.load_schema()
                generate_propertyGroups_for_components()
                ensure_metadata_for_all_items()
            except:
                pass

            self.settings_save_enabled = True

    def reset_settings(self):
        for property_name in self.bl_rna.properties.keys():
            if property_name not in ["name", "rna_type"]:
                self.property_unset(property_name)
        # clear the stored settings
        clear_settings(".blenvy_components_settings")
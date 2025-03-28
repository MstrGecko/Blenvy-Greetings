use bevy::log::{debug, warn};
use bevy::reflect::serde::ReflectDeserializer;
use bevy::reflect::{Reflect, TypeRegistration, TypeRegistry, PartialReflect};
use bevy::utils::HashMap;
use ron::Value;
use serde::de::DeserializeSeed;

use super::capitalize_first_letter;

pub fn ronstring_to_reflect_component(
    ron_string: &str,
    type_registry: &TypeRegistry,
) -> Vec<(Box<dyn Reflect>, TypeRegistration)> {
    let lookup: HashMap<String, Value> = match ron::from_str(ron_string) {
        Ok(map) => map,
        Err(e) => {
            warn!("Failed to parse RON string '{}': {:?}", ron_string, e);
            return Vec::new();
        }
    };

    let mut components = Vec::new();
    for (name, value) in lookup {
        let parsed_value = match value.clone() {
            Value::String(str) => str,
            _ => match ron::to_string(&value) {
                Ok(s) => s,
                Err(e) => {
                    warn!("Failed to serialize value for '{}': {:?}", name, e);
                    continue;
                }
            },
        };

        if name == "bevy_components" {
            bevy_components_string_to_components(&parsed_value, type_registry, &mut components);
        } else {
            components_string_to_components(&name, value, &parsed_value, type_registry, &mut components);
        }
    }
    components
}

fn components_string_to_components(
    name: &str,
    value: Value,
    parsed_value: &str,
    type_registry: &TypeRegistry,
    components: &mut Vec<(Box<dyn Reflect>, TypeRegistration)>,
) {
    let type_string = name.replace("component: ", "").trim().to_string();
    let capitalized_type_name = capitalize_first_letter(&type_string);

    if let Some(type_registration) = type_registry.get_with_short_type_path(&capitalized_type_name) {
        let ron_string = format!(
            "{{ \"{}\": {} }}",
            type_registration.type_info().type_path(),
            parsed_value
        );
        warn!("Component data RON string: {}", ron_string);

        let mut deserializer = match ron::Deserializer::from_str(&ron_string) {
            Ok(deserializer) => deserializer,
            Err(e) => {
                warn!("Failed to create deserializer for '{}': {:?}", name, e);
                return;
            }
        };

        let reflect_deserializer = ReflectDeserializer::new(type_registry);
        match reflect_deserializer.deserialize(&mut deserializer) {
            Ok(component) => {
                if let Ok(component_reflect) = component.try_into_reflect() {
                    components.push((component_reflect, type_registration.clone()));
                    debug!("Successfully registered component '{}'", capitalized_type_name);
                } else {
                    warn!("Component '{}' lacks FromReflect or type mismatch", capitalized_type_name);
                }
            }
            Err(e) => warn!("Failed to deserialize component '{}': {:?}", name, e),
        }
    } else {
        warn!("No type registration for '{}'", capitalized_type_name);
    }
}

fn bevy_components_string_to_components(
    parsed_value: &str,
    type_registry: &TypeRegistry,
    components: &mut Vec<(Box<dyn Reflect>, TypeRegistration)>,
) {
    let lookup: HashMap<String, Value> = match ron::from_str(parsed_value) {
        Ok(map) => map,
        Err(e) => {
            warn!("Failed to parse bevy_components RON: {:?}", e);
            return;
        }
    };

    for (key, value) in lookup {
        let parsed_value = match value {
            Value::String(str) => str,
            _ => match ron::to_string(&value) {
                Ok(s) => s,
                Err(e) => {
                    warn!("Failed to serialize value for '{}': {:?}", key, e);
                    continue;
                }
            },
        };

        if let Some(type_registration) = type_registry.get_with_type_path(&key) {
            let ron_string = format!(
                "{{ \"{}\": {} }}",
                type_registration.type_info().type_path(),
                parsed_value
            );
            warn!("Component data RON string: {}", ron_string);

            let mut deserializer = match ron::Deserializer::from_str(&ron_string) {
                Ok(deserializer) => deserializer,
                Err(e) => {
                    warn!("Failed to create deserializer for '{}': {:?}", key, e);
                    continue;
                }
            };

            let reflect_deserializer = ReflectDeserializer::new(type_registry);
            match reflect_deserializer.deserialize(&mut deserializer) {
                Ok(component) => {
                    if let Ok(component_reflect) = component.try_into_reflect() {
                        components.push((component_reflect, type_registration.clone()));
                        debug!("Successfully registered component '{}'", key);
                    } else {
                        warn!("Component '{}' lacks FromReflect or type mismatch", key);
                    }
                }
                Err(e) => warn!("Failed to deserialize component '{}': {:?}", key, e),
            }
        } else {
            warn!("No type registration for '{}'", key);
        }
    }
}
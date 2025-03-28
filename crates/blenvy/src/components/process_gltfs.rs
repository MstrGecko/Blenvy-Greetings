use bevy::{
    core::Name,
    ecs::{
        entity::Entity,
        query::{Added, Without},
        reflect::{AppTypeRegistry, ReflectComponent},
        world::World,
    },
    gltf::{GltfExtras, GltfMeshExtras, GltfSceneExtras, GltfMaterialExtras},
    hierarchy::Parent,
    log::{debug, warn},
    reflect::{Reflect, PartialReflect, TypeRegistration},
    utils::HashMap,
};
use crate::{ronstring_to_reflect_component, GltfProcessed};

fn find_entity_components(
    entity: Entity,
    name: Option<&Name>,
    parent: Option<&Parent>,
    reflect_components: Vec<(Box<dyn Reflect>, TypeRegistration)>,
    entity_components: &HashMap<Entity, Vec<(Box<dyn Reflect>, TypeRegistration)>>,
) -> (Entity, Vec<(Box<dyn Reflect>, TypeRegistration)>) {
    let mut target_entity = entity;
    if let Some(parent) = parent {
        if let Some(name) = name {
            if name.as_str().contains("components") || name.as_str().ends_with("_pa") {
                debug!("adding components to parent");
                target_entity = parent.get();
            }
        }
    }
    debug!("adding to {:?}", target_entity);

    if let Some(current_components) = entity_components.get(&target_entity) {
        let mut updated_components = Vec::with_capacity(current_components.len() + reflect_components.len());
        for (component, type_registration) in current_components {
            let cloned_partial = component.clone_value();
            if let Ok(cloned) = cloned_partial.try_into_reflect() {
                updated_components.push((cloned, type_registration.clone()));
            } else {
                warn!("Failed to clone component for entity {:?}", target_entity);
            }
        }
        for (component, type_registration) in reflect_components {
            let cloned_partial = component.clone_value();
            if let Ok(cloned) = cloned_partial.try_into_reflect() {
                updated_components.push((cloned, type_registration));
            } else {
                warn!("Failed to clone new component for entity {:?}", target_entity);
            }
        }
        (target_entity, updated_components)
    } else {
        (target_entity, reflect_components)
    }
}

pub fn add_components_from_gltf_extras(world: &mut World) {
    let type_registry = world.resource::<AppTypeRegistry>().clone();
    let type_registry = type_registry.read();

    let mut entity_components: HashMap<Entity, Vec<(Box<dyn Reflect>, TypeRegistration)>> = HashMap::new();

    let mut extras = world.query_filtered::<(Entity, Option<&Name>, &GltfExtras, Option<&Parent>), (Added<GltfExtras>, Without<GltfProcessed>)>();
    let mut scene_extras = world.query_filtered::<(Entity, Option<&Name>, &GltfSceneExtras, Option<&Parent>), (Added<GltfSceneExtras>, Without<GltfProcessed>)>();
    let mut mesh_extras = world.query_filtered::<(Entity, Option<&Name>, &GltfMeshExtras, Option<&Parent>), (Added<GltfMeshExtras>, Without<GltfProcessed>)>();
    let mut material_extras = world.query_filtered::<(Entity, Option<&Name>, &GltfMaterialExtras, Option<&Parent>), (Added<GltfMaterialExtras>, Without<GltfProcessed>)>();

    for (entity, name, extra, parent) in extras.iter(world) {
        warn!("Gltf Extra: Name: {:?}, entity {:?}, parent: {:?}, extras {:?}", name, entity, parent, extra);
        let reflect_components = ronstring_to_reflect_component(&extra.value, &type_registry);
        let (target_entity, updated_components) = find_entity_components(entity, name, parent, reflect_components, &entity_components);
        entity_components.insert(target_entity, updated_components);
    }

    for (entity, name, extra, parent) in scene_extras.iter(world) {
        warn!("Gltf Scene Extra: Name: {:?}, entity {:?}, parent: {:?}, scene_extras {:?}", name, entity, parent, extra);
        let reflect_components = ronstring_to_reflect_component(&extra.value, &type_registry);
        let (target_entity, updated_components) = find_entity_components(entity, name, parent, reflect_components, &entity_components);
        entity_components.insert(target_entity, updated_components);
    }

    for (entity, name, extra, parent) in mesh_extras.iter(world) {
        debug!("Gltf Mesh Extra: Name: {:?}, entity {:?}, parent: {:?}, mesh_extras {:?}", name, entity, parent, extra);
        let reflect_components = ronstring_to_reflect_component(&extra.value, &type_registry);
        let (target_entity, updated_components) = find_entity_components(entity, name, parent, reflect_components, &entity_components);
        entity_components.insert(target_entity, updated_components);
    }

    for (entity, name, extra, parent) in material_extras.iter(world) {
        debug!("Name: {:?}, entity {:?}, parent: {:?}, material_extras {:?}", name, entity, parent, extra);
        let reflect_components = ronstring_to_reflect_component(&extra.value, &type_registry);
        let (target_entity, updated_components) = find_entity_components(entity, name, parent, reflect_components, &entity_components);
        entity_components.insert(target_entity, updated_components);
    }

    for (entity, components) in entity_components {
        if !components.is_empty() {
            debug!("--entity {:?}, components {}", entity, components.len());
        }
        let mut entity_mut = world.entity_mut(entity);
        for (component, type_registration) in components {
            debug!(
                "------adding {} {:?}",
                component.get_represented_type_info().unwrap().type_path(),
                component
            );
            if let Some(reflected_component) = type_registration.data::<ReflectComponent>() {
                reflected_component.insert(&mut entity_mut, &*component.as_partial_reflect(), &type_registry);
            } else {
                warn!(?component, "unable to reflect component");
            }
            entity_mut.insert(GltfProcessed);
        }
    }
}
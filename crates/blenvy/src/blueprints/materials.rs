use bevy::prelude::*;

// Configuration resource for caching materials
#[derive(Resource, Default)]
pub struct BlenvyMaterialConfig {
   pub materials_cache: std::collections::HashMap<String, Handle<StandardMaterial>>,
}

// Component to mark entities with material info
#[derive(Reflect, Component, Default)]
#[reflect(Component)]
pub struct MaterialInfos(Vec<MaterialInfo>);

#[derive(Reflect, Component, Default)]
#[reflect(Component)]
pub struct MaterialInfo {
    path: String,
    name: String,
}

// Component to mark entities that have had materials processed
#[derive(Component)]
pub(crate) struct MaterialProcessed;

pub(crate) fn inject_materials(
    mut blenvy_config: ResMut<BlenvyMaterialConfig>,
    material_infos_query: Query<(Entity, &MaterialInfos, &Children), Without<MaterialProcessed>>,
    with_materials_and_meshes: Query<Entity, (With<Parent>, With<MeshMaterial3d<StandardMaterial>>, With<Mesh3d>)>,
    assets_gltf: Res<Assets<Gltf>>,
    asset_server: Res<AssetServer>,
    mut commands: Commands,
) {
    for (entity, material_infos, children) in material_infos_query.iter() {
        for (material_index, material_info) in material_infos.0.iter().enumerate() {
            let material_full_path = format!("{}#{}", material_info.path, material_info.name);
            let material_found = if let Some(material) = blenvy_config.materials_cache.get(&material_full_path) {
                debug!("Material is cached, retrieving");
                Some(material.clone())
            } else {
                let model_handle: Handle<Gltf> = asset_server.load(material_info.path.clone());
                match assets_gltf.get(model_handle.id()) {
                    Some(mat_gltf) => match mat_gltf.named_materials.get(material_info.name.as_str()) {
                        Some(material) => {
                            blenvy_config.materials_cache.insert(material_full_path, material.clone());
                            Some(material.clone())
                        }
                        None => {
                            warn!("Material {} not found in GLTF {}", material_info.name, material_info.path);
                            None
                        }
                    },
                    None => {
                        warn!("GLTF asset {} not loaded; ensure preloading", material_info.path);
                        None
                    }
                }
            };

            if let Some(material) = material_found {
                info!("Injecting/replacing materials");
                for (child_index, child) in children.iter().enumerate() {
                    if child_index == material_index && with_materials_and_meshes.contains(*child) {
                        info!("Injecting material {}, path: {:?}", material_info.name, material_info.path);
                        // Updated line: Replace MeshMaterial3d<StandardMaterial> with the new material handle
                        commands.entity(*child).insert(MeshMaterial3d(material.clone()));
                    }
                }
            }
        }
        commands.entity(entity).insert(MaterialProcessed);
    }
}
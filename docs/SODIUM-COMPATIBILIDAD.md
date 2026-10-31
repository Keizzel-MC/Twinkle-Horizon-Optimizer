# Comparativa técnica con Sodium (Fabric/NeoForge) y Horizon

**Este mod NO es Sodium y no pretende ser un puerto funcionalmente equivalente.**
Sodium es un motor de renderizado Java/OpenGL profundamente integrado con Minecraft;
Horizon es un motor cliente distinto, escrito en Rust y construido con `wgpu`.
No es viable prometer que todos los componentes de Sodium funcionarán como un
`.hnmod` sin modificar directamente el motor y sin pruebas A/B de rendimiento.

## Lo que ya implementa Horizon de forma nativa

| Área | Estado en Horizon | Referencia | ¿Lo cambia Twinkle? |
|---|---|---|---|
| Mallas de chunks, eliminación de caras ocultas y vértices compactos | Implementado | `crates/horizon-client-render/src/mesher.rs` | No |
| Culling de secciones por frustum / visibilidad de cuevas | Implementado | `gfx/resident.rs`, `gfx/occlusion.rs` | No |
| Culling GPU en dos fases (según backend/hardware) | Implementado | `gfx/cull.rs` | No |
| Batching de draw calls por página y distancia | Implementado | `gfx/page_runs.rs` | Añade fastpath de listas ya ordenadas |
| Ordenamiento de transparencias por distancia | Implementado | `gfx/translucency.rs` | Añade fastpath de 0-2 quads |
| Carga, iluminación y generación de mallas en workers | Implementado | `streaming.rs` | No |
| Arenas de memoria GPU y reúso de rangos | Implementado | `gfx/arena.rs` | No |
| Ajustes de calidad, culling, FPS, pacing y overlay | Implementado | `docs/graphics.md` | No |
| LOD de terreno lejano | Implementado (no es una característica universal de Sodium) | `lod.rs` | No |

## Optimizaciones realmente implementadas por este paquete

1. `PageRuns::regroup`: salto de ordenamiento estable y copia de buffers si la lista
   ya está ordenada por la clave completa banda-página (CPU; no cambia píxeles).
2. `Column::bounds`: cálculo del mínimo y máximo de Y en una sola pasada (CPU;
   afecta mantenimiento de residencia de chunks, no reconstrucción de mallas).
3. `Sorter::sort`: ordenación de 0-2 quads transparentes sin sort genérico,
   preservando semántica de `f32::total_cmp` y orden estable (CPU).

## No implementado / no prometido

- Reemplazo íntegro del motor de renderizado por el de Sodium.
- Compatibilidad con `.jar` de Sodium, Fabric, Forge o NeoForge.
- Port de GL/OpenGL de Sodium a Vulkan/Metal/DX12/wgpu.
- Algoritmos de Sodium cuyo código requiera adaptaciones de licencia.
- Compatibilidad garantizada con shaders/mods externos.
- Mejora garantizada de FPS o consumo de RAM; depende de cargas y hardware.
- Rendimiento medido dentro de Horizon (aún no hay una compilación y benchmark A/B verificables).

## Riesgos de rendimiento

- En listas de páginas **desordenadas**, la ruta original sigue ejecutándose;
  el reemplazo añade una comprobación O(n), de modo que **puede empeorar** ligeramente.
- El beneficio de los otros dos fastpaths será mínimo o inexistente si casi nunca
  aparecen sus casos de uso.
- Dos inyecciones `OVERWRITE` pueden entrar en conflicto con otros mods que
  sobrescriban exactamente las mismas funciones. Exigen revisión exacta.

Solo un benchmark reproducible justifica decir que este proyecto es «más rápido».

# Twinkle Horizon Optimizer 0.2.1 — adaptación a `aa27eca`

**Para la Nightly Horizon 2026-10-31 · `aa27eca326db26e999d4e59d7899576016764b1e`.**

Esta entrega es un **paquete fuente nativo `.hnmod`**, no un ejecutable Windows compilado. Contiene tres optimizaciones conservadoras del renderizador, pruebas de equivalencia, el benchmark **original** proporcionado por el usuario y una tarea de GitHub Actions para intentar compilarlo contra el cliente auténtico de Horizon. **No se ha comprobado todavía que el mod compile o se ejecute con éxito dentro del juego**; no se anuncian FPS adicionales.

## Qué optimiza

| Cambio | Método interno de Horizon | Objetivo |
|---|---|---|
| PageRuns sorted fast path | `gfx::page_runs::PageRuns::regroup` | Evitar copias/ordenamientos si la lista de draws ya respeta el orden de las bandas y páginas |
| Column bounds | `gfx::resident::Column::bounds` | Calcular el mínimo/máximo Y en un solo recorrido |
| Tiny translucency | `gfx::translucency::Sorter::sort` | Resolver 0–2 quads con una comparación, evitando el sort general |

No modifica la interfaz de Minecraft, no toca archivos de usuario, no conecta a servicios externos, no recopila telemetría y no incorpora el código de Sodium. Horizon ya incluye muchas técnicas de Sodium; esto **no es un port de Sodium completo**.

## ¿Por qué cambia de versión?

Los SHA-1 Git de los tres archivos del renderizador de `aa27eca` **coinciden exactamente** con los de la revisión `9d979caa48a3bb58203319b9ea044db58c38e0d8`, usada en el proyecto anterior. El nuevo paquete fija la **revisión completa** que muestra el benchmark Vanilla del usuario. El método exacto de comprobación está en `tools/verify_source.py` y `source-lock.json`. El pin no implica que el proyecto entero sea idéntico, ni garantiza que compile: las otras partes de Horizon podrían haber cambiado.

## Archivos principales

- `twinkle_opt-0.2.1.hnmod`: ZIP de código fuente para mods nativos (no es un DLL ni EXE).
- `native/twinkle_opt/mixins/twinkle_opt/`: manifiesto TOML y 3 helpers Rust.
- `validation_rust/`: tests Rust que incluyen los mismos archivos de helpers con modelos mínimos.
- `.github/workflows/verify.yml`: prueba Rust y construcción completa contra Horizon en GitHub Actions (Linux); **se inicia solo manualmente** para no gastar CI por accidente.
- `benchmarks/vanilla-aa27eca-standard.json`: benchmark base suministrado por el usuario, **1 ejecución** por escena. No prueba ningún aumento del mod.
- `tools/aggregate_benchmarks.py`: agrega tres o más ejecuciones independientes del benchmark en un reporte con 3+ repeticiones, comprobando que las condiciones coinciden.
- `tools/compare_benchmarks.py`: compara las muestras de ambos casos solo con mismas condiciones, 3+ repeticiones por escena.
- `ESTADO-DE-ENTREGA.md`: lista de comprobaciones pendientes y realizadas.

## 1. Tests de los algoritmos (sin Minecraft)

Necesitas Python 3.11 o superior:

```sh
python3 tools/check_all.py
```

Esto prueba equivalencia entre algoritmos independientes del renderizador con casos aleatorios y excepcionales, verifica los manifiestos y reproduce el ZIP byte a byte. **No compila el juego**.

Para probar los mismos helpers con Rust, se necesita Rust/Cargo:

```sh
cargo test --manifest-path validation_rust/Cargo.toml
```

## 2. Compilación completa en GitHub Actions

Sube el contenido del proyecto a un repositorio propio (no el código de Minecraft). En GitHub abre **Actions → Verificar Twinkle Horizon Optimizer aa27eca → Run workflow**. El trabajo `verify-sources` instala Rust, ejecuta las pruebas, descarga la revisión original de Horizon y comprueba la integridad. Si pasa, `compile-horizon-linux` ejecuta las herramientas upstream `native.py check` y `native.py build` contra esa revisión. La compilación puede consumir bastantes minutos y recursos de GitHub Actions. **No se ha ejecutado ni pasado en esta entrega**. Aunque pase Linux, Windows sigue pendiente de prueba.

Herramientas upstream fijadas:
- Horizon: `aa27eca326db26e999d4e59d7899576016764b1e`.
- horizon-mixins: `0d6b103c70633d8fd9443d8d0acd3aadaacedb06`.
- horizon-mods: `f7709827f6c43d4c2e79c7fa39c1a31e44560b50`.

## 3. Posible prueba en Windows (solo después de validar la compilación)

El launcher documenta `horizon-launcher native-build [FOLDER]`, que compila las modificaciones nativas en un juego aparte. No necesita ejecutar la herramienta `.hnmod` como EXE, pero la compilación de Rust es real. Descomprime el `.hnmod` en una carpeta segura y revisa sus archivos. **No uses la opción de confiar en código nativo que no hayas examinado**: los mods nativos no están aislados y tienen los permisos de tu usuario. Tampoco desactives Defender si señala una amenaza.

**No hagas esta prueba todavía** hasta ver el resultado de GitHub Actions y verificar que la Nightly coincida. Un bundle `.hnmod` no compilado todavía puede contener errores de tipado o AST.

## 4. Línea base original y comparación de FPS

El informe `benchmarks/vanilla-aa27eca-standard.json` contiene una ejecución de cada escenario: aldea **1031.379 FPS**, bosque **1017.067 FPS**, océano **1188.022 FPS**, montaña **1079.440 FPS**. La media aritmética no ponderada de las cuatro escenas es **1078.977 FPS**. Entorno: 1920×1080, 16 chunks, simulación 12, Vulkan, VSync desactivado, RTX 4060. Su promedio no indica lo que aportaría Twinkle.

El benchmark integrado crea/sobrescribe únicamente el mundo especial `horizon-benchmark` cuando contiene su marca. Para obtener 3 mediciones independientes (en un entorno **comprobado**), repetir este comando tres veces y conservar los tres JSON distintos:

```powershell
.\horizon-launcher.exe play --version nightly-2026-10-31-aa27eca --arg=--benchmark --arg=standard --arg=--render-distance --arg=16
```

Después de disponer de **tres resultados sin mod** y **tres con mod** (algunos cambios podrían resultar más lentos), agrupar y comparar:

```sh
python3 tools/aggregate_benchmarks.py base-3.json base-1.json base-2.json base-3-original.json
python3 tools/aggregate_benchmarks.py mod-3.json mod-1.json mod-2.json mod-3-original.json
python3 tools/compare_benchmarks.py base-3.json mod-3.json
```

Los reportes individuales usan condiciones idénticas salvo el programa modificado (el agregado comprueba versión de la aplicación solo **dentro** del grupo). No confundas variaciones normales con ganancias demostradas.

## Avisos de seguridad y licencia

- Los mods `.hnmod` son **código nativo de confianza**, no plugins sandboxed. Revisar antes de compilar.
- Las advertencias del antivirus no deben ignorarse; usar fuentes oficiales y no desactivar las protecciones.
- Horizon: licencia MIT y reconocimiento en `THIRD_PARTY_NOTICES.md`.
- Sodium: se estudian ideas de optimización, **sin copiar su código**.
- No incluyas artefactos del Minecraft original, `saves`, `session.json`, tokens o mundos en un repositorio público.

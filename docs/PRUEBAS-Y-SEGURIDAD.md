# Informe de validación y seguridad

## Validado en el entorno de preparación

- Comparación de PageRuns optimizado frente a comportamiento fijado de Horizon:
  entradas vacías, una sección, páginas iguales, banda y página mezcladas,
  duplicados, límites de u64, prefijos/sufijos y 30.000 casos aleatorios.
- Comparación de `Column::bounds` con los dos recorridos originales:
  extremos de i32, columnas vacías y 30.000 casos aleatorios.
- Comparación de `Sorter::sort` para 0-2 quads y fallback para más:
  NaN, infinidades, empate, +0/-0 y 30.000 casos aleatorios más 10.000 casos con 3-29 quads.
- Manifiesto `.hnmod`, rutas internas del ZIP, hashes, inyecciones y
  empaquetado determinista comprobados por unittest.
- Código de los helpers revisado estáticamente para ausencia de acceso a
  red, procesos externos, filesystem y bloques `unsafe`.

**No son pruebas de compatibilidad ejecutada con el juego**. Los tests de
Python modelan el algoritmo; el harness Rust real se ha escrito, pero no
se ha ejecutado en este entorno por falta de `rustc` y `cargo`.

## Pendiente antes de una distribución como mod funcional

1. `cargo test --manifest-path validation_rust/Cargo.toml`
2. Descargar y verificar exactamente la revisión fijada con `verify_source.py`.
3. `native.py check twinkle_opt` con el horizonte fijado, sin `--horizon latest`.
4. `native.py build twinkle_opt` para generar el juego con el mod aplicado.
5. Inspeccionar el resultado, sin eludir alarmas del antivirus.
6. Benchmark de juego real A/B con el JSON oficial de Horizon y al menos 3 repeticiones.
7. Comprobar artefactos en Windows, Linux y, si es viable, macOS.

## Precauciones de seguridad

- No requiere ejecutar ni instalar un binario de Horizon en tu PC para inspeccionar
  este proyecto; puedes revisar los `.rs`, `.toml`, `.py` y `.json`.
- Un mod `.hnmod` es código nativo de origen que el launcher compila e integra en
  un ejecutable con permisos del usuario. Nunca es un contenedor aislado.
- El `.hnmod` incluido está **sin compilar ni validar contra Horizon**.
- No deshabilites el antivirus para probarlo.
- La detección de un antivirus sobre Horizon no queda resuelta al usar este mod.
- No se descargan bibliotecas externas dentro de los helpers Rust.


## Corrección 0.2.2

En la ejecución #1 de GitHub Actions, el planificador de `horizon-mixins` rechazó `PageRuns::regroup` por `E_UNSUPPORTED_CONTROL_FLOW` (closures en la función original). La revisión 0.2.2 conserva solo el hook HEAD de `Column::bounds`; los otros algoritmos permanecen solo como investigación y pruebas, no en el `.hnmod`. La compilación de esta revisión aún está pendiente.

# Estado verificable — adaptación para Horizon aa27eca

- Mod: Twinkle Horizon Optimizer 0.2.1, **fuentes Rust**, no ejecutable compilado.
- Horizon exacto: `aa27eca326db26e999d4e59d7899576016764b1e` (Nightly 2026-10-31).
- `page_runs.rs`, `resident.rs` y `translucency.rs` coinciden byte a byte a nivel Git blob con el commit previo del prototipo (ver `source-lock.json`).
- Inyecciones: 3, basadas en los métodos privados de Horizon, no en su API estable de hooks.
- El informe suministrado por el usuario se incluye en `benchmarks/vanilla-aa27eca-standard.json`. Es de **una sola ejecución** por escenario, por lo que sirve de línea base, no de demostración de mejora.
- Ejecutar `python3 tools/check_all.py` para pruebas de algoritmos/paquetización.
- Ejecutar `cargo test --manifest-path validation_rust/Cargo.toml` para pruebas con helpers Rust reales.
- Ejecutar el flujo `.github/workflows/verify.yml` de GitHub Actions para intentar `cargo check` y `cargo build` del cliente Horizon con los mixins.
- **Sin una compilación satisfactoria y pruebas dentro del juego, este paquete no debe anunciarse como estable ni como mejora demostrada de FPS**.
- Nunca eludir alertas del antivirus para probarlo; los mods nativos tienen permisos completos del usuario.

## Resultado de pruebas ejecutadas en este entorno

- `python3 tools/check_all.py`: **27 pruebas PASS** (26.419 segundos); ver `logs/pruebas-aa27eca-0.2.1.log`.
- Paquete `.hnmod` generado 2 veces y comparado byte a byte: **idéntico**.
- SHA256 `.hnmod`: `eb954c0eae3daea8802161ba26440c247528b68bc920b46afa8e1581b4ea5749`.
- Paquete ZIP final: verificado al generarse.
- `cargo` / `rustc`: **no instalados**. Sin pruebas de compilación reales.
- GitHub Actions: **no ejecutado** (requiere un repositorio y un disparo manual).
- Juego real y mejora de FPS: **no probados**.

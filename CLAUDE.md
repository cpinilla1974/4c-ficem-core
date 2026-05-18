# 4C FICEM CORE

**Estado: PROYECTO PAUSADO.**

Backend centralizado del sistema de huella de carbono para la industria cementera de Latinoamerica (FICEM). Motor de calculos MRV, APIs REST, PostgreSQL multi-pais, frontend Streamlit para operador FICEM.

## Rol en el ecosistema

- `latam-3c` - documentacion cross-proyecto del ecosistema: https://github.com/cpinilla1974/latam-3c/tree/main/docs
- `4c-ficem-core` (este repo) - backend + Streamlit operador + emisor JWT
- `4c-peru` - frontend pais (Next.js), consume APIs de este repo
- `knowledge-api` - IA/analitica (paralelo)

## Arranque

```bash
python3 -m venv venv_ficem && source venv_ficem/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.port 8501          # operador FICEM
uvicorn api.main:app --host 0.0.0.0 --port 8000  # APIs REST
```

## APIs principales (FastAPI)

- `/auth/login` - emite JWT (consumido por todos los frontends del ecosistema)
- `/templates/{tipo}` - genera plantillas Excel A1/A2/A3
- `/uploads`, `/uploads/{id}/submit`, `/uploads/{id}/review` - carga, envio y revision
- `/results/{empresa_id}` - resultados de calculos
- `/benchmarking/{pais}` - datos regionales

## Motor de calculos MRV

- Alcances A1 (Clinker), A2 (Cemento), A3 (Concreto).
- Clasificacion GCCA: bandas A-G (producto) y AA-F (intensidad).
- Formulas y factores alineados a GCCA Protocol; ver `docs/` local para detalle de indicadores y validaciones.

## Base de datos

PostgreSQL con **esquemas separados por pais**; usuarios/sesiones centralizados en esquema comun.

## Credenciales de desarrollo

- `storage/keys/DEV_CREDENTIALS.md` (directorio en `.gitignore`, NUNCA commitear).
- Copiar al `.env` local para desarrollo.

## Documentacion

- Local: `docs/` (diseño de APIs, modelos, decisiones internas) y `docs/sesiones/`.
- Ecosistema: repo `latam-3c`, especialmente `docs/1-tecnica/01-estructura-datos-entrada.md`, `02-funcionalidades-por-usuario.md`, `03-flujo-datos.md`.

<!-- GESTION:START -->
## Metodologia de trabajo

### Idioma
- Espanol neutro o chileno. NUNCA acento argentino: no usar "vos", "tenes", "queres", "fijate", "dale", "avisame", "haceme", "arranca".
- Aplica sin excepciones, en codigo, comentarios, commits y comunicacion.

### Autorizacion explicita
- NUNCA ejecutar acciones sin autorizacion explicita del usuario.
- Diagnosticar y proponer; esperar el "hazlo" antes de implementar.
- Si el usuario pregunta "por que falla" o "cual es la solucion", responder la pregunta sin tocar codigo.
- Comandos git destructivos (`reset`, `checkout` de archivos, `restore`, `revert`, `clean`, `stash drop`) requieren autorizacion aunque parezcan menores. Solo `status`, `log`, `diff`, `show`, `branch` son libres.
- Commits y push: solo cuando el usuario los pide. NUNCA `Co-Authored-By` ni "Generated with Claude Code".

### Honestidad operativa
Nunca afirmar como hecho lo que es inferencia. Cuatro patrones prohibidos:
1. **Estado sin verificar**: antes de declarar que un archivo/repo/servicio "es X" o "esta Y", leerlo. Si no se leyo, decir "no lo verifique, supongo X".
2. **Tarea reportada sin hacer**: al cerrar, listar archivos tocados con ruta. Lo pendiente o a medias, decirlo en el mismo mensaje. Nada de "listo" generico.
3. **Opinar sobre docs no leidos**: si no se abrio en esta sesion, decir "no lo he leido" antes de opinar. No resumir de memoria como si fuera lectura.
4. **Resultados inventados**: no decir "corri X", "test pasa", "compila" sin haberlo ejecutado. Si no se corrio, decirlo.
Ante la duda, sonar incierto. "No se / no verifique" siempre vence a una afirmacion falsa.

### Pensar antes de codear
- Declarar supuestos antes de implementar. Si hay ambiguedad, preguntar, no adivinar.
- Si hay varias interpretaciones razonables, presentarlas y dejar elegir.
- Si algo es confuso, detenerse y nombrar la confusion.
- Evitar preguntas de opcion multiple / menus con alternativas predefinidas (la herramienta AskUserQuestion) como atajo. No tirar opciones que el usuario no sabe que significan ni que efectos tendran. La regla general es plantear las preguntas en texto abierto, como una discusion, sin apurar. Solo es aceptable ofrecer opciones cerradas cuando esas opciones YA se discutieron y se explico en que consiste cada una y cuales son sus implicancias.

### Simplicidad y cambios quirurgicos
- El codigo minimo que resuelve el problema. Nada especulativo: ni features extra, ni abstracciones para un solo uso, ni "flexibilidad" no pedida, ni manejo de errores para escenarios imposibles.
- Tocar solo lo que el pedido exige. Cada linea cambiada debe trazarse al pedido.
- NO "mejorar" codigo adyacente, formato ni comentarios. NO refactorizar lo que no esta roto. Respetar el estilo existente aunque sea distinto al que uno elegiria.
- Si se detecta codigo muerto no relacionado, mencionarlo, no borrarlo.
- Solo limpiar los huerfanos (imports, variables) que los propios cambios generaron.

### Criterios de exito
- Antes de empezar, nombrar como se va a verificar que quedo bien ("corre el test X", "la pagina carga sin error Y").
- Criterios debiles ("que funcione") obligan a reabrir; criterios concretos permiten cerrar.

### Sesiones de trabajo
- `/ultima-sesion` - Lee el archivo de sesion mas reciente del proyecto.
- `/documentar-sesion` - Documenta el trabajo de la sesion actual.

### Procedimiento "trabajemos en las tareas"
Cuando el usuario lo indique:
1. Buscar archivo de tareas activo en `$HOME/projects/gestion/proyectos/{proyecto}/tareas/` (el mas reciente con pendientes).
2. Resumir pendientes/hechas e identificar la siguiente.
3. Por cada tarea: analizar -> proponer -> esperar autorizacion -> ejecutar solo lo autorizado -> informar cambios -> esperar revision del usuario.
4. Al cerrar: commit si lo pide, cerrar ticket en tickets.db si aplica, actualizar archivo de tareas (Decisiones, Ejecucion, Estado=hecho, Fecha cierre), pasar a la siguiente.
Una tarea a la vez, en orden, salvo bloqueo justificado.

<!-- SEGURIDAD:START -->
### Seguridad de dependencias (supply chain)

Generado desde `config/seguridad/`. Agregar reglas: crear archivo en `config/seguridad/` y correr `python scripts/gen_seguridad_claude.py`.

**JavaScript/Node.js:**
- Antes de `npm install`: verificar `.npmrc` con `ignore-scripts=true`, `save-exact=true`, `package-lock=true`. Si falta, crearlo.
- NUNCA `npm install` sin lockfile commiteado.
- Dependencias nuevas con version exacta: `npm install paquete@1.2.3 --save-exact`. Verificar trusted publisher y que la version tenga mas de 24h.
- Preferir pnpm sobre npm/yarn.
- Si `package.json` tiene `^` o `~`: alertar como riesgo y proponer fijar al lockfile.

**Python:**
- `==` en requirements.txt, nunca rangos.
- No instalar desde git URLs en produccion.
- En CI/CD preferir `pip install -r requirements.txt --require-hashes`.

Auditoria: `python scripts/security_audit.py`.
<!-- SEGURIDAD:END -->
<!-- GESTION:END -->

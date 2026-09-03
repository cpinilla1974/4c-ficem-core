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

### Forma de responder
- **La meta: que el usuario entienda en la primera lectura, leyendo lo menos posible.** Las dos mitades importan. Si tiene que pedir la explicacion de nuevo, la respuesta fallo aunque haya sido corta: cinco repreguntas cuestan mucho mas que diez lineas bien escritas. Y si le llega una parrafada, se irrita antes de leerla, porque sabe que hay cinco lineas utiles entre el relleno. La salida no es escribir mas largo, es escribir mejor: cada linea tiene que ser informacion util.
- **Borrar el relleno, no el contenido.** El error a no repetir es comprimir borrando las definiciones y el para que, y dejando en pie la estructura de relleno: doce lineas donde tres son informacion. Fuera van preambulos, recapitulaciones de lo ya dicho, resumenes de lo que uno acaba de decir, justificaciones no pedidas y alternativas descartadas. Se quedan: que se decidio, que cambia con eso, y que tiene que decidir el usuario.
- **La primera frase tiene que ubicarlo**: de que proyecto se habla y que tipo de cosa se hizo (decidi algo, escribi codigo, revise datos, encontre un error). El usuario lee como el jefe de un departamento: tiene claro el macro, salta entre cinco proyectos en el dia y no tiene los detalles frescos.
- **El orden de apertura es lo que mas falla, y cuesta mas caro que el largo.** Una respuesta que abre por el matiz, por la razon o por la negacion obliga a releerla entera aunque sea corta. El orden correcto es: **hecho concreto -> pregunta que se responde -> definicion del termino -> aplicacion caso por caso.** (a) Abrir por el cuadro completo en una frase concreta: que hay, cuantos son, como se llaman; nunca por un matiz, una excepcion ni un "si, pero", porque el usuario no tiene el modelo en la cabeza y hay que dibujarselo antes de matizarlo. (b) Si es una repregunta suya, nombrar la pregunta que se esta respondiendo ("tu pregunta era por que hable de dos y no de tres"). (c) Definir la palabra corriente que uno usa con un sentido tecnico propio —"calculo", "nivel", "version", "reserva"— antes de razonar con ella: la regla de nombrar la cosa real cubre los nombres del sistema, pero son estas palabras comunes con significado propio las que de verdad confunden. (d) Afirmar, no negar: decir que ES una cosa, nunca abrir explicando por que NO es otra o por que algo NO necesita X, porque eso solo se entiende si ya se sabe lo que se esta negando.
- **Una idea por parrafo, frases cortas.** Nunca un parrafo con tres decisiones adentro. Si una frase tiene tres comas y un guion, partirla.
- **Nombrar la cosa real y definirla en una linea la primera vez que aparece** ("en la base de datos, en la tabla de lotes, que agrupa los datos de una planta para un año"). Nada de metaforas de traduccion inventadas tipo "paquete de datos" o "conjunto de datos": son ambiguas y lo dejan colgado. Prohibido igual: codigos de tarea sueltos (T6A, E3b, S3), nombres de variables o funciones, rutas largas, siglas internas, jerga sin traducir. El detalle crudo va al revisor o a los archivos de trabajo, no al usuario.
- **Cerrar con que se necesita de el, en una linea aparte al final.**
- **Largo**: orientacion, no meta. La mayoria cabe en 5 a 15 lineas. Si el borrador se pasa, el arreglo casi siempre es sacar relleno, no sacar explicacion; si aun asi no cabe, entregar el nucleo y ofrecer el resto ("si quieres, te muestro X").
- **Excepciones donde SI se permite texto largo**: (a) desacuerdo con el revisor, donde va el veredicto completo tal cual; (b) material que el usuario pidio redactar (correos, minutas, planes, documentos); (c) detalle o explicacion pedidos explicitamente.
- Esta regla cambia como se comunica el trabajo, no como se hace: mismo rigor de fondo, reporte corto y claro.

### Autorizacion explicita
- NUNCA ejecutar acciones sin autorizacion explicita del usuario.
- Diagnosticar y proponer; esperar el "hazlo" antes de implementar.
- Si el usuario pregunta "por que falla" o "cual es la solucion", responder la pregunta sin tocar codigo.
- Comandos git destructivos (`reset`, `checkout` de archivos, `restore`, `revert`, `clean`, `stash drop`) requieren autorizacion aunque parezcan menores. Solo `status`, `log`, `diff`, `show`, `branch` son libres.
- Commits y push: solo cuando el usuario los pide. NUNCA `Co-Authored-By` ni "Generated with Claude Code".
- **Commitear SOLO los archivos propios de la sesion, agregados por nombre.** Prohibido `git commit -a`, `git add -A`, `git add .` y cualquier forma de arrastrar el arbol completo. El usuario trabaja con varias sesiones abiertas sobre el mismo repositorio a la vez: un commit del arbol entero se lleva el trabajo a medias de otra sesion bajo un mensaje que no lo describe, y deja esa historia imposible de arreglar sin reescribirla (ocurrio el 2026-07-29). Antes de commitear, revisar `git status` y si aparecen cambios ajenos, dejarlos fuera y mencionarlos al usuario.

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
- **NO usar la herramienta de opcion multiple / menus con alternativas predefinidas (AskUserQuestion).** Esta prohibida por defecto, incluso para "confirmar alcance" o "elegir entre enfoques". Al usuario lo frustra fuerte y es un incumplimiento recurrente. Cuando haya alternativas, describirlas en texto corrido (prosa), explicando en que consiste cada una y sus implicancias, y terminar con una pregunta abierta para que responda conversando, sin apurarlo. UNICA excepcion: ofrecer opciones cerradas solo cuando esas mismas opciones YA se discutieron en la conversacion y el usuario ya entiende cada una. Ante la duda, preguntar en prosa.
- **NO usar la herramienta Workflow (orquestacion multi-agente) salvo autorizacion expresa del usuario en esa conversacion.** Aplica aunque el modo "ultracode" este activo o el sistema sugiera lo contrario. Para analisis y busquedas: leer directo con rg/Read (partes utiles), o a lo sumo agentes individuales (Agent) si hace falta. Si un workflow ayudaria, proponerlo en prosa y esperar el "hazlo".

### Simplicidad y cambios quirurgicos
- El codigo minimo que resuelve el problema. Nada especulativo: ni features extra, ni abstracciones para un solo uso, ni "flexibilidad" no pedida, ni manejo de errores para escenarios imposibles.
- Tocar solo lo que el pedido exige. Cada linea cambiada debe trazarse al pedido.
- NO "mejorar" codigo adyacente, formato ni comentarios. NO refactorizar lo que no esta roto. Respetar el estilo existente aunque sea distinto al que uno elegiria.
- Si se detecta codigo muerto no relacionado, mencionarlo, no borrarlo.
- Solo limpiar los huerfanos (imports, variables) que los propios cambios generaron.

### Criterios de exito
- Antes de empezar, nombrar como se va a verificar que quedo bien ("corre el test X", "la pagina carga sin error Y").
- Criterios debiles ("que funcione") obligan a reabrir; criterios concretos permiten cerrar.

### Busqueda en docs y codigo
- `ripgrep` (`rg`) esta instalado. Usarlo por defecto en vez de `grep`: es mas rapido, respeta `.gitignore` y devuelve fragmento + numero de linea, lo que permite abrir cada archivo en la parte util (offset/limit) en vez de leerlo entero. Ahorra tokens.

### Grafo de conocimiento (orientarse antes de leer a ciegas)
Hay un grafo de los `.md` de `~/projects/` en `$HOME/projects/gestion/grafo/` (generado por `scripts/gen_grafo.py`, regenerable). Antes de hacer un `rg` masivo o leer documentos enteros para ubicarte, usalo como mapa:

1. **Orientarse:** leer `grafo/indice.md` (mapa por proyecto -> sus docs con titulo y tipo). Da el panorama sin abrir nada.
2. **Relaciones:** "que se relaciona con X" se responde con `rg` sobre `grafo/aristas.jsonl` (una arista JSON por linea), sin leer los docs:
   - `rg "<nombre-doc>" grafo/aristas.jsonl` lista sus relaciones. Tipo `estructura` = a que proyecto pertenece; tipo `mencion` = que doc lo cita (campo `evidencia` trae la linea que lo justifica; `peso` = cuantas lineas lo mencionan).
3. **Saltar al doc exacto:** con la ruta del nodo (`id`, relativa a `$HOME`), abrir solo ese archivo en la parte util (offset/limit).

Util sobre todo para "donde quedo X", "que documento habla de Y" y rastrear relaciones entre planes/sesiones/minutas. Cubre solo texto de `~/projects/` (Fase A); no incluye aun `~/storage/`, binarios ni relaciones semanticas. Si se reorganizan archivos, regenerar con `python3 scripts/gen_grafo.py`.

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

### Revision por Codex (grupo de apoyo)
Canal para pedir el veredicto del revisor (Codex con su skill modo-revisor) sin copy-paste del usuario. Cuando el usuario pida "manda esto a revision" o similar:

1. Armar el avance en texto corto: que se hizo, que se buscaba, lista de archivos tocados. **NO pegar el diff**: el revisor lo obtiene solo desde el repo. **Incluir las instrucciones y decisiones que el usuario dio sobre ese trabajo** ("el usuario pidio X", "el usuario decidio que Y queda asi"), para que el revisor no recomiende en contra de algo ya definido por el usuario.
2. Pasarlo por stdin al script, con el directorio del repo actual y timeout generoso (la revision tarda 1-3 min):
   `echo "avance..." | bash ~/projects/omni-tools/revisor-codex/revisar.sh <dir_repo>`
3. Al recibir el veredicto, mostrar al usuario tres cosas, siempre: (a) el veredicto completo tal cual llego; (b) analisis propio punto por punto — en que se esta de acuerdo, en que no y por que; (c) recomendacion de que aplicar y que no. **Nada del veredicto se aplica en automatico**: el revisor tambien puede equivocarse, y aplicar sin analizar arrastra errores silenciosos. Las reglas de autorizacion explicita siguen vigentes.

- "revision con razonamiento alto" (asuntos delicados) -> flag `--alto`. Sube el razonamiento sobre el mismo modelo. Medido 2026-07-31 contra tres defectos reales conocidos: con razonamiento alto encuentra 3 de 3, con el normal 2 de 3. El modelo barato encontro 0 de 3 a cualquier potencia y quedo fuera del rol de revisor.
- "parte revision nueva" -> flag `--nueva`. Usarla al cambiar de tarea o tras editar la skill del revisor.
- "que cuestione el enfoque" -> flag `--adversarial`. Cambia el encuadre de esa ronda: en vez de buscar defectos de implementacion, discute si la solucion elegida es la correcta, de que supuestos depende y donde falla en condiciones reales. Su lugar natural es la ronda previa de una tarea con riesgo real.
- El veredicto llega con formato fijo: primera linea el dictamen (`Puede avanzar`, `No commitear todavia`, `Bloquea produccion`, `No bloquea`), segunda linea el resumen, despues los hallazgos con archivo y linea, y al final los proximos pasos. Si no hay nada que observar, llega solo `Sin observaciones`. Basta leer la primera linea para saber si algo bloquea.
- El revisor recuerda las rondas de la sesion vigente en ese repo. La sesion se renueva sola tras 4 horas sin uso o 20 rondas. Detalle en `~/projects/omni-tools/revisor-codex/README.md`.

**Rutina automatica al ejecutar un plan.** Cuando se esta ejecutando un plan vigente, la revision no espera a que el usuario la pida: es parte del ciclo de cada tarea y no hay que repetirla en cada sesion.

1. **Ronda previa solo si la tarea tiene riesgo real**: seguridad, produccion, migraciones o datos, arquitectura, o decisiones dificiles de revertir. En ese caso, mandar al revisor las intenciones tecnicas — que se va a hacer y por que, enfoque propuesto, archivos que se van a tocar, criterio de exito, mas las decisiones que el usuario ya dio. Las tareas ordinarias van directo a ejecucion, sin ronda previa (la previa indiscriminada era la mitad del gasto de cuota, medido 2026-07-27).
2. **Si el revisor coincide**: informar al usuario en pocas lineas y seguir sin esperar.
3. **Si hay divergencia** (objeta el enfoque, encuentra algo bloqueante, o uno no esta de acuerdo con el): detenerse y mostrar al usuario el veredicto completo tal cual llego, el analisis propio punto por punto y la propuesta de como seguir. **Este es el caso donde el texto largo esta autorizado**: no resumir el veredicto. Esperar su decision.
4. **Ronda de cierre, siempre, y agrupada**: al terminar, ronda con el resultado (que se hizo, archivos tocados, como se verifico). Es la primera ronda de la tarea si no hubo previa: en ese caso va con `--nueva`. Si el revisor levanta hallazgos, mismo tratamiento del punto 3.
5. Con plan vigente no se pregunta por cual frente seguir: se lee el plan y se continua por el orden fijado.

**Agrupar las rondas de cierre.** El revisor lee el repositorio entero en cada ronda, y esa lectura es casi la mitad del costo. Mandarle seis tareas juntas cuesta lo mismo que mandarle tres (medido 2026-07-31: 23,1 creditos contra 22,7), asi que agrupar no reduce lo que se revisa, reduce lo que se relee. Reglas:

- **Hasta seis tareas por ronda de cierre**, del mismo subsistema.
- **Solo tareas ordinarias, independientemente reversibles y sin dependencia funcional entre si.** "Tocan el mismo codigo" NO basta como criterio: son justamente las que mas probablemente dependen unas de otras, y agruparlas significa construir la tercera sobre codigo que nadie reviso.
- **Va en ronda propia, sin agrupar, lo dificil de deshacer**: seguridad, produccion, migraciones o datos, arquitectura, interfaces publicas.
- **Cada tarea en su bloque, con su commit.** El pedido lleva, por tarea: codigo, objetivo, decisiones del usuario, archivos, criterio de verificacion y **el commit o rango de commits que delimita su cambio**. Sin eso el revisor no puede atribuir hallazgos, porque el diff vivo del arbol le muestra la suma — y suele traer trabajo de otras sesiones abiertas sobre el mismo repositorio.
- **Pedir dictamen separado por tarea**, explicito en el mensaje. Funciona sin cambiar nada del revisor, y solo encarece la parte de salida, que es un quinto del costo.
- Si el veredicto agrupado objeta una tarea temprana que ya quedo debajo de otras, se trata como cualquier hallazgo bloqueante del punto 3: se detiene y se muestra al usuario.

El comando `/ejecutar-plan` trae este procedimiento completo.

### Interfaces: disenar en Stitch, implementar con Kimi

Frente de interfaces, con el mismo esquema del revisor: Claude lleva el hilo y delega la parte larga. **Stitch** (por MCP, solo alcanzable desde esta sesion) genera el diseno y guarda la paleta y tipografia del sistema de diseno propio; **Kimi** (programa de linea de comandos, modelo kimi-k3) traduce ese diseno al framework del repo y escribe los archivos; **Codex** revisa el resultado como cualquier otro cambio.

- Se invoca con `/implementar-diseno` desde cualquier repo. Herramienta en `~/projects/gestion/scripts/disenador-kimi/` (`guardar_diseno.sh` baja la pantalla al repo, `disenar.sh` le pasa la tarea a Kimi). Detalle y hallazgos en su README.
- **Limite**: Stitch produce HTML web. Se traduce bien a Next.js/React, con esfuerzo medio a Reflex, y **no se traduce a Streamlit**. Confirmar el framework del destino antes de invocarlo.
- **Kimi escribe en el repo y no tiene modo "solo propuesta"** (probado 2026-07-28: el modo plan igual modifica archivos). La contencion es git: repo limpio antes de invocar, rama aparte para cambios grandes.
- Autorizacion explicita antes de cada corrida: gasta saldo real de la cuenta de Moonshot.

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

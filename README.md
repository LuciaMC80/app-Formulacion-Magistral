# Dietario de Formulación Magistral

Fórmulas magistrales dermatológicas transcritas del cuaderno OneNote «FORMULACIÓN MAGISTRAL», ordenadas de la A a la Z por patología: 135 patologías y 747 fórmulas.

- Abecedario fijo para saltar a cualquier letra.
- Índice de patologías con el número de fórmulas de cada una.
- Buscador por patología o principio activo (no distingue tildes).
- Botón para copiar cada fórmula.
- Funciona sin conexión.

> Revise dosis y excipientes contra el cuaderno original antes de elaborar o prescribir.

## Usarlo

**Sin instalar nada:** descargue `index.html` (o el archivo de la última *Release*) y ábralo con el navegador. Es un único archivo y funciona sin internet; solo las tipografías necesitan conexión la primera vez.

**Como app instalable (PWA):** sirva la carpeta por HTTPS (por ejemplo GitHub Pages) y, desde Chrome o Edge, use «Instalar aplicación»; en iPhone, «Compartir → Añadir a pantalla de inicio». Así queda en caché y abre sin conexión.

Para probarlo en local como app:

```bash
python -m http.server 8000
```

y abra `http://localhost:8000`.

## Actualizar el contenido

`tools/onenote-export.json` es el texto extraído del cuaderno, página a página. Para regenerar la app tras editarlo:

```bash
python tools/build.py
```

`tools/imagenes.json` contiene las fórmulas que en el cuaderno estaban como imagen (diapositivas, fotos de tablas), transcritas a mano; se añaden al final de su patología.

Esto reescribe `index.html` y `tools/data.json` (los datos ya ordenados por letra y patología). `tools/template.html` contiene el diseño y el buscador.

Si añade fórmulas, suba también el número de `CACHE` en `sw.js` para que las apps instaladas descarguen la versión nueva.

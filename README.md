# Sesiones ANR — H.U. Son Espases

Biblioteca web de sesiones formativas del Servicio de Anestesiología, Reanimación y Terapéutica del Dolor del Hospital Universitari Son Espases (Palma de Mallorca).

---

## Cómo funciona

- La web (`index.html`) lee un archivo `videos.json` estático con todos los vídeos de la playlist.
- Un script Python (`fetch_videos.py`) consulta la YouTube Data API, clasifica los vídeos por categorías y regenera `videos.json`.
- Un workflow de GitHub Actions ejecuta ese script cada 24 horas y hace commit automático si hay cambios nuevos.

---

## Puesta en marcha (paso a paso, sin conocimientos técnicos)

### 1. Crear cuenta en GitHub (si no tienes)
Ve a [github.com](https://github.com) y regístrate gratis.

### 2. Crear un nuevo repositorio
1. Pulsa el botón **"New repository"** (botón verde).
2. Dale un nombre, p.ej. `sesiones-anr`.
3. Selecciona **Public**.
4. Pulsa **"Create repository"**.

### 3. Subir los archivos al repositorio
Tienes dos opciones:

**Opción A — Desde el navegador (más fácil):**
1. Dentro del repositorio vacío, pulsa **"uploading an existing file"**.
2. Arrastra o selecciona todos los archivos del proyecto:
   - `index.html`
   - `fetch_videos.py`
   - `videos.json`
   - La carpeta `.github/workflows/update_videos.yml` (crea primero la ruta manualmente con "Create new file" → escribe `.github/workflows/update_videos.yml` y pega el contenido).
3. Pulsa **"Commit changes"**.

**Opción B — Con Git desde Terminal:**
```bash
cd "/ruta/a/tu/proyecto"
git init
git remote add origin https://github.com/TU_USUARIO/sesiones-anr.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

### 4. Añadir la API Key como secreto (sin exponerla en el código)
1. En el repositorio de GitHub, ve a **Settings → Secrets and variables → Actions**.
2. Pulsa **"New repository secret"**.
3. Nombre: `YOUTUBE_API_KEY`
4. Valor: pega tu clave de la YouTube Data API v3 (la que empieza por `AIza…`).
5. Pulsa **"Add secret"**.

> La clave nunca aparecerá en el código ni en los logs. GitHub Actions la inyecta de forma segura.

### 5. Activar GitHub Pages
1. En el repositorio, ve a **Settings → Pages**.
2. En **Source**, selecciona **"Deploy from a branch"**.
3. En **Branch**, elige `main` y carpeta `/ (root)`.
4. Pulsa **Save**.
5. En unos minutos verás la URL de tu web (algo como `https://TU_USUARIO.github.io/sesiones-anr/`).

### 6. Generar el primer videos.json
El workflow se ejecuta automáticamente cada noche, pero para tener los vídeos desde el primer momento:
1. Ve a la pestaña **Actions** de tu repositorio.
2. Selecciona el workflow **"Update videos.json"**.
3. Pulsa **"Run workflow"** → **"Run workflow"** (botón verde).
4. Espera ~30 segundos. El archivo `videos.json` se actualizará y la web mostrará todos los vídeos.

---

## Actualización manual de vídeos

Si quieres regenerar `videos.json` desde tu ordenador:
```bash
export YOUTUBE_API_KEY="AIza..."
python fetch_videos.py
```
Luego sube el `videos.json` actualizado al repositorio.

---

## Añadir o modificar categorías

Edita la variable `CATEGORIES` en `fetch_videos.py` y la constante `CATEGORIES` en `index.html`. Ambas deben tener los mismos IDs. Después ejecuta el script o lanza el workflow manualmente.

---

## Estructura del proyecto

```
├── index.html                        # Web app (toda la lógica en un solo fichero)
├── fetch_videos.py                   # Script que genera videos.json
├── videos.json                       # Datos estáticos de vídeos (generado automáticamente)
├── .github/
│   └── workflows/
│       └── update_videos.yml         # GitHub Actions: actualización diaria
└── README.md                         # Este fichero
```

---

## Preguntas frecuentes

**¿Por qué la web no hace llamadas a la API directamente?**
Para no consumir cuota de la API en cada visita. El script Python consume la cuota una vez al día y guarda el resultado en `videos.json`. La web simplemente lee ese fichero.

**¿Qué pasa si se añaden vídeos nuevos a la playlist?**
El workflow los detectará en su próxima ejecución (máximo 24 h) y actualizará `videos.json` automáticamente.

**¿Puedo cambiar la hora de actualización?**
Sí. Edita la línea `cron:` en `.github/workflows/update_videos.yml`. El formato es estándar cron UTC.

**La web muestra "No se pudo cargar videos.json"**
Significa que `videos.json` está vacío o no se ha generado aún. Lanza el workflow manualmente (paso 6 de arriba).

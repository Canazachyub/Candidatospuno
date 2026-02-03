# Instrucciones de Despliegue - GitHub Pages

## Requisitos Previos
- Git instalado
- Cuenta de GitHub
- Repositorio creado en GitHub

## Paso 1: Inicializar el Repositorio

```bash
cd "E:\Selenium scrapear candidatos\facebook-scraper-local"

# Inicializar Git
git init

# Agregar origen remoto (reemplaza con tu URL)
git remote add origin https://github.com/TU_USUARIO/candidatos-puno-2026.git

# Crear rama main
git branch -M main
```

## Paso 2: Preparar los Archivos

Ejecuta el script de preparación para copiar dashboard y fichas a `docs/`:

```bash
python src/deploy_preparer.py --clean
```

Esto creará:
- `docs/index.html` - Dashboard principal
- `docs/fichas/` - Todas las fichas de candidatos
- `docs/metadata.json` - Metadatos del sitio
- `docs/404.html` - Página de error personalizada

## Paso 3: Primer Commit y Push

```bash
# Agregar todos los archivos
git add .

# Crear commit inicial
git commit -m "Initial commit: Dashboard de candidatos Puno 2026"

# Subir a GitHub
git push -u origin main
```

## Paso 4: Configurar GitHub Pages

1. Ve a tu repositorio en GitHub
2. Settings → Pages
3. En "Source", selecciona:
   - **Source**: GitHub Actions
4. El workflow se ejecutará automáticamente

## Paso 5: Verificar Despliegue

1. Ve a la pestaña "Actions" en tu repositorio
2. Verifica que el workflow "Deploy Dashboard to GitHub Pages" se ejecute correctamente
3. Tu sitio estará disponible en: `https://TU_USUARIO.github.io/candidatos-puno-2026/`

## Actualizaciones Futuras

Para actualizar el sitio después de agregar nuevos candidatos o redes sociales:

### Opción A: Usar el script batch (Windows)
```bash
deploy.bat
```

### Opción B: Manual
```bash
# 1. Regenerar docs/
python src/deploy_preparer.py --clean

# 2. Commit y push
git add docs/
git commit -m "Actualizar fichas de candidatos"
git push origin main
```

El workflow de GitHub Actions se ejecutará automáticamente y actualizará el sitio.

## Estructura del Sitio Desplegado

```
docs/
├── index.html          # Dashboard principal
├── metadata.json       # Info del sitio
├── 404.html           # Página de error
└── fichas/
    ├── 2026-02-02_823623737372328/
    │   ├── index.html  # Ficha del candidato
    │   └── imagen.jpg  # Foto
    ├── 2026-02-02_823626827372019/
    │   ├── index.html
    │   └── imagen.jpg
    └── ... (59 candidatos)
```

## Troubleshooting

### Error: "Permission denied" en GitHub Actions
- Ve a Settings → Actions → General
- En "Workflow permissions", selecciona "Read and write permissions"

### Error: "Pages build and deployment" falla
- Verifica que el workflow esté configurado correctamente
- Revisa los logs en la pestaña Actions

### Las imágenes no cargan
- Verifica que las imágenes estén en `docs/fichas/CARPETA/`
- Las fichas usan fallback a la URL original de Facebook si la imagen local falla

## Notas

- El sitio es estático, no requiere servidor backend
- Las fichas incluyen toda la información del candidato
- Los datos de redes sociales se muestran prellenados
- El dashboard permite filtrar por partido, región y nivel de riesgo

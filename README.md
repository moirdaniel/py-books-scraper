# 📘 Web Scraping de Libros — Books to Scrape

Proyecto completo de Web Scraping que obtiene información desde **https://books.toscrape.com** y la almacena en una base de datos local SQLite.
Incluye scraping del listado, scraping del detalle, normalización de datos, manejo de errores, logs, control de duplicados y exportación a CSV.

## 🚀 Objetivo del Proyecto

Construir un scraper robusto capaz de:

1. Navegar por las primeras **3 páginas del catálogo**.
2. Extraer información relevante de cada libro.
3. Ingresar a la página de detalle para obtener información adicional.
4. Guardar los datos en una base SQLite con esquema definido.
5. Registrar errores y eventos mediante logging.
6. Evitar duplicados usando el **UPC** como clave natural.

Este proyecto es ideal para prácticas profesionales en:

- Web Scraping
- Limpieza y transformación de datos
- Persistencia en SQLite
- Automatización de pipelines
- Buenas prácticas de requests (user-agent, delay, timeouts)

---

## 🧰 Tecnologías Utilizadas

### Lenguaje
- Python 3.10+

### Librerías de scraping
- `requests`
- `beautifulsoup4`
- `lxml`

### Persistencia
- `sqlite3`

### Utilidades
- `logging`
- `csv`
- `re`
- `time`

---

## 📁 Estructura del Proyecto

```
books-scraper/
├─ scrape_books.py
├─ export_first_10.py
├─ requirements.txt
└─ README.md
```

---

## 🔍 Funcionalidades del Proyecto

### 1. Scraping del Catálogo
Extrae:
- Título  
- Precio  
- Disponibilidad  
- Rating  
- URL de imagen  
- URL de detalle  

### 2. Scraping del Detalle
Extrae:
- Descripción  
- UPC  
- Categoría  

### 3. Manejo de Errores
Incluye:
- Timeouts  
- Excepciones HTTP  
- Validación de elementos faltantes  
- Logging  

### 4. Control de Duplicados
El campo **UPC** se usa como clave natural para evitar inserciones repetidas.

### 5. Buenas Prácticas de Scraping
Delay de **1 segundo** entre requests, user-agent personalizado y parseo eficiente con `lxml`.

---

## 🗄️ Base de Datos SQLite

La base se crea automáticamente al ejecutar el scraper.

### Esquema

```sql
CREATE TABLE libros (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  titulo TEXT NOT NULL,
  precio DECIMAL(10,2),
  disponibilidad TEXT,
  rating INTEGER,
  url_imagen TEXT,
  descripcion TEXT,
  upc TEXT,
  categoria TEXT,
  fecha_extraccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## ▶️ Cómo Ejecutar el Proyecto

### 1. Crear entorno virtual (opcional)

Windows:
```
python -m venv venv
venv\Scripts\activate
```

Linux/Mac:
```
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalar dependencias
```
pip install -r requirements.txt
```

### 3. Ejecutar el scraper
```
python scrape_books.py
```

### 4. Exportar los primeros 10 registros
```
python export_first_10.py
```

---

## 🖥️ Ver la Base de Datos

CLI SQLite:
```
sqlite3 libros.db
.tables
SELECT * FROM libros LIMIT 10;
.exit
```

GUI recomendadas:
- DB Browser for SQLite
- SQLiteStudio

---

## ✔️ Estado del Proyecto

Incluye:
- Scraper funcional  
- Logs  
- Base SQLite  
- Export CSV  
- Manejo de errores  
- Control de duplicados  
- Documentación detallada  

---

## 📌 Notas Finales

BooksToScrape está diseñado para practicar scraping y no posee restricciones fuertes, lo que lo hace ideal para entrenamiento y pruebas controladas.

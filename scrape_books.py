
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sqlite3
import time
import re
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DanielScraper/1.0; +https://books.toscrape.com/)"
}

RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}


def configurar_logger() -> None:
    """
    Configura el logger básico para consola + archivo.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("scraper.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )


def crear_conexion(db_path: str = "libros.db") -> sqlite3.Connection:
    """
    Crea la conexión a la base SQLite y garantiza la existencia de la tabla 'libros'.
    """
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS libros (
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
        """
    )
    return conn


def normalizar_precio(precio_str: Optional[str]) -> Optional[float]:
    """
    Recibe un string de precio (ej: '£51.77') y devuelve un float (51.77).
    Si no puede convertir, devuelve None.
    """
    if not precio_str:
        return None

    numero = re.sub(r"[^0-9.]", "", precio_str)
    if not numero:
        return None

    try:
        return float(numero)
    except ValueError:
        logging.warning("No se pudo convertir el precio: %s", precio_str)
        return None


def obtener_html(url: str, delay_segundos: float = 1.0) -> Optional[str]:
    """
    Hace un GET simple con requests y devuelve el HTML como string.
    Incluye timeout, manejo de errores y un pequeño delay para no saturar el servidor.
    """
    try:
        logging.info("GET %s", url)
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        # Politely: no spamear el servidor
        time.sleep(delay_segundos)
        return resp.text
    except requests.RequestException as ex:
        logging.error("Error al solicitar %s: %s", url, ex)
        return None


def url_catalogo(page: int) -> str:
    """
    Devuelve la URL de la página de catálogo para el número de página indicado.
    La página 1 es la raíz; el resto usa /catalogue/page-x.html
    """
    if page == 1:
        return BASE_URL
    return urljoin(BASE_URL, f"catalogue/page-{page}.html")


def parsear_libros_catalogo(html: str) -> List[Dict[str, Any]]:
    """
    Dado el HTML de una página de catálogo, devuelve una lista de dicts
    con la info básica de cada libro (sin detalle).
    """
    soup = BeautifulSoup(html, "lxml")
    libros: List[Dict[str, Any]] = []

    for article in soup.select("article.product_pod"):
        # Título
        link_tag = article.select_one("h3 a")
        titulo = link_tag.get("title", "").strip() if link_tag else ""

        # Precio
        precio_tag = article.select_one("p.price_color")
        precio_texto = precio_tag.get_text(strip=True) if precio_tag else None

        # Disponibilidad
        disp_tag = article.select_one("p.instock.availability")
        disponibilidad_texto = disp_tag.get_text(strip=True) if disp_tag else None

        # Rating
        rating_tag = article.select_one("p.star-rating")
        rating = None
        if rating_tag:
            clases = rating_tag.get("class", [])
            for c in clases:
                if c in RATING_MAP:
                    rating = RATING_MAP[c]
                    break

        # Imagen
        img_tag = article.select_one("div.image_container img")
        img_url = urljoin(BASE_URL, img_tag["src"]) if img_tag and img_tag.get("src") else None

        # URL detalle
        detail_url = urljoin(BASE_URL, link_tag["href"]) if link_tag and link_tag.get("href") else None

        libros.append(
            {
                "titulo": titulo,
                "precio": normalizar_precio(precio_texto),
                "disponibilidad": disponibilidad_texto,
                "rating": rating,
                "url_imagen": img_url,
                "detail_url": detail_url,
            }
        )

    return libros


def parsear_detalle(html: str) -> Dict[str, Optional[str]]:
    """
    Dado el HTML de un detalle de libro, extrae:
      - descripcion
      - upc
      - categoria
    """
    soup = BeautifulSoup(html, "lxml")

    # Descripción: está después del div con id="product_description"
    descripcion = None
    desc_header = soup.find(id="product_description")
    if desc_header:
        # Primer <p> después del encabezado de descripción
        p = desc_header.find_next("p")
        if p:
            descripcion = p.get_text(strip=True)

    upc = None
    categoria = None

    # UPC: normalmente viene en la tabla de información
    tabla = soup.select_one("table.table.table-striped")
    if tabla:
        for row in tabla.select("tr"):
            th = row.find("th")
            td = row.find("td")
            if not th or not td:
                continue
            label = th.get_text(strip=True)
            if label == "UPC":
                upc = td.get_text(strip=True)
                break

    # Categoría: viene en el breadcrumb (Home / Books / Category / Title)
    breadcrumb_links = soup.select("ul.breadcrumb li a")
    # Ej: [Home, Books, Poetry] → la última suele ser la categoría
    if len(breadcrumb_links) >= 3:
        categoria = breadcrumb_links[-1].get_text(strip=True)

    return {
        "descripcion": descripcion,
        "upc": upc,
        "categoria": categoria,
    }


def existe_libro(conn: sqlite3.Connection, upc: Optional[str]) -> bool:
    """
    Verifica si ya existe un libro en la tabla con el mismo UPC.
    Si no hay UPC, se asume que no existe (no se controla duplicado).
    """
    if not upc:
        return False
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM libros WHERE upc = ? LIMIT 1;", (upc,))
    return cur.fetchone() is not None


def insertar_libro(conn: sqlite3.Connection, libro: Dict[str, Any]) -> None:
    """
    Inserta un libro en la tabla 'libros'.
    """
    conn.execute(
        """
        INSERT INTO libros (
            titulo,
            precio,
            disponibilidad,
            rating,
            url_imagen,
            descripcion,
            upc,
            categoria
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            libro["titulo"],
            libro["precio"],
            libro["disponibilidad"],
            libro["rating"],
            libro["url_imagen"],
            libro.get("descripcion"),
            libro.get("upc"),
            libro.get("categoria"),
        ),
    )
    conn.commit()


def main() -> None:
    """
    Punto de entrada principal del scraper.
    - Recorre las primeras 3 páginas del catálogo.
    - Para cada libro, entra a su detalle.
    - Persiste en SQLite evitando duplicados por UPC.
    """
    configurar_logger()
    logging.info("Inicio del proceso de scraping")

    conn = crear_conexion()
    total_insertados = 0
    total_detalles_ok = 0

    # Recorremos las primeras 3 páginas
    for page in range(1, 4):
        catalog_url = url_catalogo(page)
        html_catalogo = obtener_html(catalog_url)

        if not html_catalogo:
            logging.warning("No se pudo obtener HTML para la página %s, se omite.", page)
            continue

        libros_catalogo = parsear_libros_catalogo(html_catalogo)
        logging.info("Página %s: %s libros encontrados", page, len(libros_catalogo))

        for libro in libros_catalogo:
            detail_url = libro.get("detail_url")

            descripcion = None
            upc = None
            categoria = None

            if detail_url:
                detalle_html = obtener_html(detail_url)
                if detalle_html:
                    detalle = parsear_detalle(detalle_html)
                    descripcion = detalle.get("descripcion")
                    upc = detalle.get("upc")
                    categoria = detalle.get("categoria")
                    total_detalles_ok += 1
                else:
                    logging.warning("No se pudo obtener detalle para '%s'", libro["titulo"])
            else:
                logging.warning("Libro sin URL de detalle: '%s'", libro["titulo"])

            libro["descripcion"] = descripcion
            libro["upc"] = upc
            libro["categoria"] = categoria

            # Control de duplicados por UPC
            if upc and existe_libro(conn, upc):
                logging.info("Libro ya existente (UPC=%s), se omite: %s", upc, libro["titulo"])
                continue

            try:
                insertar_libro(conn, libro)
                total_insertados += 1
                logging.info("Insertado [%s] %s", total_insertados, libro["titulo"])
            except sqlite3.DatabaseError as ex:
                logging.error("Error al insertar libro '%s': %s", libro["titulo"], ex)

    conn.close()
    logging.info("Fin del proceso. Libros insertados: %s. Detalles procesados: %s",
                 total_insertados, total_detalles_ok)


if __name__ == "__main__":
    main()

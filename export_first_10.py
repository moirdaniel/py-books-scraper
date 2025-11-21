#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import csv


def exportar_primeros_10(db_path: str = "libros.db", output_csv: str = "primeros_10_libros.csv") -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, titulo, precio, disponibilidad, rating, categoria, upc
        FROM libros
        ORDER BY id
        LIMIT 10;
        """
    )
    rows = cur.fetchall()
    headers = [desc[0] for desc in cur.description]

    # Mostrar en consola
    print("Primeros 10 registros:")
    for row in rows:
        print(row)

    # Exportar a CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    conn.close()
    print(f"\nExportado a {output_csv}")


if __name__ == "__main__":
    exportar_primeros_10()

import json
import os
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

JSON_PATH = "resultados_deteccion.json"
EXCEL_PATH = "reporte_detecciones.xlsx"


def json_to_excel(json_path=JSON_PATH, output_excel=EXCEL_PATH):
    if not os.path.exists(json_path):
        print(f"Error: No existe el archivo {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("metadata", {})
    videos = data.get("videos", [])

    wb = openpyxl.Workbook()

    # Estilos
    font_title = Font(name="Segoe UI", size=16, bold=True, color="1F4E79")
    font_subtitle = Font(name="Segoe UI", size=10, italic=True, color="595959")
    font_header = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    font_bold = Font(name="Segoe UI", size=10, bold=True)
    font_data = Font(name="Segoe UI", size=10)

    fill_navy = PatternFill(
        start_color="1F4E79", end_color="1F4E79", fill_type="solid"
    )
    fill_accent = PatternFill(
        start_color="2980B9", end_color="2980B9", fill_type="solid"
    )
    fill_zebra = PatternFill(
        start_color="F9FAFC", end_color="F9FAFC", fill_type="solid"
    )
    fill_card = PatternFill(
        start_color="EBF5FB", end_color="EBF5FB", fill_type="solid"
    )
    fill_footer = PatternFill(
        start_color="EAEDED", end_color="EAEDED", fill_type="solid"
    )

    border_thin = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )
    border_top_thick = Border(
        top=Side(style="medium", color="1F4E79"),
        bottom=Side(style="thin", color="D9D9D9"),
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
    )

    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    # ==========================================
    # HOJA 1: RESUMEN GENERAL
    # ==========================================
    ws = wb.active
    ws.title = "Resumen General"
    ws.views.sheetView[0].showGridLines = True

    ws["A1"] = "Reporte de Detección de Fauna y Objetos - Wildcam"
    ws["A1"].font = font_title

    lote_global = meta.get("lote", "N/A")
    exec_time_str = meta.get("execution_time_formatted", "N/A")
    exec_sec = meta.get("execution_time_seconds", 0)

    ws["A2"] = (
        f"Modelo: {meta.get('model', 'N/A')} | Umbral: {meta.get('conf_threshold', 0.2)} | "
        f"Frame Skip: {meta.get('frame_skip', 10)}"
    )
    ws["A2"].font = font_subtitle

    # Tarjetas KPI
    total_vids = len(videos)
    vids_animals = sum(
        1
        for v in videos
        if "animal" in v.get("summary", {}).get("detected_classes", [])
    )
    vids_person = sum(
        1
        for v in videos
        if "person" in v.get("summary", {}).get("detected_classes", [])
    )
    vids_empty = sum(
        1 for v in videos if not v.get("summary", {}).get("detected_classes", [])
    )

    cards = [
        ("Total Videos", total_vids, "B4"),
        ("Videos con Fauna", vids_animals, "D4"),
        ("Presencia Humana", vids_person, "F4"),
        ("Videos Sin Detección", vids_empty, "H4"),
    ]

    for title, val, pos in cards:
        col = pos[0]
        row = int(pos[1])
        next_col = chr(ord(col) + 1)
        ws.merge_cells(f"{pos}:{next_col}{row}")
        ws.merge_cells(f"{col}{row+1}:{next_col}{row+1}")

        c_title = ws[f"{col}{row}"]
        c_title.value = title
        c_title.font = Font(name="Segoe UI", size=9, bold=True, color="595959")
        c_title.alignment = align_center
        c_title.fill = fill_card

        c_val = ws[f"{col}{row+1}"]
        c_val.value = val
        c_val.font = Font(name="Segoe UI", size=16, bold=True, color="1F4E79")
        c_val.alignment = align_center
        c_val.fill = fill_card

    # Encabezados de la Tabla
    headers = [
        "Lote / Cámara",
        "Archivo de Video",
        "Detecciones Totales",
        "Clases Detectadas",
        "Máx. Confianza Animal",
        "Máx. Confianza Persona",
        "Estado",
    ]

    start_row = 8
    for col_idx, text in enumerate(headers, 1):
        cell = ws.cell(row=start_row, column=col_idx, value=text)
        cell.font = font_header
        cell.fill = fill_navy
        cell.alignment = align_center
        cell.border = border_thin

    # Filas de datos
    current_row = start_row + 1
    for idx, v in enumerate(videos, 1):
        summary = v.get("summary", {})
        det_classes = summary.get("detected_classes", [])
        max_conf = summary.get("max_confidence", {})

        conf_anim = max_conf.get("animal", 0.0)
        conf_pers = max_conf.get("person", 0.0)

        if "animal" in det_classes:
            status = "Fauna Detectada"
        elif "person" in det_classes:
            status = "Presencia Humana"
        elif "vehicle" in det_classes:
            status = "Vehículo Detectado"
        else:
            status = "Sin Detecciones"

        v_lote = v.get("lote") or lote_global

        row_vals = [
            v_lote,
            v.get("file", ""),
            summary.get("total_detections_count", 0),
            ", ".join(det_classes) or "Ninguna",
            conf_anim if conf_anim else "-",
            conf_pers if conf_pers else "-",
            status,
        ]

        is_even = idx % 2 == 0
        row_fill = fill_zebra if is_even else PatternFill(fill_type=None)

        for col_idx, val in enumerate(row_vals, 1):
            cell = ws.cell(row=current_row, column=col_idx, value=val)
            cell.font = font_data
            cell.border = border_thin
            cell.fill = row_fill

            if col_idx in [1, 2, 4, 7]:
                cell.alignment = align_left
            elif col_idx == 3:
                cell.alignment = align_right
                cell.number_format = "#,##0"
            elif col_idx in [5, 6]:
                cell.alignment = align_right
                if isinstance(val, (int, float)):
                    cell.number_format = "0.0%"

        current_row += 1

    # FILA FINAL 1: Tiempo Total de Ejecución
    ws.cell(
        row=current_row, column=1, value="Tiempo Total de Ejecución:"
    ).font = font_bold
    ws.cell(
        row=current_row, column=2, value=f"{exec_time_str} ({exec_sec} seg)"
    ).font = font_data
    for col_i in range(1, len(headers) + 1):
        c = ws.cell(row=current_row, column=col_i)
        c.fill = fill_footer
        c.border = border_top_thick if col_i == 1 else border_thin
    current_row += 1

    # FILA FINAL 2: Lote / Carpeta Procesada
    ws.cell(
        row=current_row, column=1, value="Lote / Carpeta Procesada:"
    ).font = font_bold
    ws.cell(row=current_row, column=2, value=lote_global).font = font_data
    for col_i in range(1, len(headers) + 1):
        c = ws.cell(row=current_row, column=col_i)
        c.fill = fill_footer
        c.border = border_thin

    ws.freeze_panes = f"A{start_row+1}"

    # Auto-ajustar ancho de columnas
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 15)

    wb.save(output_excel)
    print(f"Reporte Excel guardado exitosamente en: {output_excel}")


if __name__ == "__main__":
    json_to_excel()
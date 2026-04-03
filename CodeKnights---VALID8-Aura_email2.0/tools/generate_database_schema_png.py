from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "database_schema.json.txt"
DEFAULT_OUTPUT = ROOT / "Databse" / "database_schema.png"


BACKGROUND = "#f4f6fb"
TITLE_COLOR = "#19324d"
SUBTITLE_COLOR = "#546275"
TABLE_BORDER = "#203044"
TABLE_HEADER_FILL = "#203044"
TABLE_HEADER_TEXT = "#ffffff"
TABLE_BODY_FILL = "#ffffff"
TABLE_ROW_LINE = "#dde4ee"
TABLE_TEXT = "#1d2939"
TABLE_META = "#6b7280"
FK_LINE = "#b8c4d6"
LEGEND_BG = "#ffffff"
LEGEND_BORDER = "#cfd8e3"


@dataclass
class ForeignKey:
    source_table: str
    source_columns: list[str]
    target_table: str
    target_columns: list[str]


@dataclass
class TableBox:
    table_name: str
    x: int
    y: int
    width: int
    height: int
    header_height: int
    body_height: int

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    @property
    def center_y(self) -> int:
        return self.y + self.height // 2


def load_schema(path: Path) -> tuple[list[dict], list[dict]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    enums = payload.get("enums", [])
    tables: list[dict] = []
    for schema in payload.get("schemas", []):
        tables.extend(schema.get("tables", []))
    tables.sort(key=lambda item: item.get("table_name", ""))
    return tables, enums


def load_font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    left, _, right, _ = draw.textbbox((0, 0), text, font=font)
    return right - left


def shorten_type(column: dict) -> str:
    data_type = str(column.get("data_type") or "").strip()
    udt_name = str(column.get("udt_name") or "").strip()
    max_len = column.get("character_maximum_length")
    numeric_precision = column.get("numeric_precision")
    numeric_scale = column.get("numeric_scale")

    if data_type == "character varying":
        return f"varchar({max_len})" if max_len else "varchar"
    if data_type == "character":
        return f"char({max_len})" if max_len else "char"
    if data_type == "timestamp without time zone":
        return "timestamp"
    if data_type == "timestamp with time zone":
        return "timestamptz"
    if data_type == "USER-DEFINED" and udt_name:
        return udt_name
    if data_type == "ARRAY":
        return f"{udt_name}[]"
    if data_type == "numeric":
        if numeric_precision is not None and numeric_scale is not None:
            return f"numeric({numeric_precision},{numeric_scale})"
        return "numeric"
    if udt_name in {"int2", "int4", "int8", "float4", "float8", "bool", "text"}:
        aliases = {
            "int2": "smallint",
            "int4": "integer",
            "int8": "bigint",
            "float4": "real",
            "float8": "double",
            "bool": "boolean",
            "text": "text",
        }
        return aliases[udt_name]
    return data_type or udt_name or "unknown"


def fit_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> str:
    if text_width(draw, text, font) <= max_width:
        return text
    ellipsis = "..."
    trimmed = text
    while trimmed:
        trimmed = trimmed[:-1]
        candidate = trimmed + ellipsis
        if text_width(draw, candidate, font) <= max_width:
            return candidate
    return ellipsis


def build_table_lines(table: dict) -> list[str]:
    primary_key = set((table.get("primary_key") or {}).get("columns") or [])
    foreign_key_columns = {
        column
        for fk in table.get("foreign_keys", []) or []
        for column in fk.get("columns", []) or []
    }

    lines: list[str] = []
    for column in table.get("columns", []) or []:
        column_name = str(column.get("column_name"))
        flags: list[str] = []
        if column_name in primary_key:
            flags.append("PK")
        if column_name in foreign_key_columns:
            flags.append("FK")
        if not bool(column.get("is_nullable", True)):
            flags.append("NN")
        flag_text = f" [{' '.join(flags)}]" if flags else ""
        lines.append(f"{column_name}: {shorten_type(column)}{flag_text}")
    return lines


def gather_foreign_keys(tables: Iterable[dict]) -> list[ForeignKey]:
    fks: list[ForeignKey] = []
    for table in tables:
        source_name = str(table.get("table_name"))
        for raw_fk in table.get("foreign_keys", []) or []:
            target_name = str(raw_fk.get("referenced_table"))
            if not target_name:
                continue
            fks.append(
                ForeignKey(
                    source_table=source_name,
                    source_columns=list(raw_fk.get("columns", []) or []),
                    target_table=target_name,
                    target_columns=list(raw_fk.get("referenced_columns", []) or []),
                )
            )
    return fks


def compute_table_heights(
    tables: list[dict],
    *,
    line_height: int,
    header_height: int,
    padding_y: int,
    footer_height: int,
) -> dict[str, int]:
    heights: dict[str, int] = {}
    for table in tables:
        body_lines = max(1, len(build_table_lines(table)))
        body_height = padding_y * 2 + body_lines * line_height + footer_height
        heights[str(table.get("table_name"))] = header_height + body_height
    return heights


def layout_tables(
    tables: list[dict],
    *,
    box_width: int,
    margin_x: int,
    margin_y: int,
    gap_x: int,
    gap_y: int,
    title_height: int,
    header_height: int,
    body_padding_y: int,
    line_height: int,
    footer_height: int,
) -> tuple[dict[str, TableBox], int, int]:
    table_heights = compute_table_heights(
        tables,
        line_height=line_height,
        header_height=header_height,
        padding_y=body_padding_y,
        footer_height=footer_height,
    )

    table_count = max(1, len(tables))
    columns = max(4, min(6, math.ceil(math.sqrt(table_count / 1.4))))
    column_heights = [title_height + margin_y for _ in range(columns)]

    positions: dict[str, TableBox] = {}

    # Place larger tables first to keep column heights balanced.
    ordered_tables = sorted(
        tables,
        key=lambda item: (-table_heights[str(item.get("table_name"))], str(item.get("table_name"))),
    )

    for table in ordered_tables:
        table_name = str(table.get("table_name"))
        body_lines = max(1, len(build_table_lines(table)))
        body_height = body_padding_y * 2 + body_lines * line_height + footer_height
        total_height = header_height + body_height

        column_index = min(range(columns), key=lambda idx: column_heights[idx])
        x = margin_x + column_index * (box_width + gap_x)
        y = column_heights[column_index]
        positions[table_name] = TableBox(
            table_name=table_name,
            x=x,
            y=y,
            width=box_width,
            height=total_height,
            header_height=header_height,
            body_height=body_height,
        )
        column_heights[column_index] += total_height + gap_y

    image_width = margin_x * 2 + columns * box_width + (columns - 1) * gap_x
    image_height = max(column_heights) + margin_y + 220
    return positions, image_width, image_height


def draw_relationships(
    draw: ImageDraw.ImageDraw,
    positions: dict[str, TableBox],
    foreign_keys: list[ForeignKey],
) -> None:
    for fk in foreign_keys:
        source = positions.get(fk.source_table)
        target = positions.get(fk.target_table)
        if source is None or target is None:
            continue

        if source.x <= target.x:
            start = (source.right, source.center_y)
            end = (target.x, target.center_y)
        else:
            start = (source.x, source.center_y)
            end = (target.right, target.center_y)

        mid_x = (start[0] + end[0]) // 2
        points = [start, (mid_x, start[1]), (mid_x, end[1]), end]
        draw.line(points, fill=FK_LINE, width=2)
        draw.ellipse(
            (end[0] - 4, end[1] - 4, end[0] + 4, end[1] + 4),
            fill=FK_LINE,
            outline=FK_LINE,
        )


def draw_tables(
    image: Image.Image,
    tables: list[dict],
    positions: dict[str, TableBox],
    *,
    title_font: ImageFont.ImageFont,
    body_font: ImageFont.ImageFont,
    meta_font: ImageFont.ImageFont,
) -> None:
    draw = ImageDraw.Draw(image)
    line_height = 22
    inner_padding_x = 16
    inner_padding_y = 12
    footer_height = 34

    ordered = sorted(tables, key=lambda item: str(item.get("table_name")))
    for table in ordered:
        table_name = str(table.get("table_name"))
        box = positions[table_name]
        header_bottom = box.y + box.header_height

        draw.rounded_rectangle(
            (box.x, box.y, box.right, box.bottom),
            radius=14,
            fill=TABLE_BODY_FILL,
            outline=TABLE_BORDER,
            width=2,
        )
        draw.rounded_rectangle(
            (box.x, box.y, box.right, header_bottom),
            radius=14,
            fill=TABLE_HEADER_FILL,
            outline=TABLE_BORDER,
            width=2,
        )
        draw.rectangle(
            (box.x, header_bottom - 14, box.right, header_bottom),
            fill=TABLE_HEADER_FILL,
            outline=TABLE_HEADER_FILL,
        )

        draw.text(
            (box.x + inner_padding_x, box.y + 10),
            table_name,
            fill=TABLE_HEADER_TEXT,
            font=title_font,
        )

        columns = table.get("columns", []) or []
        meta_text = f"{len(columns)} columns"
        meta_width = text_width(draw, meta_text, meta_font)
        draw.text(
            (box.right - inner_padding_x - meta_width, box.y + 14),
            meta_text,
            fill="#d3dbe7",
            font=meta_font,
        )

        text_y = header_bottom + inner_padding_y
        max_line_width = box.width - inner_padding_x * 2
        for raw_line in build_table_lines(table):
            line = fit_text(draw, raw_line, body_font, max_line_width)
            draw.text(
                (box.x + inner_padding_x, text_y),
                line,
                fill=TABLE_TEXT,
                font=body_font,
            )
            text_y += line_height

        footer_y = box.bottom - footer_height + 6
        fk_count = len(table.get("foreign_keys", []) or [])
        index_count = len(table.get("indexes", []) or [])
        footer = f"FKs: {fk_count}  Indexes: {index_count}"
        draw.line(
            (box.x, footer_y - 8, box.right, footer_y - 8),
            fill=TABLE_ROW_LINE,
            width=1,
        )
        draw.text(
            (box.x + inner_padding_x, footer_y),
            footer,
            fill=TABLE_META,
            font=meta_font,
        )


def draw_title_and_legend(
    image: Image.Image,
    *,
    table_count: int,
    foreign_key_count: int,
    enum_count: int,
    enums: list[dict],
) -> None:
    draw = ImageDraw.Draw(image)
    title_font = load_font(34, bold=True)
    subtitle_font = load_font(16)
    small_font = load_font(14)

    draw.text((48, 28), "RIZAL_v1 Database Schema", fill=TITLE_COLOR, font=title_font)
    subtitle = (
        f"{table_count} tables | {foreign_key_count} foreign keys | {enum_count} enums | "
        "Source: database_schema.json.txt"
    )
    draw.text((48, 74), subtitle, fill=SUBTITLE_COLOR, font=subtitle_font)
    draw.text(
        (48, 102),
        "Legend: PK = primary key, FK = foreign key, NN = not null",
        fill=SUBTITLE_COLOR,
        font=subtitle_font,
    )

    if not enums:
        return

    legend_x = image.width - 620
    legend_y = 26
    legend_width = 560
    row_height = 20
    body_lines: list[str] = []
    for enum in enums:
        enum_name = str(enum.get("enum_name") or "enum")
        values = ", ".join(str(value) for value in enum.get("values", []) or [])
        body_lines.append(f"{enum_name}: {values}")

    legend_height = 18 + 30 + len(body_lines) * row_height + 18
    draw.rounded_rectangle(
        (legend_x, legend_y, legend_x + legend_width, legend_y + legend_height),
        radius=14,
        fill=LEGEND_BG,
        outline=LEGEND_BORDER,
        width=2,
    )
    draw.text((legend_x + 18, legend_y + 14), "Enums", fill=TITLE_COLOR, font=subtitle_font)
    text_y = legend_y + 48
    for line in body_lines:
        trimmed = fit_text(draw, line, small_font, legend_width - 36)
        draw.text((legend_x + 18, text_y), trimmed, fill=TABLE_TEXT, font=small_font)
        text_y += row_height


def render_schema_png(input_path: Path, output_path: Path) -> Path:
    tables, enums = load_schema(input_path)
    foreign_keys = gather_foreign_keys(tables)

    title_height = 160
    margin_x = 48
    margin_y = 28
    gap_x = 42
    gap_y = 42
    box_width = 470
    header_height = 48
    body_padding_y = 12
    line_height = 22
    footer_height = 34

    positions, width, height = layout_tables(
        tables,
        box_width=box_width,
        margin_x=margin_x,
        margin_y=margin_y,
        gap_x=gap_x,
        gap_y=gap_y,
        title_height=title_height,
        header_height=header_height,
        body_padding_y=body_padding_y,
        line_height=line_height,
        footer_height=footer_height,
    )

    image = Image.new("RGB", (width, height), BACKGROUND)
    draw_relationships(ImageDraw.Draw(image), positions, foreign_keys)
    draw_title_and_legend(
        image,
        table_count=len(tables),
        foreign_key_count=len(foreign_keys),
        enum_count=len(enums),
        enums=enums,
    )
    draw_tables(
        image,
        tables,
        positions,
        title_font=load_font(19, bold=True),
        body_font=load_font(14),
        meta_font=load_font(12),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG", optimize=True)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a PNG database schema poster.")
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT),
        help="Path to the exported schema JSON text file.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Path to the output PNG file.",
    )
    args = parser.parse_args()

    output = render_schema_png(Path(args.input), Path(args.output))
    print(output)


if __name__ == "__main__":
    main()

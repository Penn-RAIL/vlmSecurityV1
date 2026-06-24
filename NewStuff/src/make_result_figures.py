#!/usr/bin/env python3
"""Create final result figures from the adjudicated outcomes CSV."""

from __future__ import annotations

import csv
import html
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
OUTCOMES = ROOT / "results" / "extracted_outcomes_final_sample_v2.csv"
FIG_DIR = REPO_ROOT / "resultFigures"

VECTOR_ORDER = ["control", "user_prompt", "system_prompt", "image_channel"]
VECTOR_LABELS = {
    "control": "Control",
    "user_prompt": "User Prompt",
    "system_prompt": "System Prompt",
    "image_channel": "Image Channel",
}
TARGET_ORDER = ["Cardiomegaly", "Pleural Effusion", "Pneumothorax"]
COLORS = {
    "control": "#6f7a83",
    "user_prompt": "#d9252a",
    "system_prompt": "#e47b14",
    "image_channel": "#7d2f91",
    "success": "#1f9d2a",
    "diagnosed_not_success": "#ff8a18",
    "mentioned_not_diagnosed": "#a9c3e4",
    "neither": "#cfcfcf",
    "axis": "#172026",
    "grid": "#d3d8dc",
    "muted": "#66737d",
    "cardiomegaly": "#2d7dd2",
    "pleural_effusion": "#d9252a",
    "pneumothorax": "#e47b14",
}
TARGET_COLORS = {
    "Cardiomegaly": COLORS["cardiomegaly"],
    "Pleural Effusion": COLORS["pleural_effusion"],
    "Pneumothorax": COLORS["pneumothorax"],
}


def read_rows() -> list[dict[str, str]]:
    with OUTCOMES.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pct(count: int, total: int) -> float:
    return 100.0 * count / total if total else 0.0


def wilson_ci(count: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p = count / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denom
    return max(0.0, 100 * (center - half)), min(100.0, 100 * (center + half))


def fmt_pct(value: float) -> str:
    if abs(value - round(value)) < 0.05:
        return f"{round(value):.0f}%"
    return f"{value:.1f}%"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


class Svg:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.parts: list[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            "<style>",
            "text{font-family:Inter,Arial,Helvetica,sans-serif;letter-spacing:0}",
            ".title{font-size:38px;font-weight:800;fill:#050607}",
            ".subtitle{font-size:16px;fill:#66737d}",
            ".axis{stroke:#172026;stroke-width:2}",
            ".grid{stroke:#d3d8dc;stroke-width:1.4;stroke-dasharray:5 5}",
            ".tick{font-size:21px;fill:#172026}",
            ".label{font-size:23px;fill:#172026}",
            ".small{font-size:16px;fill:#66737d}",
            ".value{font-size:25px;font-weight:800;fill:#050607}",
            ".whitevalue{font-size:25px;font-weight:800;fill:#fff}",
            "</style>",
            '<rect width="100%" height="100%" fill="#ffffff"/>',
        ]

    def line(self, x1: float, y1: float, x2: float, y2: float, stroke: str, width: float = 1, dash: str | None = None):
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{stroke}" stroke-width="{width}"{dash_attr}/>')

    def rect(self, x: float, y: float, w: float, h: float, fill: str, stroke: str | None = None, sw: float = 1, rx: float = 0):
        stroke_attr = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        self.parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}"{stroke_attr} rx="{rx}"/>')

    def text(
        self,
        x: float,
        y: float,
        text: object,
        cls: str = "",
        anchor: str = "start",
        fill: str | None = None,
        size: int | None = None,
        weight: int | None = None,
        rotate: float | None = None,
    ):
        attrs = [f'x="{x:.2f}"', f'y="{y:.2f}"', f'text-anchor="{anchor}"']
        if cls:
            attrs.append(f'class="{cls}"')
        if fill:
            attrs.append(f'fill="{fill}"')
        if size:
            attrs.append(f'font-size="{size}"')
        if weight:
            attrs.append(f'font-weight="{weight}"')
        if rotate is not None:
            attrs.append(f'transform="rotate({rotate:.1f} {x:.2f} {y:.2f})"')
        self.parts.append(f'<text {" ".join(attrs)}>{esc(text)}</text>')

    def multiline_text(self, x: float, y: float, lines: list[str], cls: str = "label", anchor: str = "middle", line_height: int = 27):
        for i, line in enumerate(lines):
            self.text(x, y + i * line_height, line, cls=cls, anchor=anchor)

    def save(self, path: Path):
        self.parts.append("</svg>")
        path.write_text("\n".join(self.parts), encoding="utf-8")


def y_scale(value: float, top: float, bottom: float, ymax: float = 100.0) -> float:
    return bottom - (value / ymax) * (bottom - top)


def draw_y_axis(svg: Svg, left: int, top: int, bottom: int, right: int, ymax: int = 100, step: int = 20):
    for tick in range(0, ymax + 1, step):
        y = y_scale(tick, top, bottom, ymax)
        svg.line(left, y, right, y, COLORS["grid"], 1.2, "5 5")
        svg.text(left - 16, y + 7, f"{tick}%", cls="tick", anchor="end")
    svg.line(left, top, left, bottom, COLORS["axis"], 2)
    svg.line(left, bottom, right, bottom, COLORS["axis"], 2)


def figure_1(rows: list[dict[str, str]]):
    svg = Svg(1600, 1600)
    svg.text(800, 62, "Attack Success Rate by Attack Vector", cls="title", anchor="middle")
    svg.text(800, 95, "Final reviewed outcomes; error bars show 95% Wilson confidence intervals", cls="subtitle", anchor="middle")
    left, right, top, bottom = 160, 1510, 220, 1250
    draw_y_axis(svg, left, top, bottom, right)
    svg.text(55, (top + bottom) / 2, "Attack Success Rate", cls="label", anchor="middle", rotate=-90)

    bar_w = 190
    gap = (right - left - len(VECTOR_ORDER) * bar_w) / (len(VECTOR_ORDER) + 1)
    for i, vector in enumerate(VECTOR_ORDER):
        group = [r for r in rows if r["attack_vector"] == vector]
        total = len(group)
        count = sum(r["attack_success"] == "True" for r in group)
        rate = pct(count, total)
        lo, hi = wilson_ci(count, total)
        x = left + gap + i * (bar_w + gap)
        y = y_scale(rate, top, bottom)
        svg.rect(x, y, bar_w, bottom - y, COLORS[vector])
        xmid = x + bar_w / 2
        svg.line(xmid, y_scale(lo, top, bottom), xmid, y_scale(hi, top, bottom), "#333333", 4)
        svg.line(xmid - 24, y_scale(lo, top, bottom), xmid + 24, y_scale(lo, top, bottom), "#333333", 4)
        svg.line(xmid - 24, y_scale(hi, top, bottom), xmid + 24, y_scale(hi, top, bottom), "#333333", 4)
        label_y = max(top + 42, y_scale(hi, top, bottom) - 26)
        svg.rect(xmid - 46, label_y - 28, 92, 38, "#ffffff", rx=4)
        svg.text(xmid, label_y, f"{fmt_pct(rate)}", cls="value", anchor="middle")
        svg.text(xmid, bottom + 50, VECTOR_LABELS[vector], cls="label", anchor="middle")
        svg.text(xmid, bottom + 82, f"{count}/{total}", cls="small", anchor="middle")
    svg.save(FIG_DIR / "fig1_attack_success_by_vector.svg")


def figure_2(rows: list[dict[str, str]]):
    svg = Svg(1800, 1800)
    svg.text(900, 58, "Outcome Cascade by Attack Vector", cls="title", anchor="middle")
    svg.text(900, 91, "Proportion of readings mentioning the target, recommending follow-up, or meeting attack success criteria", cls="subtitle", anchor="middle")
    left, right, top, bottom = 150, 1710, 220, 1250
    draw_y_axis(svg, left, top, bottom, right)
    svg.text(52, (top + bottom) / 2, "Proportion of Cases", cls="label", anchor="middle", rotate=-90)

    metrics = [
        ("mentions_target_pathology", ["Mentions", "Target"]),
        ("recommends_followup", ["Recommends", "Follow-up"]),
        ("attack_success", ["Attack", "Success"]),
    ]
    group_w = 370
    bar_w = 72
    metric_gap = (right - left - len(metrics) * group_w) / (len(metrics) + 1)
    for mi, (field, label_lines) in enumerate(metrics):
        gx = left + metric_gap + mi * (group_w + metric_gap)
        for vi, vector in enumerate(VECTOR_ORDER):
            group = [r for r in rows if r["attack_vector"] == vector]
            total = len(group)
            count = sum(r[field] == "True" for r in group)
            rate = pct(count, total)
            x = gx + vi * (bar_w + 10)
            y = y_scale(rate, top, bottom)
            svg.rect(x, y, bar_w, bottom - y, COLORS[vector])
            if rate > 0:
                svg.text(x + bar_w / 2, y - 8, fmt_pct(rate), cls="small", anchor="middle", fill="#172026", weight=700)
        svg.multiline_text(gx + (len(VECTOR_ORDER) * bar_w + (len(VECTOR_ORDER) - 1) * 10) / 2, bottom + 48, label_lines, cls="label", anchor="middle")

    legend_x, legend_y = 1080, 170
    for i, vector in enumerate(VECTOR_ORDER):
        x = legend_x + (i % 2) * 260
        y = legend_y + (i // 2) * 36
        svg.rect(x, y - 18, 26, 18, COLORS[vector])
        svg.text(x + 38, y - 2, VECTOR_LABELS[vector], cls="small", anchor="start", fill="#172026", size=18)
    svg.save(FIG_DIR / "fig2_outcome_cascade.svg")


def heat_color(value: float) -> str:
    # Green -> pale yellow -> red.
    stops = [(0, (0, 104, 55)), (50, (255, 241, 160)), (100, (184, 0, 36))]
    if value <= 50:
        t = value / 50
        a, b = stops[0][1], stops[1][1]
    else:
        t = (value - 50) / 50
        a, b = stops[1][1], stops[2][1]
    rgb = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def figure_3(rows: list[dict[str, str]]):
    svg = Svg(1700, 1700)
    svg.text(850, 60, "Attack Success Rate by Vector and Target Pathology", cls="title", anchor="middle")
    svg.text(850, 92, "Final reviewed attack_success values", cls="subtitle", anchor="middle")
    left, top = 300, 220
    cell_w, cell_h = 360, 240
    for ri, vector in enumerate(VECTOR_ORDER):
        svg.text(left - 25, top + ri * cell_h + cell_h / 2 + 9, VECTOR_LABELS[vector], cls="label", anchor="end")
        for ci, target in enumerate(TARGET_ORDER):
            group = [r for r in rows if r["attack_vector"] == vector and r["assigned_target_pathology"] == target]
            total = len(group)
            count = sum(r["attack_success"] == "True" for r in group)
            rate = pct(count, total)
            x = left + ci * cell_w
            y = top + ri * cell_h
            fill = heat_color(rate)
            svg.rect(x, y, cell_w, cell_h, fill)
            text_fill = "#ffffff" if rate >= 55 or rate <= 8 else "#050607"
            svg.text(x + cell_w / 2, y + cell_h / 2 - 8, fmt_pct(rate), cls="value", anchor="middle", fill=text_fill)
            svg.text(x + cell_w / 2, y + cell_h / 2 + 28, f"{count}/{total}", cls="small", anchor="middle", fill=text_fill)
    for ci, target in enumerate(TARGET_ORDER):
        svg.text(left + ci * cell_w + cell_w / 2, top + len(VECTOR_ORDER) * cell_h + 55, target, cls="label", anchor="middle")

    # Colorbar.
    bar_x, bar_y, bar_w, bar_h = 1450, top, 34, cell_h * len(VECTOR_ORDER)
    steps = 100
    for i in range(steps):
        value = 100 - i
        y = bar_y + i * bar_h / steps
        svg.rect(bar_x, y, bar_w, bar_h / steps + 1, heat_color(value))
    svg.rect(bar_x, bar_y, bar_w, bar_h, "none", stroke="#172026", sw=2)
    for tick in range(0, 101, 20):
        y = bar_y + (100 - tick) / 100 * bar_h
        svg.line(bar_x + bar_w, y, bar_x + bar_w + 12, y, "#172026", 2)
        svg.text(bar_x + bar_w + 24, y + 7, f"{tick}%", cls="tick", anchor="start")
    svg.text(bar_x + 160, bar_y + bar_h / 2, "Attack Success Rate", cls="label", anchor="middle", rotate=-90)
    svg.save(FIG_DIR / "fig3_attack_success_heatmap.svg")


def figure_4(rows: list[dict[str, str]]):
    svg = Svg(1800, 1800)
    svg.text(900, 58, "Target Pathology Diagnosis Rate by Vector and Pathology", cls="title", anchor="middle")
    svg.text(900, 91, "Diagnosis rate uses diagnoses_target_pathology after radiologist adjudication of hedge/manual-review flags", cls="subtitle", anchor="middle")
    left, right, top, bottom = 150, 1710, 220, 1250
    draw_y_axis(svg, left, top, bottom, right)
    svg.text(52, (top + bottom) / 2, "Diagnosis Rate", cls="label", anchor="middle", rotate=-90)

    group_w = 380
    bar_w = 62
    gap = (right - left - len(TARGET_ORDER) * group_w) / (len(TARGET_ORDER) + 1)
    vector_order = ["control", "image_channel", "system_prompt", "user_prompt"]
    for ti, target in enumerate(TARGET_ORDER):
        gx = left + gap + ti * (group_w + gap)
        for vi, vector in enumerate(vector_order):
            group = [r for r in rows if r["attack_vector"] == vector and r["assigned_target_pathology"] == target]
            total = len(group)
            count = sum(r["diagnoses_target_pathology"] == "True" for r in group)
            rate = pct(count, total)
            x = gx + vi * (bar_w + 10)
            y = y_scale(rate, top, bottom)
            svg.rect(x, y, bar_w, bottom - y, COLORS[vector])
            if rate > 0:
                svg.text(x + bar_w / 2, y - 8, fmt_pct(rate), cls="small", anchor="middle", fill="#172026", weight=700)
        svg.text(gx + (len(vector_order) * bar_w + (len(vector_order) - 1) * 10) / 2, bottom + 55, target, cls="label", anchor="middle")

    legend_x, legend_y = 460, 170
    for i, vector in enumerate(vector_order):
        x = legend_x + i * 275
        svg.rect(x, legend_y - 18, 26, 18, COLORS[vector])
        svg.text(x + 38, legend_y - 2, VECTOR_LABELS[vector], cls="small", anchor="start", fill="#172026", size=18)
    svg.save(FIG_DIR / "fig4_diagnosis_rate_by_target.svg")


def figure_5(rows: list[dict[str, str]]):
    svg = Svg(1700, 1700)
    svg.text(850, 58, "Attack Success Rate by Target Pathology", cls="title", anchor="middle")
    svg.text(850, 91, "Attack conditions only; control rows excluded. Error bars show 95% Wilson confidence intervals", cls="subtitle", anchor="middle")
    left, right, top, bottom = 150, 1580, 220, 1220
    draw_y_axis(svg, left, top, bottom, right)
    svg.text(55, (top + bottom) / 2, "Attack Success Rate", cls="label", anchor="middle", rotate=-90)

    attack_rows = [r for r in rows if r["attack_vector"] != "control"]
    bar_w = 280
    gap = (right - left - len(TARGET_ORDER) * bar_w) / (len(TARGET_ORDER) + 1)
    for i, target in enumerate(TARGET_ORDER):
        group = [r for r in attack_rows if r["assigned_target_pathology"] == target]
        total = len(group)
        count = sum(r["attack_success"] == "True" for r in group)
        rate = pct(count, total)
        lo, hi = wilson_ci(count, total)
        x = left + gap + i * (bar_w + gap)
        y = y_scale(rate, top, bottom)
        svg.rect(x, y, bar_w, bottom - y, TARGET_COLORS[target])
        xmid = x + bar_w / 2
        svg.line(xmid, y_scale(lo, top, bottom), xmid, y_scale(hi, top, bottom), "#333333", 4)
        svg.line(xmid - 24, y_scale(lo, top, bottom), xmid + 24, y_scale(lo, top, bottom), "#333333", 4)
        svg.line(xmid - 24, y_scale(hi, top, bottom), xmid + 24, y_scale(hi, top, bottom), "#333333", 4)
        label_y = max(top + 42, y_scale(hi, top, bottom) - 26)
        svg.rect(xmid - 50, label_y - 28, 100, 38, "#ffffff", rx=4)
        svg.text(xmid, label_y, fmt_pct(rate), cls="value", anchor="middle")
        svg.text(xmid, bottom + 50, target, cls="label", anchor="middle")
        svg.text(xmid, bottom + 82, f"{count}/{total}", cls="small", anchor="middle")
    svg.save(FIG_DIR / "fig5_attack_success_by_target.svg")


def write_summary(rows: list[dict[str, str]]):
    summary_path = FIG_DIR / "figure_values_summary.csv"
    fields = ["figure", "attack_vector", "target_pathology", "metric", "count", "total", "percent"]
    records: list[dict[str, str | int | float]] = []

    for vector in VECTOR_ORDER:
        group = [r for r in rows if r["attack_vector"] == vector]
        for metric in ["mentions_target_pathology", "recommends_followup", "attack_success", "hedged_answer", "needs_manual_review"]:
            count = sum(r[metric] == "True" for r in group)
            records.append(
                {
                    "figure": "overall_by_vector",
                    "attack_vector": VECTOR_LABELS[vector],
                    "target_pathology": "All",
                    "metric": metric,
                    "count": count,
                    "total": len(group),
                    "percent": f"{pct(count, len(group)):.1f}",
                }
            )

    for vector in VECTOR_ORDER:
        for target in TARGET_ORDER:
            group = [r for r in rows if r["attack_vector"] == vector and r["assigned_target_pathology"] == target]
            count = sum(r["attack_success"] == "True" for r in group)
            records.append(
                {
                    "figure": "by_vector_and_target",
                    "attack_vector": VECTOR_LABELS[vector],
                    "target_pathology": target,
                    "metric": "attack_success",
                    "count": count,
                    "total": len(group),
                    "percent": f"{pct(count, len(group)):.1f}",
                }
            )

    attack_rows = [r for r in rows if r["attack_vector"] != "control"]
    for target in TARGET_ORDER:
        group = [r for r in attack_rows if r["assigned_target_pathology"] == target]
        count = sum(r["attack_success"] == "True" for r in group)
        records.append(
            {
                "figure": "attack_conditions_by_target",
                "attack_vector": "All attack vectors",
                "target_pathology": target,
                "metric": "attack_success",
                "count": count,
                "total": len(group),
                "percent": f"{pct(count, len(group)):.1f}",
            }
        )

    with summary_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def main() -> int:
    rows = read_rows()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    figure_1(rows)
    figure_2(rows)
    figure_3(rows)
    figure_4(rows)
    figure_5(rows)
    write_summary(rows)
    print(f"Wrote figures to {FIG_DIR}")
    print(f"Rows used: {len(rows)}")
    print(f"Attack successes: {sum(r['attack_success'] == 'True' for r in rows)}")
    print(f"Hedged rows: {sum(r['hedged_answer'] == 'True' for r in rows)}")
    print(f"Manual-review rows: {sum(r['needs_manual_review'] == 'True' for r in rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

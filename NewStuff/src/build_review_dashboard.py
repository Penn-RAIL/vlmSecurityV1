#!/usr/bin/env python3
"""Build a standalone HTML review dashboard for radiologist adjudication."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUTCOMES = RESULTS / "extracted_outcomes_final_sample_v2.csv"
RAW_OUTPUTS = RESULTS / "raw_outputs_final_sample.jsonl"
REVIEW_HTML = RESULTS / "review_dashboard.html"
REVIEW_CSV = RESULTS / "radiologist_review.csv"

REVIEW_FIELDS = [
    "job_id",
    "sample_id",
    "condition_id",
    "attack_vector",
    "assigned_target_pathology",
    "original_attack_success",
    "review_attack_success",
    "final_attack_success",
    "original_hedged",
    "review_hedged",
    "final_hedged",
    "needs_manual_review",
    "reviewer_notes",
    "reviewed_at",
]


def read_outcomes() -> dict[str, dict[str, str]]:
    with OUTCOMES.open(newline="", encoding="utf-8") as f:
        return {row["job_id"]: row for row in csv.DictReader(f)}


def read_raw_outputs() -> dict[str, dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    with RAW_OUTPUTS.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            records[record["job_id"]] = record
    return records


def make_records() -> list[dict[str, str]]:
    outcomes = read_outcomes()
    raw = read_raw_outputs()
    records: list[dict[str, str]] = []
    for job_id in sorted(outcomes):
        outcome = outcomes[job_id]
        raw_record = raw.get(job_id, {})
        image_path = raw_record.get("image_path", "")
        records.append(
            {
                "job_id": job_id,
                "sample_id": outcome.get("sample_id", ""),
                "condition_id": outcome.get("condition_id", ""),
                "attack_vector": outcome.get("attack_vector", ""),
                "assigned_target_slug": outcome.get("assigned_target_slug", ""),
                "assigned_target_pathology": outcome.get("assigned_target_pathology", ""),
                "attack_success": outcome.get("attack_success", ""),
                "hedged_answer": outcome.get("hedged_answer", ""),
                "hedge_reason": outcome.get("hedge_reason", ""),
                "needs_manual_review": outcome.get("needs_manual_review", ""),
                "review_reason": outcome.get("review_reason", ""),
                "mentions_target_pathology": outcome.get("mentions_target_pathology", ""),
                "diagnoses_target_pathology": outcome.get("diagnoses_target_pathology", ""),
                "negates_target_pathology": outcome.get("negates_target_pathology", ""),
                "label_acknowledged": outcome.get("label_acknowledged", ""),
                "label_rejected": outcome.get("label_rejected", ""),
                "positive_evidence": outcome.get("positive_evidence", ""),
                "negation_evidence": outcome.get("negation_evidence", ""),
                "label_evidence": outcome.get("label_evidence", ""),
                "image_path": image_path,
                "image_src": f"../{image_path}" if image_path else "",
                "raw_output": raw_record.get("raw_output", ""),
            }
        )
    return records


def write_review_csv(records: list[dict[str, str]]) -> None:
    if REVIEW_CSV.exists():
        return
    with REVIEW_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "job_id": record["job_id"],
                    "sample_id": record["sample_id"],
                    "condition_id": record["condition_id"],
                    "attack_vector": record["attack_vector"],
                    "assigned_target_pathology": record["assigned_target_pathology"],
                    "original_attack_success": record["attack_success"],
                    "review_attack_success": "",
                    "final_attack_success": record["attack_success"],
                    "original_hedged": record["hedged_answer"],
                    "review_hedged": "",
                    "final_hedged": record["hedged_answer"],
                    "needs_manual_review": record["needs_manual_review"],
                    "reviewer_notes": "",
                    "reviewed_at": "",
                }
            )


HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>VLM Radiology Review Dashboard</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f5f7f8;
      --surface: #ffffff;
      --ink: #172026;
      --muted: #66737d;
      --line: #d9e0e4;
      --line-strong: #bac6cc;
      --accent: #0b6b61;
      --accent-dark: #084d47;
      --success: #0b6b2d;
      --danger: #9d241f;
      --warn: #a06000;
      --review: #5b3a91;
      --shadow: 0 14px 40px rgba(25, 39, 52, 0.08);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--ink);
    }

    button, input, select, textarea {
      font: inherit;
    }

    .app {
      display: grid;
      grid-template-rows: auto 1fr;
      min-height: 100vh;
    }

    header {
      background: var(--surface);
      border-bottom: 1px solid var(--line);
      padding: 18px 24px 16px;
      position: sticky;
      top: 0;
      z-index: 20;
    }

    .topline {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 14px;
    }

    h1 {
      margin: 0;
      font-size: 22px;
      line-height: 1.2;
      letter-spacing: 0;
    }

    .meta {
      color: var(--muted);
      font-size: 13px;
      margin-top: 4px;
    }

    .actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }

    .button, .file-label {
      border: 1px solid var(--line-strong);
      background: var(--surface);
      color: var(--ink);
      min-height: 34px;
      padding: 7px 12px;
      border-radius: 6px;
      cursor: pointer;
      transition: background 120ms ease, border-color 120ms ease, transform 120ms ease;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      white-space: nowrap;
    }

    .button:hover, .file-label:hover {
      border-color: var(--accent);
      background: #f1faf8;
      transform: translateY(-1px);
    }

    .button.primary {
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
    }

    .button.primary:hover {
      background: var(--accent-dark);
    }

    input[type="file"] {
      display: none;
    }

    .stats {
      display: grid;
      grid-template-columns: repeat(5, minmax(120px, 1fr));
      gap: 8px;
      margin-bottom: 14px;
    }

    .stat {
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 10px 12px;
      background: #fbfcfd;
      min-height: 62px;
    }

    .stat-label {
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 4px;
    }

    .stat-value {
      font-size: 21px;
      font-weight: 700;
    }

    .filters {
      display: grid;
      grid-template-columns: minmax(220px, 1.6fr) repeat(5, minmax(125px, 1fr));
      gap: 8px;
    }

    .filters input, .filters select {
      width: 100%;
      border: 1px solid var(--line-strong);
      border-radius: 6px;
      min-height: 36px;
      background: var(--surface);
      color: var(--ink);
      padding: 7px 10px;
    }

    main {
      display: grid;
      grid-template-columns: minmax(420px, 46%) 1fr;
      min-height: 0;
    }

    .list-pane {
      border-right: 1px solid var(--line);
      background: var(--surface);
      min-height: 0;
      overflow: hidden;
      display: grid;
      grid-template-rows: auto 1fr;
    }

    .list-summary {
      padding: 12px 16px;
      color: var(--muted);
      font-size: 13px;
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      gap: 12px;
    }

    .rows {
      overflow: auto;
      min-height: 0;
    }

    table {
      border-collapse: collapse;
      width: 100%;
      table-layout: fixed;
    }

    th {
      position: sticky;
      top: 0;
      z-index: 5;
      background: #f7f9fa;
      color: var(--muted);
      font-size: 11px;
      text-align: left;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      border-bottom: 1px solid var(--line);
      padding: 9px 10px;
    }

    td {
      border-bottom: 1px solid var(--line);
      padding: 10px;
      vertical-align: top;
      font-size: 13px;
    }

    tr {
      cursor: pointer;
      transition: background 120ms ease;
    }

    tr:hover {
      background: #f4faf9;
    }

    tr.selected {
      background: #e9f7f4;
      box-shadow: inset 3px 0 0 var(--accent);
    }

    .job-cell {
      font-weight: 700;
      color: var(--ink);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .sub {
      color: var(--muted);
      font-size: 12px;
      margin-top: 3px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .chip {
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      padding: 3px 7px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      border: 1px solid transparent;
      white-space: nowrap;
    }

    .chip.true {
      color: var(--success);
      background: #e9f6ec;
      border-color: #b7dec1;
    }

    .chip.false {
      color: var(--danger);
      background: #fff0ef;
      border-color: #edc0bd;
    }

    .chip.hedged {
      color: var(--warn);
      background: #fff6e8;
      border-color: #f2d39b;
    }

    .chip.review {
      color: var(--review);
      background: #f1ebff;
      border-color: #d5c4fa;
    }

    .detail-pane {
      min-width: 0;
      min-height: 0;
      overflow: auto;
      padding: 20px 22px 40px;
    }

    .detail-grid {
      display: grid;
      grid-template-columns: minmax(280px, 38%) 1fr;
      gap: 18px;
      align-items: start;
    }

    .panel {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      overflow: hidden;
    }

    .panel-head {
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }

    .panel-title {
      margin: 0;
      font-size: 15px;
      font-weight: 800;
    }

    .image-stage {
      background: #0e1519;
      min-height: 360px;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 12px;
    }

    .image-stage img {
      display: block;
      max-width: 100%;
      max-height: 68vh;
      object-fit: contain;
      border-radius: 4px;
    }

    .facts {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      padding: 14px 16px 16px;
    }

    .fact {
      min-width: 0;
    }

    .fact-label {
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-bottom: 3px;
    }

    .fact-value {
      font-size: 13px;
      font-weight: 700;
      overflow-wrap: anywhere;
    }

    .review-box {
      padding: 16px;
      display: grid;
      gap: 14px;
    }

    .review-row {
      display: grid;
      grid-template-columns: 150px 1fr;
      gap: 10px;
      align-items: start;
    }

    .review-label {
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      padding-top: 7px;
    }

    .segmented {
      display: inline-flex;
      flex-wrap: wrap;
      gap: 6px;
    }

    .segmented button {
      border: 1px solid var(--line-strong);
      background: #fff;
      border-radius: 6px;
      min-height: 34px;
      padding: 7px 10px;
      cursor: pointer;
      color: var(--ink);
    }

    .segmented button.active {
      border-color: var(--accent);
      background: #dff3ef;
      color: var(--accent-dark);
      font-weight: 800;
    }

    textarea {
      width: 100%;
      min-height: 90px;
      border: 1px solid var(--line-strong);
      border-radius: 6px;
      resize: vertical;
      padding: 10px;
      color: var(--ink);
      background: #fff;
    }

    .raw-output {
      padding: 18px 20px 24px;
      line-height: 1.55;
      font-size: 14px;
    }

    .raw-output h1, .raw-output h2, .raw-output h3, .raw-output h4 {
      margin: 14px 0 8px;
      line-height: 1.25;
      letter-spacing: 0;
    }

    .raw-output h1 { font-size: 20px; }
    .raw-output h2 { font-size: 18px; }
    .raw-output h3, .raw-output h4 { font-size: 16px; }
    .raw-output p { margin: 0 0 11px; }
    .raw-output ul, .raw-output ol { margin: 0 0 13px 22px; padding: 0; }
    .raw-output li { margin: 5px 0; }
    .raw-output code {
      background: #eef2f4;
      border: 1px solid var(--line);
      padding: 1px 4px;
      border-radius: 4px;
    }

    .empty {
      padding: 30px;
      text-align: center;
      color: var(--muted);
    }

    .path {
      padding: 10px 12px;
      color: #b6c4cc;
      background: #0e1519;
      font-size: 12px;
      border-top: 1px solid #23313a;
      overflow-wrap: anywhere;
    }

    .changed {
      color: var(--accent-dark);
      font-weight: 800;
    }

    @media (max-width: 1100px) {
      main {
        grid-template-columns: 1fr;
      }
      .list-pane {
        border-right: 0;
        border-bottom: 1px solid var(--line);
        max-height: 48vh;
      }
      .detail-grid {
        grid-template-columns: 1fr;
      }
      .filters {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .stats {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 700px) {
      header {
        padding: 14px;
      }
      .topline {
        align-items: flex-start;
        flex-direction: column;
      }
      .actions {
        justify-content: flex-start;
      }
      .filters {
        grid-template-columns: 1fr;
      }
      .review-row {
        grid-template-columns: 1fr;
      }
      .detail-pane {
        padding: 14px;
      }
    }
  </style>
</head>
<body>
  <div class="app">
    <header>
      <div class="topline">
        <div>
          <h1>VLM Radiology Review Dashboard</h1>
          <div class="meta">Review model outputs, adjudicate attack success and hedging, then export a reviewer CSV.</div>
        </div>
        <div class="actions">
          <label class="file-label" for="reviewFile">Load review CSV</label>
          <input id="reviewFile" type="file" accept=".csv,text/csv">
          <button class="button" id="clearOverrides" type="button">Clear browser edits</button>
          <button class="button primary" id="downloadCsv" type="button">Download review CSV</button>
        </div>
      </div>

      <div class="stats" id="stats"></div>

      <div class="filters">
        <input id="search" type="search" placeholder="Search job, target, vector, or raw output">
        <select id="filterVector">
          <option value="">All attack vectors</option>
        </select>
        <select id="filterPathology">
          <option value="">All pathologies</option>
        </select>
        <select id="filterSuccess">
          <option value="">Attack success: all</option>
          <option value="True">Attack success: true</option>
          <option value="False">Attack success: false</option>
        </select>
        <select id="filterHedged">
          <option value="">Hedged: all</option>
          <option value="True">Hedged: true</option>
          <option value="False">Hedged: false</option>
        </select>
        <select id="filterReview">
          <option value="">Manual review: all</option>
          <option value="True">Manual review: true</option>
          <option value="False">Manual review: false</option>
        </select>
      </div>
    </header>

    <main>
      <section class="list-pane">
        <div class="list-summary">
          <span id="rowCount">0 rows</span>
          <span id="overrideCount">0 reviewer edits</span>
        </div>
        <div class="rows">
          <table>
            <thead>
              <tr>
                <th style="width: 28%">Job</th>
                <th style="width: 20%">Vector</th>
                <th style="width: 24%">Target</th>
                <th style="width: 14%">Success</th>
                <th style="width: 14%">Flags</th>
              </tr>
            </thead>
            <tbody id="rows"></tbody>
          </table>
        </div>
      </section>

      <section class="detail-pane">
        <div id="detail" class="empty">Select a row to review the image and raw output.</div>
      </section>
    </main>
  </div>

  <script id="records-data" type="application/json">__RECORDS_JSON__</script>
  <script>
    const records = JSON.parse(document.getElementById('records-data').textContent);
    const storageKey = 'vlm-radiologist-review-v2';
    let overrides = loadOverrides();
    let filtered = records.slice();
    let selectedId = records[0]?.job_id || null;

    const elements = {
      rows: document.getElementById('rows'),
      detail: document.getElementById('detail'),
      stats: document.getElementById('stats'),
      rowCount: document.getElementById('rowCount'),
      overrideCount: document.getElementById('overrideCount'),
      search: document.getElementById('search'),
      filterVector: document.getElementById('filterVector'),
      filterPathology: document.getElementById('filterPathology'),
      filterSuccess: document.getElementById('filterSuccess'),
      filterHedged: document.getElementById('filterHedged'),
      filterReview: document.getElementById('filterReview'),
      reviewFile: document.getElementById('reviewFile'),
      downloadCsv: document.getElementById('downloadCsv'),
      clearOverrides: document.getElementById('clearOverrides'),
    };

    function loadOverrides() {
      try {
        return JSON.parse(localStorage.getItem(storageKey) || '{}');
      } catch {
        return {};
      }
    }

    function saveOverrides() {
      localStorage.setItem(storageKey, JSON.stringify(overrides));
    }

    function canonicalBool(value) {
      if (value === true || value === 'true' || value === 'True' || value === '1' || value === 1) return 'True';
      if (value === false || value === 'false' || value === 'False' || value === '0' || value === 0) return 'False';
      return '';
    }

    function overrideFor(jobId) {
      return overrides[jobId] || {};
    }

    function effectiveValue(record, field) {
      const override = overrideFor(record.job_id);
      if (field === 'attack_success') {
        return canonicalBool(override.review_attack_success) || canonicalBool(record.attack_success);
      }
      if (field === 'hedged_answer') {
        return canonicalBool(override.review_hedged) || canonicalBool(record.hedged_answer);
      }
      return '';
    }

    function isChanged(record, field) {
      const override = overrideFor(record.job_id);
      if (field === 'attack_success') {
        const v = canonicalBool(override.review_attack_success);
        return v && v !== canonicalBool(record.attack_success);
      }
      if (field === 'hedged_answer') {
        const v = canonicalBool(override.review_hedged);
        return v && v !== canonicalBool(record.hedged_answer);
      }
      return false;
    }

    function setOptions(select, values) {
      const current = select.value;
      values.forEach(value => {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = value.replaceAll('_', ' ');
        select.appendChild(option);
      });
      select.value = current;
    }

    function initFilters() {
      setOptions(elements.filterVector, [...new Set(records.map(r => r.attack_vector))].sort());
      setOptions(elements.filterPathology, [...new Set(records.map(r => r.assigned_target_pathology))].sort());
      ['search', 'filterVector', 'filterPathology', 'filterSuccess', 'filterHedged', 'filterReview'].forEach(id => {
        elements[id].addEventListener('input', applyFilters);
        elements[id].addEventListener('change', applyFilters);
      });
    }

    function applyFilters() {
      const q = elements.search.value.trim().toLowerCase();
      filtered = records.filter(record => {
        const success = effectiveValue(record, 'attack_success');
        const hedged = effectiveValue(record, 'hedged_answer');
        const review = canonicalBool(record.needs_manual_review);
        if (elements.filterVector.value && record.attack_vector !== elements.filterVector.value) return false;
        if (elements.filterPathology.value && record.assigned_target_pathology !== elements.filterPathology.value) return false;
        if (elements.filterSuccess.value && success !== elements.filterSuccess.value) return false;
        if (elements.filterHedged.value && hedged !== elements.filterHedged.value) return false;
        if (elements.filterReview.value && review !== elements.filterReview.value) return false;
        if (!q) return true;
        const haystack = [
          record.job_id,
          record.sample_id,
          record.attack_vector,
          record.assigned_target_pathology,
          record.raw_output,
          record.hedge_reason,
          record.review_reason,
          overrideFor(record.job_id).reviewer_notes || '',
        ].join(' ').toLowerCase();
        return haystack.includes(q);
      });
      if (!filtered.some(record => record.job_id === selectedId)) {
        selectedId = filtered[0]?.job_id || null;
      }
      render();
    }

    function chip(value, kind = '') {
      const v = canonicalBool(value);
      if (v === 'True') return `<span class="chip true ${kind}">True</span>`;
      if (v === 'False') return `<span class="chip false ${kind}">False</span>`;
      return '<span class="chip">Blank</span>';
    }

    function flagChips(record) {
      const flags = [];
      if (effectiveValue(record, 'hedged_answer') === 'True') flags.push('<span class="chip hedged">Hedged</span>');
      if (canonicalBool(record.needs_manual_review) === 'True') flags.push('<span class="chip review">Review</span>');
      return flags.join(' ') || '<span class="sub">None</span>';
    }

    function renderStats() {
      const total = filtered.length;
      const success = filtered.filter(r => effectiveValue(r, 'attack_success') === 'True').length;
      const hedged = filtered.filter(r => effectiveValue(r, 'hedged_answer') === 'True').length;
      const review = filtered.filter(r => canonicalBool(r.needs_manual_review) === 'True').length;
      const edited = records.filter(r => {
        const o = overrideFor(r.job_id);
        return canonicalBool(o.review_attack_success) || canonicalBool(o.review_hedged) || (o.reviewer_notes || '').trim();
      }).length;
      const stats = [
        ['Visible rows', total],
        ['Attack success', success],
        ['Hedged', hedged],
        ['Manual review', review],
        ['Reviewer edits', edited],
      ];
      elements.stats.innerHTML = stats.map(([label, value]) => `
        <div class="stat">
          <div class="stat-label">${escapeHtml(label)}</div>
          <div class="stat-value">${value}</div>
        </div>
      `).join('');
      elements.rowCount.textContent = `${total} visible of ${records.length}`;
      elements.overrideCount.textContent = `${edited} reviewer edits`;
    }

    function renderRows() {
      elements.rows.innerHTML = filtered.map(record => {
        const selected = record.job_id === selectedId ? 'selected' : '';
        const successChanged = isChanged(record, 'attack_success') ? ' changed' : '';
        const hedgedChanged = isChanged(record, 'hedged_answer') ? ' changed' : '';
        return `
          <tr class="${selected}" data-job-id="${escapeAttr(record.job_id)}">
            <td>
              <div class="job-cell">${escapeHtml(record.job_id)}</div>
              <div class="sub">${escapeHtml(record.condition_id)} · ${escapeHtml(record.sample_id)}</div>
            </td>
            <td>${escapeHtml(record.attack_vector.replaceAll('_', ' '))}</td>
            <td>
              <div>${escapeHtml(record.assigned_target_pathology)}</div>
              <div class="sub">${escapeHtml(record.assigned_target_slug.replaceAll('_', ' '))}</div>
            </td>
            <td>
              <span class="${successChanged.trim()}">${chip(effectiveValue(record, 'attack_success'))}</span>
              ${successChanged ? '<div class="sub changed">review override</div>' : ''}
            </td>
            <td>
              <span class="${hedgedChanged.trim()}">${flagChips(record)}</span>
              ${hedgedChanged ? '<div class="sub changed">review override</div>' : ''}
            </td>
          </tr>
        `;
      }).join('');
      elements.rows.querySelectorAll('tr[data-job-id]').forEach(row => {
        row.addEventListener('click', () => {
          selectedId = row.dataset.jobId;
          render();
        });
      });
    }

    function renderDetail() {
      const record = records.find(r => r.job_id === selectedId);
      if (!record) {
        elements.detail.className = 'empty';
        elements.detail.textContent = 'No rows match the current filters.';
        return;
      }
      elements.detail.className = '';
      const override = overrideFor(record.job_id);
      const finalSuccess = effectiveValue(record, 'attack_success');
      const finalHedged = effectiveValue(record, 'hedged_answer');
      elements.detail.innerHTML = `
        <div class="detail-grid">
          <div class="panel">
            <div class="panel-head">
              <h2 class="panel-title">${escapeHtml(record.job_id)}</h2>
              <div>${chip(finalSuccess)}</div>
            </div>
            <div class="image-stage">
              ${record.image_src ? `<img src="${escapeAttr(record.image_src)}" alt="Radiograph for ${escapeAttr(record.job_id)}">` : '<div class="empty">No image path</div>'}
            </div>
            <div class="path">${escapeHtml(record.image_path || 'No image path')}</div>
            <div class="facts">
              ${fact('Attack vector', record.attack_vector.replaceAll('_', ' '))}
              ${fact('Target', record.assigned_target_pathology)}
              ${fact('Original success', canonicalBool(record.attack_success))}
              ${fact('Displayed success', finalSuccess)}
              ${fact('Original hedged', canonicalBool(record.hedged_answer))}
              ${fact('Displayed hedged', finalHedged)}
              ${fact('Needs manual review', canonicalBool(record.needs_manual_review))}
              ${fact('Review reason', record.review_reason || 'None')}
              ${fact('Hedge reason', record.hedge_reason || 'None')}
              ${fact('Label acknowledged', canonicalBool(record.label_acknowledged))}
            </div>
          </div>

          <div>
            <div class="panel" style="margin-bottom: 18px;">
              <div class="panel-head">
                <h2 class="panel-title">Radiologist adjudication</h2>
                <button class="button" id="clearCurrent" type="button">Clear this row</button>
              </div>
              <div class="review-box">
                <div class="review-row">
                  <div class="review-label">Attack success</div>
                  <div class="segmented" data-field="review_attack_success">
                    ${segmentButton('True', override.review_attack_success)}
                    ${segmentButton('False', override.review_attack_success)}
                    ${segmentButton('', override.review_attack_success, 'Use original')}
                  </div>
                </div>
                <div class="review-row">
                  <div class="review-label">Hedged</div>
                  <div class="segmented" data-field="review_hedged">
                    ${segmentButton('True', override.review_hedged)}
                    ${segmentButton('False', override.review_hedged)}
                    ${segmentButton('', override.review_hedged, 'Use original')}
                  </div>
                </div>
                <div class="review-row">
                  <div class="review-label">Notes</div>
                  <textarea id="reviewNotes" placeholder="Optional radiologist notes">${escapeHtml(override.reviewer_notes || '')}</textarea>
                </div>
              </div>
            </div>

            <div class="panel">
              <div class="panel-head">
                <h2 class="panel-title">Raw output</h2>
                <div>${flagChips(record)}</div>
              </div>
              <div class="raw-output">${renderMarkdown(record.raw_output || '')}</div>
            </div>
          </div>
        </div>
      `;

      elements.detail.querySelectorAll('.segmented button').forEach(button => {
        button.addEventListener('click', () => {
          const field = button.closest('.segmented').dataset.field;
          updateOverride(record.job_id, field, button.dataset.value);
        });
      });
      elements.detail.querySelector('#reviewNotes').addEventListener('input', event => {
        updateOverride(record.job_id, 'reviewer_notes', event.target.value, false);
      });
      elements.detail.querySelector('#clearCurrent').addEventListener('click', () => {
        delete overrides[record.job_id];
        saveOverrides();
        applyFilters();
      });
    }

    function fact(label, value) {
      return `
        <div class="fact">
          <div class="fact-label">${escapeHtml(label)}</div>
          <div class="fact-value">${escapeHtml(value || '')}</div>
        </div>
      `;
    }

    function segmentButton(value, current, label = null) {
      const selected = canonicalBool(current) === canonicalBool(value) || (!value && !canonicalBool(current));
      return `<button type="button" data-value="${escapeAttr(value)}" class="${selected ? 'active' : ''}">${escapeHtml(label || value)}</button>`;
    }

    function updateOverride(jobId, field, value, rerender = true) {
      overrides[jobId] ||= {};
      overrides[jobId][field] = value;
      overrides[jobId].reviewed_at = new Date().toISOString();
      const empty = !canonicalBool(overrides[jobId].review_attack_success)
        && !canonicalBool(overrides[jobId].review_hedged)
        && !(overrides[jobId].reviewer_notes || '').trim();
      if (empty) delete overrides[jobId];
      saveOverrides();
      if (rerender) applyFilters();
      else renderStats();
    }

    function render() {
      renderStats();
      renderRows();
      renderDetail();
    }

    function escapeHtml(value) {
      return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
    }

    function escapeAttr(value) {
      return escapeHtml(value).replaceAll('\n', ' ');
    }

    function renderInlineMarkdown(value) {
      let text = escapeHtml(value);
      text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
      text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
      text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
      return text;
    }

    function renderMarkdown(markdown) {
      const lines = String(markdown || '').replace(/\r\n/g, '\n').split('\n');
      let html = '';
      let listType = null;
      const closeList = () => {
        if (listType) {
          html += `</${listType}>`;
          listType = null;
        }
      };
      for (const rawLine of lines) {
        const line = rawLine.trim();
        if (!line) {
          closeList();
          continue;
        }
        const heading = line.match(/^(#{1,4})\s+(.+)$/);
        if (heading) {
          closeList();
          const level = heading[1].length;
          html += `<h${level}>${renderInlineMarkdown(heading[2])}</h${level}>`;
          continue;
        }
        const bullet = line.match(/^[-*]\s+(.+)$/);
        if (bullet) {
          if (listType !== 'ul') {
            closeList();
            html += '<ul>';
            listType = 'ul';
          }
          html += `<li>${renderInlineMarkdown(bullet[1])}</li>`;
          continue;
        }
        const numbered = line.match(/^\d+[.)]\s+(.+)$/);
        if (numbered) {
          if (listType !== 'ol') {
            closeList();
            html += '<ol>';
            listType = 'ol';
          }
          html += `<li>${renderInlineMarkdown(numbered[1])}</li>`;
          continue;
        }
        closeList();
        html += `<p>${renderInlineMarkdown(line)}</p>`;
      }
      closeList();
      return html || '<p>No raw output.</p>';
    }

    function parseCsv(text) {
      const rows = [];
      let row = [];
      let cell = '';
      let inQuotes = false;
      for (let i = 0; i < text.length; i++) {
        const char = text[i];
        const next = text[i + 1];
        if (char === '"' && inQuotes && next === '"') {
          cell += '"';
          i++;
        } else if (char === '"') {
          inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
          row.push(cell);
          cell = '';
        } else if ((char === '\n' || char === '\r') && !inQuotes) {
          if (char === '\r' && next === '\n') i++;
          row.push(cell);
          if (row.some(value => value !== '')) rows.push(row);
          row = [];
          cell = '';
        } else {
          cell += char;
        }
      }
      row.push(cell);
      if (row.some(value => value !== '')) rows.push(row);
      const headers = rows.shift() || [];
      return rows.map(values => Object.fromEntries(headers.map((header, index) => [header, values[index] || ''])));
    }

    function csvEscape(value) {
      const text = String(value ?? '');
      if (/[",\n\r]/.test(text)) return `"${text.replaceAll('"', '""')}"`;
      return text;
    }

    function buildReviewRows() {
      return records.map(record => {
        const override = overrideFor(record.job_id);
        const reviewSuccess = canonicalBool(override.review_attack_success);
        const reviewHedged = canonicalBool(override.review_hedged);
        return {
          job_id: record.job_id,
          sample_id: record.sample_id,
          condition_id: record.condition_id,
          attack_vector: record.attack_vector,
          assigned_target_pathology: record.assigned_target_pathology,
          original_attack_success: canonicalBool(record.attack_success),
          review_attack_success: reviewSuccess,
          final_attack_success: reviewSuccess || canonicalBool(record.attack_success),
          original_hedged: canonicalBool(record.hedged_answer),
          review_hedged: reviewHedged,
          final_hedged: reviewHedged || canonicalBool(record.hedged_answer),
          needs_manual_review: canonicalBool(record.needs_manual_review),
          reviewer_notes: override.reviewer_notes || '',
          reviewed_at: override.reviewed_at || '',
        };
      });
    }

    function downloadReviewCsv() {
      const fields = [
        'job_id',
        'sample_id',
        'condition_id',
        'attack_vector',
        'assigned_target_pathology',
        'original_attack_success',
        'review_attack_success',
        'final_attack_success',
        'original_hedged',
        'review_hedged',
        'final_hedged',
        'needs_manual_review',
        'reviewer_notes',
        'reviewed_at',
      ];
      const rows = buildReviewRows();
      const csv = [fields.join(',')].concat(rows.map(row => fields.map(field => csvEscape(row[field])).join(','))).join('\n');
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'radiologist_review.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    }

    function loadReviewCsv(file) {
      const reader = new FileReader();
      reader.onload = () => {
        const rows = parseCsv(String(reader.result || ''));
        for (const row of rows) {
          if (!row.job_id) continue;
          overrides[row.job_id] ||= {};
          overrides[row.job_id].review_attack_success = canonicalBool(row.review_attack_success) || '';
          overrides[row.job_id].review_hedged = canonicalBool(row.review_hedged) || '';
          overrides[row.job_id].reviewer_notes = row.reviewer_notes || '';
          overrides[row.job_id].reviewed_at = row.reviewed_at || '';
          const empty = !overrides[row.job_id].review_attack_success
            && !overrides[row.job_id].review_hedged
            && !overrides[row.job_id].reviewer_notes.trim();
          if (empty) delete overrides[row.job_id];
        }
        saveOverrides();
        applyFilters();
      };
      reader.readAsText(file);
    }

    elements.downloadCsv.addEventListener('click', downloadReviewCsv);
    elements.reviewFile.addEventListener('change', event => {
      const file = event.target.files?.[0];
      if (file) loadReviewCsv(file);
      event.target.value = '';
    });
    elements.clearOverrides.addEventListener('click', () => {
      if (!confirm('Clear all reviewer edits saved in this browser?')) return;
      overrides = {};
      saveOverrides();
      applyFilters();
    });

    initFilters();
    applyFilters();
  </script>
</body>
</html>
"""


def write_html(records: list[dict[str, str]]) -> None:
    records_json = json.dumps(records, ensure_ascii=False)
    REVIEW_HTML.write_text(HTML_TEMPLATE.replace("__RECORDS_JSON__", records_json), encoding="utf-8")


def main() -> int:
    records = make_records()
    write_review_csv(records)
    write_html(records)
    print(f"Wrote {REVIEW_HTML.relative_to(ROOT)}")
    print(f"Wrote {REVIEW_CSV.relative_to(ROOT)}")
    print(f"Embedded records: {len(records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

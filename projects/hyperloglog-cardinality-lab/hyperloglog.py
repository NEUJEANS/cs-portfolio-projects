import argparse
import csv
import hashlib
import io
import json
import math
import random
from pathlib import Path
from typing import Any, Iterable

MAX_HASH_BITS = 64
MAX_HASH_VALUE = 1 << MAX_HASH_BITS
MISSING = object()


class HyperLogLog:
    def __init__(self, precision: int = 10, registers: list[int] | None = None):
        if not (4 <= precision <= 16):
            raise ValueError("precision must be between 4 and 16")
        self.precision = precision
        self.register_count = 1 << precision
        self.registers = list(registers or [0] * self.register_count)
        if len(self.registers) != self.register_count:
            raise ValueError("register count does not match precision")

    @classmethod
    def from_dict(cls, data: dict) -> "HyperLogLog":
        return cls(precision=data["precision"], registers=data["registers"])

    def to_dict(self) -> dict:
        return {
            "precision": self.precision,
            "register_count": self.register_count,
            "registers": self.registers,
        }

    def _hash(self, item: str) -> int:
        digest = hashlib.sha1(item.encode("utf-8")).digest()
        return int.from_bytes(digest[:8], "big")

    def _split_hash(self, hashed: int) -> tuple[int, int]:
        suffix_width = MAX_HASH_BITS - self.precision
        index = hashed >> suffix_width
        remainder_mask = (1 << suffix_width) - 1
        remainder = hashed & remainder_mask
        rank = self._rho(remainder, suffix_width)
        return index, rank

    @staticmethod
    def _rho(value: int, width: int) -> int:
        if value == 0:
            return width + 1
        leading_zeros = width - value.bit_length()
        return leading_zeros + 1

    def add(self, item: str) -> None:
        index, rank = self._split_hash(self._hash(item))
        self.registers[index] = max(self.registers[index], rank)

    def extend(self, items: Iterable[str]) -> int:
        inserted = 0
        for item in items:
            normalized = item.strip()
            if not normalized:
                continue
            self.add(normalized)
            inserted += 1
        return inserted

    def merge(self, other: "HyperLogLog") -> "HyperLogLog":
        if self.precision != other.precision:
            raise ValueError("cannot merge HyperLogLogs with different precisions")
        return HyperLogLog(
            precision=self.precision,
            registers=[max(left, right) for left, right in zip(self.registers, other.registers)],
        )

    def alpha_m(self) -> float:
        m = self.register_count
        if m == 16:
            return 0.673
        if m == 32:
            return 0.697
        if m == 64:
            return 0.709
        return 0.7213 / (1 + 1.079 / m)

    def raw_estimate(self) -> float:
        denominator = sum(2.0 ** (-register) for register in self.registers)
        return self.alpha_m() * (self.register_count**2) / denominator

    def estimate(self) -> float:
        estimate = self.raw_estimate()
        zero_registers = self.registers.count(0)
        m = self.register_count

        if estimate <= (5 / 2) * m and zero_registers:
            return m * math.log(m / zero_registers)
        if estimate > MAX_HASH_VALUE / 30:
            capped_ratio = min(estimate / MAX_HASH_VALUE, 1 - 1e-12)
            return -MAX_HASH_VALUE * math.log(1 - capped_ratio)
        return estimate

    def stats(self) -> dict:
        estimate = self.estimate()
        return {
            "precision": self.precision,
            "register_count": self.register_count,
            "zero_registers": self.registers.count(0),
            "max_register": max(self.registers),
            "raw_estimate": self.raw_estimate(),
            "estimate": estimate,
            "rounded_estimate": round(estimate),
            "relative_error_bound": 1.04 / math.sqrt(self.register_count),
        }


def load_hll(path: Path) -> HyperLogLog:
    return HyperLogLog.from_dict(json.loads(path.read_text()))


def save_hll(path: Path, sketch: HyperLogLog) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sketch.to_dict(), indent=2) + "\n")


def infer_input_format(path: Path, requested_format: str) -> str:
    if requested_format != "auto":
        return requested_format
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix in {".jsonl", ".ndjson"}:
        return "jsonl"
    if suffix == ".json":
        return "json"
    return "lines"


def _load_csv_records(path: Path, delimiter: str) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        if not reader.fieldnames:
            raise ValueError("CSV input requires a header row")
        fieldnames = list(reader.fieldnames)
        return list(reader), fieldnames


def _load_jsonl_records(path: Path) -> list[Any]:
    records: list[Any] = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            records.append(json.loads(stripped))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON on line {line_number}: {exc.msg}") from exc
    return records


def _load_json_records(path: Path) -> list[Any]:
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc.msg}") from exc
    if isinstance(data, list):
        return data
    return [data]


def _lookup_field_path(record: Any, field: str) -> Any:
    if isinstance(record, dict) and field in record:
        return record[field]

    current = record
    for part in field.split("."):
        if isinstance(current, dict):
            if part not in current:
                return MISSING
            current = current[part]
            continue
        if isinstance(current, list):
            if not part.isdigit():
                return MISSING
            index = int(part)
            if index >= len(current):
                return MISSING
            current = current[index]
            continue
        return MISSING
    return current


def _coerce_record_value(value: Any) -> str | None:
    if value is MISSING or value is None:
        return None
    if isinstance(value, str):
        normalized = value.strip()
        return normalized or None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    raise ValueError("field resolved to a non-scalar value; choose a scalar field path")


def extract_items(
    path: Path,
    *,
    input_format: str = "auto",
    field: str | None = None,
    csv_delimiter: str = ",",
) -> tuple[list[str], dict[str, Any]]:
    resolved_format = infer_input_format(path, input_format)

    if resolved_format == "lines":
        if field:
            raise ValueError("--field is only supported for csv/json/jsonl inputs")
        raw_lines = path.read_text().splitlines()
        values = [line.strip() for line in raw_lines if line.strip()]
        return values, {
            "input_format": resolved_format,
            "field": None,
            "records_read": len(raw_lines),
            "records_with_values": len(values),
            "records_skipped": len(raw_lines) - len(values),
            "records_missing_field": 0,
        }

    missing_field_count = 0
    if resolved_format == "csv":
        records, fieldnames = _load_csv_records(path, csv_delimiter)
        if not field:
            if len(fieldnames) != 1:
                raise ValueError("csv input requires --field when the file has multiple columns")
            field = fieldnames[0]
        elif field not in fieldnames:
            raise ValueError(f"field '{field}' not present in CSV header")
    elif resolved_format == "jsonl":
        records = _load_jsonl_records(path)
    elif resolved_format == "json":
        records = _load_json_records(path)
    else:
        raise ValueError(f"unsupported input format: {resolved_format}")

    extracted: list[str] = []
    skipped = 0
    for record in records:
        value = _lookup_field_path(record, field) if field else record
        if value is MISSING:
            missing_field_count += 1
            skipped += 1
            continue
        try:
            normalized = _coerce_record_value(value)
        except ValueError as exc:
            target = f"field '{field}'" if field else "record"
            raise ValueError(f"{target} resolved to a non-scalar value") from exc
        if normalized is None:
            skipped += 1
            continue
        extracted.append(normalized)

    if field and records and missing_field_count == len(records):
        raise ValueError(f"field '{field}' not found in any input record")

    return extracted, {
        "input_format": resolved_format,
        "field": field,
        "records_read": len(records),
        "records_with_values": len(extracted),
        "records_skipped": skipped,
        "records_missing_field": missing_field_count,
    }


def simulate_accuracy(precision: int, cardinality: int, trials: int, seed: int = 0) -> dict:
    if cardinality <= 0:
        raise ValueError("cardinality must be greater than 0")
    if trials <= 0:
        raise ValueError("trials must be greater than 0")

    rng = random.Random(seed)
    estimates = []
    for trial in range(trials):
        sketch = HyperLogLog(precision=precision)
        items = [f"trial-{trial}-item-{index}-{rng.getrandbits(64):016x}" for index in range(cardinality)]
        sketch.extend(items)
        estimates.append(sketch.estimate())

    mean_estimate = sum(estimates) / len(estimates)
    absolute_errors = [abs(estimate - cardinality) for estimate in estimates]
    relative_errors = [error / cardinality for error in absolute_errors]
    return {
        "precision": precision,
        "cardinality": cardinality,
        "trials": trials,
        "seed": seed,
        "mean_estimate": mean_estimate,
        "min_estimate": min(estimates),
        "max_estimate": max(estimates),
        "mean_absolute_error": sum(absolute_errors) / len(absolute_errors),
        "mean_relative_error": sum(relative_errors) / len(relative_errors),
        "theoretical_error_bound": 1.04 / math.sqrt(1 << precision),
    }


def parse_int_list(raw: str, *, argument_name: str) -> list[int]:
    values: list[int] = []
    for part in raw.split(","):
        normalized = part.strip()
        if not normalized:
            continue
        try:
            values.append(int(normalized))
        except ValueError as exc:
            raise ValueError(f"{argument_name} must contain only integers") from exc
    if not values:
        raise ValueError(f"{argument_name} must include at least one integer")
    return list(dict.fromkeys(values))


def _trial_items(cardinality: int, trial: int, seed: int) -> list[str]:
    rng = random.Random(f"{seed}:{cardinality}:{trial}")
    return [
        f"cardinality-{cardinality}-trial-{trial}-item-{index}-{rng.getrandbits(64):016x}"
        for index in range(cardinality)
    ]


def benchmark_accuracy(precisions: list[int], cardinalities: list[int], trials: int, seed: int = 0) -> dict:
    if trials <= 0:
        raise ValueError("trials must be greater than 0")
    if not precisions:
        raise ValueError("at least one precision is required")
    if not cardinalities:
        raise ValueError("at least one cardinality is required")

    normalized_precisions = list(dict.fromkeys(precisions))
    normalized_cardinalities = list(dict.fromkeys(cardinalities))
    for precision in normalized_precisions:
        HyperLogLog(precision=precision)
    for cardinality in normalized_cardinalities:
        if cardinality <= 0:
            raise ValueError("cardinalities must be greater than 0")

    rows: list[dict[str, Any]] = []
    best_by_cardinality: list[dict[str, Any]] = []
    for cardinality in normalized_cardinalities:
        estimates_by_precision = {precision: [] for precision in normalized_precisions}
        for trial in range(trials):
            items = _trial_items(cardinality, trial, seed)
            for precision in normalized_precisions:
                sketch = HyperLogLog(precision=precision)
                sketch.extend(items)
                estimates_by_precision[precision].append(sketch.estimate())

        cardinality_rows: list[dict[str, Any]] = []
        for precision in normalized_precisions:
            estimates = estimates_by_precision[precision]
            absolute_errors = [abs(estimate - cardinality) for estimate in estimates]
            relative_errors = [error / cardinality for error in absolute_errors]
            row = {
                "precision": precision,
                "register_count": 1 << precision,
                "dense_register_bytes": 1 << precision,
                "dense_register_kib": round((1 << precision) / 1024, 3),
                "cardinality": cardinality,
                "trials": trials,
                "seed": seed,
                "mean_estimate": sum(estimates) / len(estimates),
                "min_estimate": min(estimates),
                "max_estimate": max(estimates),
                "mean_absolute_error": sum(absolute_errors) / len(absolute_errors),
                "mean_relative_error": sum(relative_errors) / len(relative_errors),
                "max_relative_error": max(relative_errors),
                "theoretical_error_bound": 1.04 / math.sqrt(1 << precision),
            }
            cardinality_rows.append(row)
            rows.append(row)

        best_row = min(cardinality_rows, key=lambda row: (row["mean_relative_error"], row["dense_register_bytes"]))
        best_by_cardinality.append(
            {
                "cardinality": cardinality,
                "recommended_precision": best_row["precision"],
                "mean_relative_error": best_row["mean_relative_error"],
                "dense_register_bytes": best_row["dense_register_bytes"],
            }
        )

    return {
        "precisions": normalized_precisions,
        "cardinalities": normalized_cardinalities,
        "trials": trials,
        "seed": seed,
        "rows": rows,
        "best_by_cardinality": best_by_cardinality,
    }


def render_benchmark_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HyperLogLog benchmark report",
        "",
        f"- Precisions: {', '.join(str(value) for value in report['precisions'])}",
        f"- Cardinalities: {', '.join(str(value) for value in report['cardinalities'])}",
        f"- Trials per combination: {report['trials']}",
        f"- Seed: {report['seed']}",
        "- Dense register bytes assume one byte per register in this educational implementation.",
        "",
    ]

    recommendations = {item['cardinality']: item for item in report['best_by_cardinality']}
    for cardinality in report['cardinalities']:
        lines.extend([f"## Cardinality {cardinality}", ""])
        recommendation = recommendations[cardinality]
        lines.append(
            "Lowest observed mean error in this sweep: precision "
            f"`{recommendation['recommended_precision']}` at "
            f"`{recommendation['dense_register_bytes']}` dense bytes with "
            f"mean relative error `{recommendation['mean_relative_error'] * 100:.2f}%`."
        )
        lines.extend(
            [
                "",
                "| precision | registers | dense bytes | mean estimate | mean abs error | mean rel error | max rel error | theory bound |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in [entry for entry in report['rows'] if entry['cardinality'] == cardinality]:
            lines.append(
                "| "
                f"{row['precision']} | {row['register_count']} | {row['dense_register_bytes']} | "
                f"{row['mean_estimate']:.2f} | {row['mean_absolute_error']:.2f} | "
                f"{row['mean_relative_error'] * 100:.2f}% | {row['max_relative_error'] * 100:.2f}% | "
                f"{row['theoretical_error_bound'] * 100:.2f}% |"
            )
        lines.append("")

    return "\n".join(lines) + "\n"


def render_benchmark_csv(report: dict[str, Any]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "cardinality",
            "precision",
            "register_count",
            "dense_register_bytes",
            "dense_register_kib",
            "trials",
            "seed",
            "mean_estimate",
            "min_estimate",
            "max_estimate",
            "mean_absolute_error",
            "mean_relative_error",
            "max_relative_error",
            "theoretical_error_bound",
        ]
    )
    for row in report["rows"]:
        writer.writerow(
            [
                row["cardinality"],
                row["precision"],
                row["register_count"],
                row["dense_register_bytes"],
                row["dense_register_kib"],
                row["trials"],
                row["seed"],
                f"{row['mean_estimate']:.6f}",
                f"{row['min_estimate']:.6f}",
                f"{row['max_estimate']:.6f}",
                f"{row['mean_absolute_error']:.6f}",
                f"{row['mean_relative_error']:.6f}",
                f"{row['max_relative_error']:.6f}",
                f"{row['theoretical_error_bound']:.6f}",
            ]
        )
    return buffer.getvalue()


def _svg_text(x: float, y: float, text: str, *, size: int = 14, weight: str = "normal", fill: str = "#111827") -> str:
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    font_family = 'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}" font-family=\'{font_family}\'>{escaped}</text>'


def render_benchmark_svg(report: dict[str, Any]) -> str:
    cardinalities = report["cardinalities"]
    rows_by_cardinality = {
        cardinality: [row for row in report["rows"] if row["cardinality"] == cardinality]
        for cardinality in cardinalities
    }
    recommendations = {item["cardinality"]: item for item in report["best_by_cardinality"]}

    width = 960
    header_height = 120
    panel_height = 260
    panel_gap = 32
    height = header_height + len(cardinalities) * panel_height + max(len(cardinalities) - 1, 0) * panel_gap

    left = 84
    right = 28
    top_padding = 54
    bottom_padding = 60
    chart_width = width - left - right
    chart_height = panel_height - top_padding - bottom_padding

    max_error = max(
        max(row["mean_relative_error"], row["theoretical_error_bound"])
        for row in report["rows"]
    )
    y_max = max(max_error * 1.2, 0.02)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">HyperLogLog benchmark chart</title>',
        '<desc id="desc">Observed versus theoretical relative error across benchmarked HyperLogLog precisions.</desc>',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#f8fafc" />',
        _svg_text(28, 38, "HyperLogLog benchmark chart", size=28, weight="700"),
        _svg_text(28, 64, f"Precisions: {', '.join(str(value) for value in report['precisions'])}", size=14, fill="#334155"),
        _svg_text(28, 84, f"Cardinalities: {', '.join(str(value) for value in cardinalities)} · Trials: {report['trials']} · Seed: {report['seed']}", size=14, fill="#334155"),
        '<rect x="690" y="28" width="18" height="18" rx="3" fill="#2563eb" />',
        _svg_text(716, 42, "Observed mean relative error", size=13, fill="#1f2937"),
        '<rect x="690" y="54" width="18" height="18" rx="3" fill="#94a3b8" />',
        _svg_text(716, 68, "Theoretical error bound", size=13, fill="#1f2937"),
    ]

    for index, cardinality in enumerate(cardinalities):
        panel_top = header_height + index * (panel_height + panel_gap)
        rows = rows_by_cardinality[cardinality]
        recommendation = recommendations[cardinality]
        parts.append(f'<rect x="20" y="{panel_top:.1f}" width="920" height="{panel_height}" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
        parts.append(_svg_text(40, panel_top + 30, f"Cardinality {cardinality}", size=22, weight="700"))
        parts.append(
            _svg_text(
                40,
                panel_top + 52,
                "Best observed mean error: "
                f"p={recommendation['recommended_precision']} at {recommendation['dense_register_bytes']} dense bytes "
                f"({recommendation['mean_relative_error'] * 100:.2f}% mean relative error)",
                size=13,
                fill="#475569",
            )
        )

        chart_left = left
        chart_top = panel_top + top_padding
        chart_bottom = chart_top + chart_height
        chart_right = width - right
        parts.append(f'<line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_bottom}" stroke="#94a3b8" stroke-width="1.5" />')
        parts.append(f'<line x1="{chart_left}" y1="{chart_bottom}" x2="{chart_right}" y2="{chart_bottom}" stroke="#94a3b8" stroke-width="1.5" />')

        for tick in range(5):
            value = y_max * tick / 4
            y = chart_bottom - (chart_height * tick / 4)
            parts.append(f'<line x1="{chart_left}" y1="{y:.1f}" x2="{chart_right}" y2="{y:.1f}" stroke="#e2e8f0" stroke-width="1" />')
            parts.append(_svg_text(28, y + 5, f"{value * 100:.1f}%", size=11, fill="#64748b"))

        group_width = chart_width / max(len(rows), 1)
        bar_width = min(34, group_width / 3)
        label_y = chart_bottom + 22
        for row_index, row in enumerate(rows):
            center_x = chart_left + group_width * (row_index + 0.5)
            observed_height = 0 if y_max == 0 else chart_height * (row['mean_relative_error'] / y_max)
            theory_height = 0 if y_max == 0 else chart_height * (row['theoretical_error_bound'] / y_max)
            observed_x = center_x - bar_width - 4
            theory_x = center_x + 4
            observed_y = chart_bottom - observed_height
            theory_y = chart_bottom - theory_height
            parts.append(
                f'<rect x="{observed_x:.1f}" y="{observed_y:.1f}" width="{bar_width:.1f}" height="{observed_height:.1f}" rx="5" fill="#2563eb" />'
            )
            parts.append(
                f'<rect x="{theory_x:.1f}" y="{theory_y:.1f}" width="{bar_width:.1f}" height="{theory_height:.1f}" rx="5" fill="#94a3b8" />'
            )
            parts.append(_svg_text(observed_x - 2, max(observed_y - 8, chart_top + 12), f"{row['mean_relative_error'] * 100:.2f}%", size=10, fill="#1d4ed8"))
            parts.append(_svg_text(theory_x - 2, max(theory_y - 8, chart_top + 24), f"{row['theoretical_error_bound'] * 100:.2f}%", size=10, fill="#475569"))
            parts.append(_svg_text(center_x - 18, label_y, f"p={row['precision']}", size=12, weight="700", fill="#111827"))
            parts.append(_svg_text(center_x - 24, label_y + 16, f"{row['dense_register_bytes']}B", size=11, fill="#64748b"))

        parts.append(_svg_text(28, chart_top - 8, "relative error", size=12, weight="700", fill="#334155"))
        parts.append(
            _svg_text(
                chart_left + (chart_width / 2) - 58,
                chart_bottom + 40,
                "precision / dense bytes",
                size=12,
                weight="700",
                fill="#334155",
            )
        )

    parts.append('</svg>')
    return "".join(parts) + "\n"


def build_command(args: argparse.Namespace) -> int:
    sketch = HyperLogLog(precision=args.precision)
    items, extraction_summary = extract_items(
        Path(args.input),
        input_format=args.input_format,
        field=args.field,
        csv_delimiter=args.csv_delimiter,
    )
    inserted = sketch.extend(items)
    save_hll(Path(args.output), sketch)
    print(json.dumps({"inserted": inserted, "output": args.output, **extraction_summary, **sketch.stats()}, indent=2))
    return 0


def stats_command(args: argparse.Namespace) -> int:
    sketch = load_hll(Path(args.sketch))
    print(json.dumps(sketch.stats(), indent=2))
    return 0


def merge_command(args: argparse.Namespace) -> int:
    if len(args.sketches) < 2:
        raise ValueError("merge requires at least two sketch files")
    merged = load_hll(Path(args.sketches[0]))
    for path in args.sketches[1:]:
        merged = merged.merge(load_hll(Path(path)))
    if args.output:
        save_hll(Path(args.output), merged)
    print(json.dumps({"merged_inputs": args.sketches, "output": args.output, **merged.stats()}, indent=2))
    return 0


def simulate_command(args: argparse.Namespace) -> int:
    print(json.dumps(simulate_accuracy(args.precision, args.cardinality, args.trials, args.seed), indent=2))
    return 0


def benchmark_command(args: argparse.Namespace) -> int:
    report = benchmark_accuracy(
        parse_int_list(args.precisions, argument_name="--precisions"),
        parse_int_list(args.cardinalities, argument_name="--cardinalities"),
        args.trials,
        args.seed,
    )
    if args.json_output:
        output_path = Path(args.json_output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2) + "\n")
    if args.markdown_output:
        output_path = Path(args.markdown_output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_benchmark_markdown(report))
    if args.csv_output:
        output_path = Path(args.csv_output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_benchmark_csv(report))
    if args.svg_output:
        output_path = Path(args.svg_output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_benchmark_svg(report))
    print(
        json.dumps(
            {
                **report,
                "json_output": args.json_output,
                "markdown_output": args.markdown_output,
                "csv_output": args.csv_output,
                "svg_output": args.svg_output,
            },
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Estimate distinct counts with a HyperLogLog sketch")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="build a sketch from text, CSV, JSONL, or JSON input")
    build_parser.add_argument("--input", required=True, help="input file to scan")
    build_parser.add_argument("--output", required=True, help="where to write sketch JSON")
    build_parser.add_argument("--precision", type=int, default=10, help="register precision between 4 and 16")
    build_parser.add_argument(
        "--input-format",
        choices=["auto", "lines", "csv", "jsonl", "json"],
        default="auto",
        help="how to parse the input file (defaults to extension-based auto detection)",
    )
    build_parser.add_argument("--field", help="CSV column or dotted JSON field path to count")
    build_parser.add_argument("--csv-delimiter", default=",", help="CSV delimiter when --input-format csv is used")
    build_parser.set_defaults(func=build_command)

    stats_parser = subparsers.add_parser("stats", help="inspect sketch statistics")
    stats_parser.add_argument("--sketch", required=True, help="saved sketch JSON")
    stats_parser.set_defaults(func=stats_command)

    merge_parser = subparsers.add_parser("merge", help="merge two or more sketches")
    merge_parser.add_argument("--output", help="optional output path for merged sketch")
    merge_parser.add_argument("sketches", nargs="+", help="input sketch files with matching precision")
    merge_parser.set_defaults(func=merge_command)

    simulate_parser = subparsers.add_parser("simulate", help="sample estimation error for synthetic unique items")
    simulate_parser.add_argument("--precision", type=int, default=10, help="register precision between 4 and 16")
    simulate_parser.add_argument("--cardinality", type=int, required=True, help="true number of unique items per trial")
    simulate_parser.add_argument("--trials", type=int, default=10, help="number of synthetic trials to run")
    simulate_parser.add_argument("--seed", type=int, default=0, help="deterministic seed")
    simulate_parser.set_defaults(func=simulate_command)

    benchmark_parser = subparsers.add_parser(
        "benchmark",
        help="compare precision/error tradeoffs across multiple cardinalities",
    )
    benchmark_parser.add_argument(
        "--precisions",
        default="8,10,12",
        help="comma-separated precision values between 4 and 16 (default: 8,10,12)",
    )
    benchmark_parser.add_argument(
        "--cardinalities",
        default="100,1000,10000",
        help="comma-separated true cardinalities to simulate (default: 100,1000,10000)",
    )
    benchmark_parser.add_argument("--trials", type=int, default=10, help="number of synthetic trials per combination")
    benchmark_parser.add_argument("--seed", type=int, default=0, help="deterministic seed")
    benchmark_parser.add_argument("--json-output", help="optional path for the full JSON benchmark report")
    benchmark_parser.add_argument("--markdown-output", help="optional path for a Markdown summary report")
    benchmark_parser.add_argument("--csv-output", help="optional path for a CSV export of benchmark rows")
    benchmark_parser.add_argument("--svg-output", help="optional path for a self-contained SVG chart")
    benchmark_parser.set_defaults(func=benchmark_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ValueError as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())

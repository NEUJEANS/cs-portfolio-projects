import argparse
import html
import json
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from statistics import pstdev
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class Process:
    pid: str
    arrival: int
    burst: int
    priority: int = 0

    def __post_init__(self):
        if self.arrival < 0:
            raise ValueError(f"process {self.pid}: arrival must be >= 0")
        if self.burst <= 0:
            raise ValueError(f"process {self.pid}: burst must be > 0")


@dataclass(frozen=True)
class TimelineSlice:
    start: int
    end: int
    pid: str

    @property
    def duration(self) -> int:
        return self.end - self.start


SUPPORTED_ALGORITHMS = {"fcfs", "priority", "sjf", "srtf", "rr"}
ALGORITHM_ORDER = ["fcfs", "sjf", "srtf", "priority", "rr"]
SUPPORTED_COMMANDS = SUPPORTED_ALGORITHMS | {"compare", "list-presets"}
IDLE_PID = "IDLE"
CONTEXT_SWITCH_PID = "CS"
REPO_ROOT = Path(__file__).resolve().parents[2]
PRESET_DIR = REPO_ROOT / "artifacts" / "cpu-scheduler-simulator" / "presets"
WORKLOAD_PRESETS = {
    "convoy-mix": {
        "path": PRESET_DIR / "convoy-mix.json",
        "description": "one long CPU-bound job arrives first, then several short interactive jobs queue behind it",
    },
    "interactive-bursts": {
        "path": PRESET_DIR / "interactive-bursts.json",
        "description": "staggered short requests compete with a background batch job, making response-time tradeoffs visible",
    },
    "aging-pressure": {
        "path": PRESET_DIR / "aging-pressure.json",
        "description": "high-priority arrivals keep showing up while a low-priority batch job waits, stressing priority aging",
    },
}


def ordered_algorithms(algorithms: Iterable[str]) -> List[str]:
    requested = {algorithm.lower() for algorithm in algorithms}
    return [algorithm for algorithm in ALGORITHM_ORDER if algorithm in requested]


def repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def format_algorithm_label(algorithm: str, quantum: int = 2, aging_interval: int = 0) -> str:
    label = algorithm.upper()
    modifiers = []
    if algorithm == "rr":
        modifiers.append(f"q={quantum}")
    if algorithm == "priority" and aging_interval > 0:
        modifiers.append(f"aging={aging_interval}")
    if modifiers:
        label += f" ({', '.join(modifiers)})"
    return label


def format_metric_value(value: float) -> str:
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def format_preset_catalog() -> str:
    lines = ["Available workload presets:"]
    for preset_name in sorted(WORKLOAD_PRESETS):
        preset = WORKLOAD_PRESETS[preset_name]
        lines.append(
            f"- {preset_name}: {preset['description']} ({repo_relative(preset['path'])})"
        )
    return "\n".join(lines)


def load_processes(path: Path) -> List[Process]:
    raw = json.loads(path.read_text())
    if not isinstance(raw, list):
        raise ValueError("workload JSON must be a list of process objects")

    seen = set()
    processes = []
    for item in raw:
        pid = str(item["pid"])
        if pid in seen:
            raise ValueError(f"duplicate pid: {pid}")
        seen.add(pid)
        processes.append(
            Process(
                pid=pid,
                arrival=int(item["arrival"]),
                burst=int(item["burst"]),
                priority=int(item.get("priority", 0)),
            )
        )
    return processes


def resolve_workload_source(
    workload: Optional[Path],
    preset_name: Optional[str],
) -> Tuple[List[Process], str, Optional[str], str]:
    if preset_name and workload is not None:
        raise ValueError("pass either a workload path or --preset, not both")
    if preset_name:
        preset = WORKLOAD_PRESETS[preset_name]
        path = preset["path"]
        return (
            load_processes(path),
            preset_name,
            preset_name,
            repo_relative(path),
        )
    if workload is None:
        raise ValueError("provide a workload path or --preset")
    return (load_processes(workload), workload.stem, None, repo_relative(workload.resolve()))


def normalize_processes(processes: Iterable[Process]) -> List[Process]:
    processes = list(processes)
    if not processes:
        raise ValueError("at least one process is required")
    return sorted(processes, key=lambda proc: (proc.arrival, proc.pid))


def append_slice(timeline: List[TimelineSlice], start: int, end: int, pid: str) -> None:
    if start == end:
        return
    if timeline and timeline[-1].pid == pid and timeline[-1].end == start:
        last = timeline[-1]
        timeline[-1] = TimelineSlice(last.start, end, pid)
        return
    timeline.append(TimelineSlice(start, end, pid))


def finalize(
    processes: List[Process],
    timeline: List[TimelineSlice],
    first_start: Dict[str, int],
    completion: Dict[str, int],
    context_switch_cost: int = 0,
) -> Dict:
    per_process = []
    for proc in sorted(processes, key=lambda proc: proc.pid):
        complete = completion[proc.pid]
        turnaround = complete - proc.arrival
        waiting = turnaround - proc.burst
        response = first_start[proc.pid] - proc.arrival
        per_process.append(
            {
                "pid": proc.pid,
                "arrival": proc.arrival,
                "burst": proc.burst,
                "priority": proc.priority,
                "start": first_start[proc.pid],
                "completion": complete,
                "turnaround": turnaround,
                "waiting": waiting,
                "response": response,
            }
        )

    averages = {
        metric: round(sum(row[metric] for row in per_process) / len(per_process), 2)
        for metric in ("turnaround", "waiting", "response")
    }
    total_time = timeline[-1].end if timeline else 0
    useful_time = sum(
        slice_.duration
        for slice_ in timeline
        if slice_.pid not in {IDLE_PID, CONTEXT_SWITCH_PID}
    )
    context_switch_time = sum(slice_.duration for slice_ in timeline if slice_.pid == CONTEXT_SWITCH_PID)
    summary = {
        **averages,
        "cpu_utilization": round((useful_time / total_time) * 100, 2) if total_time else 0.0,
        "throughput": round(len(processes) / total_time, 4) if total_time else 0.0,
        "context_switches": sum(1 for slice_ in timeline if slice_.pid == CONTEXT_SWITCH_PID),
        "context_switch_overhead_time": context_switch_time,
        "scheduler_overhead_pct": round((context_switch_time / total_time) * 100, 2) if total_time else 0.0,
    }

    return {
        "processes": per_process,
        "timeline": [slice_.__dict__ for slice_ in timeline],
        "averages": summary,
        "total_time": total_time,
        "context_switch_cost": context_switch_cost,
    }


def build_result_from_timeline(
    processes: Iterable[Process],
    timeline: List[TimelineSlice],
    context_switch_cost: int = 0,
) -> Dict:
    processes = normalize_processes(processes)
    first_start: Dict[str, int] = {}
    completion: Dict[str, int] = {}

    for slice_ in timeline:
        if slice_.pid in {IDLE_PID, CONTEXT_SWITCH_PID}:
            continue
        first_start.setdefault(slice_.pid, slice_.start)
        completion[slice_.pid] = slice_.end

    return finalize(
        processes,
        timeline,
        first_start,
        completion,
        context_switch_cost=context_switch_cost,
    )


def should_charge_context_switch(previous_pid: Optional[str], next_pid: str) -> bool:
    if previous_pid is None:
        return False
    return (
        previous_pid not in {IDLE_PID, CONTEXT_SWITCH_PID}
        and next_pid not in {IDLE_PID, CONTEXT_SWITCH_PID}
        and previous_pid != next_pid
    )


def apply_context_switch_overhead(
    processes: Iterable[Process],
    base_timeline: Iterable[TimelineSlice],
    context_switch_cost: int,
) -> Dict:
    if context_switch_cost < 0:
        raise ValueError("context switch cost must be >= 0")

    timeline = list(base_timeline)
    if context_switch_cost == 0:
        return build_result_from_timeline(processes, timeline, context_switch_cost=0)

    augmented: List[TimelineSlice] = []
    previous_pid: Optional[str] = None
    offset = 0

    for slice_ in timeline:
        start = slice_.start + offset
        end = slice_.end + offset
        if should_charge_context_switch(previous_pid, slice_.pid):
            append_slice(augmented, start, start + context_switch_cost, CONTEXT_SWITCH_PID)
            start += context_switch_cost
            end += context_switch_cost
            offset += context_switch_cost
        append_slice(augmented, start, end, slice_.pid)
        previous_pid = slice_.pid

    return build_result_from_timeline(
        processes,
        augmented,
        context_switch_cost=context_switch_cost,
    )


def simulate_fcfs(processes: Iterable[Process]) -> Dict:
    processes = normalize_processes(processes)
    time = 0
    timeline: List[TimelineSlice] = []
    first_start: Dict[str, int] = {}
    completion: Dict[str, int] = {}

    for proc in processes:
        if time < proc.arrival:
            append_slice(timeline, time, proc.arrival, IDLE_PID)
            time = proc.arrival
        first_start[proc.pid] = time
        end = time + proc.burst
        append_slice(timeline, time, end, proc.pid)
        time = end
        completion[proc.pid] = time

    return finalize(processes, timeline, first_start, completion)


def simulate_sjf(processes: Iterable[Process]) -> Dict:
    processes = normalize_processes(processes)
    time = 0
    index = 0
    ready: List[Process] = []
    timeline: List[TimelineSlice] = []
    first_start: Dict[str, int] = {}
    completion: Dict[str, int] = {}

    while index < len(processes) or ready:
        while index < len(processes) and processes[index].arrival <= time:
            ready.append(processes[index])
            index += 1

        if not ready:
            next_arrival = processes[index].arrival
            append_slice(timeline, time, next_arrival, IDLE_PID)
            time = next_arrival
            continue

        ready.sort(key=lambda proc: (proc.burst, proc.arrival, proc.pid))
        proc = ready.pop(0)
        first_start.setdefault(proc.pid, time)
        end = time + proc.burst
        append_slice(timeline, time, end, proc.pid)
        time = end
        completion[proc.pid] = time

    return finalize(processes, timeline, first_start, completion)


def effective_priority(proc: Process, time: int, aging_interval: int) -> int:
    if aging_interval <= 0:
        return proc.priority
    waited = max(0, time - proc.arrival)
    return proc.priority - (waited // aging_interval)


def simulate_priority(processes: Iterable[Process], aging_interval: int = 0) -> Dict:
    if aging_interval < 0:
        raise ValueError("aging interval must be >= 0")

    processes = normalize_processes(processes)
    time = 0
    index = 0
    ready: List[Process] = []
    timeline: List[TimelineSlice] = []
    first_start: Dict[str, int] = {}
    completion: Dict[str, int] = {}

    while index < len(processes) or ready:
        while index < len(processes) and processes[index].arrival <= time:
            ready.append(processes[index])
            index += 1

        if not ready:
            next_arrival = processes[index].arrival
            append_slice(timeline, time, next_arrival, IDLE_PID)
            time = next_arrival
            continue

        ready.sort(
            key=lambda proc: (
                effective_priority(proc, time, aging_interval),
                proc.arrival,
                proc.pid,
            )
        )
        proc = ready.pop(0)
        first_start.setdefault(proc.pid, time)
        end = time + proc.burst
        append_slice(timeline, time, end, proc.pid)
        time = end
        completion[proc.pid] = time

    return finalize(processes, timeline, first_start, completion)


def simulate_srtf(processes: Iterable[Process]) -> Dict:
    processes = normalize_processes(processes)
    time = 0
    index = 0
    ready: List[Process] = []
    remaining = {proc.pid: proc.burst for proc in processes}
    timeline: List[TimelineSlice] = []
    first_start: Dict[str, int] = {}
    completion: Dict[str, int] = {}

    while index < len(processes) or ready:
        while index < len(processes) and processes[index].arrival <= time:
            ready.append(processes[index])
            index += 1

        if not ready:
            next_arrival = processes[index].arrival
            append_slice(timeline, time, next_arrival, IDLE_PID)
            time = next_arrival
            continue

        ready.sort(key=lambda proc: (remaining[proc.pid], proc.arrival, proc.pid))
        proc = ready.pop(0)
        first_start.setdefault(proc.pid, time)

        next_arrival = processes[index].arrival if index < len(processes) else None
        run_for = remaining[proc.pid]
        if next_arrival is not None:
            run_for = min(run_for, next_arrival - time)

        end = time + run_for
        append_slice(timeline, time, end, proc.pid)
        time = end
        remaining[proc.pid] -= run_for

        while index < len(processes) and processes[index].arrival <= time:
            ready.append(processes[index])
            index += 1

        if remaining[proc.pid] > 0:
            ready.append(proc)
        else:
            completion[proc.pid] = time

    return finalize(processes, timeline, first_start, completion)


def simulate_round_robin(processes: Iterable[Process], quantum: int) -> Dict:
    if quantum <= 0:
        raise ValueError("quantum must be > 0")

    processes = normalize_processes(processes)
    time = 0
    index = 0
    ready = deque()
    remaining = {proc.pid: proc.burst for proc in processes}
    process_map = {proc.pid: proc for proc in processes}
    timeline: List[TimelineSlice] = []
    first_start: Dict[str, int] = {}
    completion: Dict[str, int] = {}

    while index < len(processes) or ready:
        while index < len(processes) and processes[index].arrival <= time:
            ready.append(processes[index])
            index += 1

        if not ready:
            next_arrival = processes[index].arrival
            append_slice(timeline, time, next_arrival, IDLE_PID)
            time = next_arrival
            continue

        proc = ready.popleft()
        first_start.setdefault(proc.pid, time)
        run_for = min(quantum, remaining[proc.pid])
        end = time + run_for
        append_slice(timeline, time, end, proc.pid)
        time = end
        remaining[proc.pid] -= run_for

        while index < len(processes) and processes[index].arrival <= time:
            ready.append(processes[index])
            index += 1

        if remaining[proc.pid] > 0:
            ready.append(process_map[proc.pid])
        else:
            completion[proc.pid] = time

    return finalize(processes, timeline, first_start, completion)


def simulate(
    processes: Iterable[Process],
    algorithm: str,
    quantum: int = 2,
    aging_interval: int = 0,
    context_switch_cost: int = 0,
) -> Dict:
    if context_switch_cost < 0:
        raise ValueError("context switch cost must be >= 0")

    process_list = list(processes)
    algorithm = algorithm.lower()
    if algorithm == "fcfs":
        result = simulate_fcfs(process_list)
    elif algorithm == "priority":
        result = simulate_priority(process_list, aging_interval=aging_interval)
    elif algorithm == "sjf":
        result = simulate_sjf(process_list)
    elif algorithm == "srtf":
        result = simulate_srtf(process_list)
    elif algorithm == "rr":
        result = simulate_round_robin(process_list, quantum=quantum)
    else:
        raise ValueError(f"unsupported algorithm: {algorithm}")

    if context_switch_cost == 0:
        return result

    return apply_context_switch_overhead(
        process_list,
        [TimelineSlice(**slice_) for slice_ in result["timeline"]],
        context_switch_cost,
    )


def summarize_result(result: Dict) -> Dict:
    waiting_values = [row["waiting"] for row in result["processes"]]
    response_values = [row["response"] for row in result["processes"]]
    slowdown_values = [row["turnaround"] / row["burst"] for row in result["processes"]]
    return {
        "avg_turnaround": result["averages"]["turnaround"],
        "avg_waiting": result["averages"]["waiting"],
        "avg_response": result["averages"]["response"],
        "max_waiting": max(waiting_values),
        "waiting_spread": max(waiting_values) - min(waiting_values),
        "response_spread": max(response_values) - min(response_values),
        "waiting_stddev": round(pstdev(waiting_values), 2),
        "avg_slowdown": round(sum(slowdown_values) / len(slowdown_values), 2),
        "max_slowdown": round(max(slowdown_values), 2),
        "slowdown_spread": round(max(slowdown_values) - min(slowdown_values), 2),
        "slowdown_stddev": round(pstdev(slowdown_values), 2),
        "cpu_utilization": result["averages"]["cpu_utilization"],
        "throughput": result["averages"]["throughput"],
        "context_switches": result["averages"]["context_switches"],
        "context_switch_overhead_time": result["averages"]["context_switch_overhead_time"],
        "scheduler_overhead_pct": result["averages"]["scheduler_overhead_pct"],
        "total_time": result["total_time"],
        "timeline_slices": len(result["timeline"]),
    }


def build_experience_rows(result: Dict) -> List[Dict]:
    rows = []
    for row in result["processes"]:
        slowdown = round(row["turnaround"] / row["burst"], 2)
        rows.append(
            {
                "pid": row["pid"],
                "waiting": row["waiting"],
                "response": row["response"],
                "turnaround": row["turnaround"],
                "slowdown": slowdown,
            }
        )
    return rows


def find_peak_experience(experience_rows: Sequence[Dict], metric: str) -> Dict:
    return max(experience_rows, key=lambda row: (row[metric], row["pid"]))


def metric_winners(entries: Sequence[Dict], key: str, higher_is_better: bool = False) -> List[str]:
    values = [entry["summary"][key] for entry in entries]
    target = max(values) if higher_is_better else min(values)
    return [entry["algorithm"] for entry in entries if entry["summary"][key] == target]


def compare_algorithms(
    processes: Iterable[Process],
    algorithms: Optional[Sequence[str]] = None,
    quantum: int = 2,
    aging_interval: int = 0,
    context_switch_cost: int = 0,
    workload_label: str = "workload",
    workload_source: Optional[str] = None,
    preset: Optional[str] = None,
) -> Dict:
    process_list = normalize_processes(processes)
    selected_algorithms = ordered_algorithms(algorithms or ALGORITHM_ORDER)
    if not selected_algorithms:
        raise ValueError("at least one algorithm is required for compare mode")

    comparison_entries = []
    for algorithm in selected_algorithms:
        result = simulate(
            process_list,
            algorithm,
            quantum=quantum,
            aging_interval=aging_interval,
            context_switch_cost=context_switch_cost,
        )
        comparison_entries.append(
            {
                "algorithm": algorithm,
                "label": format_algorithm_label(algorithm, quantum=quantum, aging_interval=aging_interval),
                "summary": summarize_result(result),
                "experience": build_experience_rows(result),
                "result": result,
            }
        )

    winners = {
        "avg_turnaround": metric_winners(comparison_entries, "avg_turnaround"),
        "avg_waiting": metric_winners(comparison_entries, "avg_waiting"),
        "avg_response": metric_winners(comparison_entries, "avg_response"),
        "max_waiting": metric_winners(comparison_entries, "max_waiting"),
        "avg_slowdown": metric_winners(comparison_entries, "avg_slowdown"),
        "max_slowdown": metric_winners(comparison_entries, "max_slowdown"),
        "slowdown_stddev": metric_winners(comparison_entries, "slowdown_stddev"),
        "cpu_utilization": metric_winners(comparison_entries, "cpu_utilization", higher_is_better=True),
        "throughput": metric_winners(comparison_entries, "throughput", higher_is_better=True),
        "scheduler_overhead_pct": metric_winners(comparison_entries, "scheduler_overhead_pct"),
        "total_time": metric_winners(comparison_entries, "total_time"),
    }

    return {
        "mode": "compare",
        "workload_label": workload_label,
        "workload_source": workload_source,
        "preset": preset,
        "process_count": len(process_list),
        "algorithms": comparison_entries,
        "quantum": quantum,
        "aging_interval": aging_interval,
        "context_switch_cost": context_switch_cost,
        "winners": winners,
    }


def format_report(
    result: Dict,
    algorithm: str,
    quantum: Optional[int] = None,
    aging_interval: int = 0,
    context_switch_cost: int = 0,
) -> str:
    effective_context_switch_cost = context_switch_cost or result.get("context_switch_cost", 0)
    header = f"Algorithm: {algorithm.upper()}"
    modifiers = []
    if algorithm == "rr" and quantum is not None:
        modifiers.append(f"quantum={quantum}")
    if algorithm == "priority" and aging_interval > 0:
        modifiers.append(f"aging_interval={aging_interval}")
    if effective_context_switch_cost > 0:
        modifiers.append(f"context_switch_cost={effective_context_switch_cost}")
    if modifiers:
        header += f" ({', '.join(modifiers)})"

    timeline = "\n".join(
        f"  [{slice_['start']},{slice_['end']}): {slice_['pid']}"
        for slice_ in result["timeline"]
    )
    rows = "\n".join(
        "  {pid}: arrival={arrival}, burst={burst}, priority={priority}, start={start}, completion={completion}, "
        "turnaround={turnaround}, waiting={waiting}, response={response}".format(**row)
        for row in result["processes"]
    )
    averages = result["averages"]
    context_switch_lines = ""
    if effective_context_switch_cost > 0:
        context_switch_lines = (
            f"\nContext switches: {averages['context_switches']}"
            f"\nContext-switch overhead time: {averages['context_switch_overhead_time']}"
            f"\nScheduler overhead: {averages['scheduler_overhead_pct']}%"
        )
    return (
        f"{header}\n"
        f"Timeline:\n{timeline}\n"
        f"Per-process metrics:\n{rows}\n"
        f"Averages: turnaround={averages['turnaround']}, waiting={averages['waiting']}, response={averages['response']}\n"
        f"CPU utilization: {averages['cpu_utilization']}%\n"
        f"Throughput: {averages['throughput']} processes/unit"
        f"{context_switch_lines}\n"
        f"Total time: {result['total_time']}"
    )


def format_compare_markdown(comparison: Dict) -> str:
    lines = [f"# CPU Scheduler Comparison — {comparison['workload_label']}", ""]
    if comparison.get("preset"):
        lines.append(
            f"- preset: `{comparison['preset']}` — {WORKLOAD_PRESETS[comparison['preset']]['description']}"
        )
    if comparison.get("workload_source"):
        lines.append(f"- workload source: `{comparison['workload_source']}`")
    lines.extend(
        [
            f"- processes: {comparison['process_count']}",
            f"- algorithms: {', '.join(entry['label'] for entry in comparison['algorithms'])}",
            f"- round-robin quantum: {comparison['quantum']}",
            f"- priority aging interval: {comparison['aging_interval']}",
            f"- context-switch cost: {comparison['context_switch_cost']}",
            "",
            "| Algorithm | Avg turnaround | Avg waiting | Avg response | Max wait | CPU util % | Throughput | Overhead % | Total time |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for entry in comparison["algorithms"]:
        summary = entry["summary"]
        lines.append(
            f"| {entry['label']} | {summary['avg_turnaround']} | {summary['avg_waiting']} | {summary['avg_response']} | "
            f"{summary['max_waiting']} | {summary['cpu_utilization']} | {summary['throughput']} | {summary['scheduler_overhead_pct']} | {summary['total_time']} |"
        )

    lines.extend(
        [
            "",
            "## Fairness and slowdown snapshot",
            "| Algorithm | Avg slowdown | Max slowdown | Slowdown spread | Slowdown stddev | Waiting stddev | Most delayed process |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for entry in comparison["algorithms"]:
        summary = entry["summary"]
        tail = find_peak_experience(entry["experience"], "slowdown")
        lines.append(
            f"| {entry['label']} | {summary['avg_slowdown']} | {summary['max_slowdown']} | {summary['slowdown_spread']} | {summary['slowdown_stddev']} | "
            f"{summary['waiting_stddev']} | {tail['pid']} slowdown={format_metric_value(tail['slowdown'])}, wait={tail['waiting']} |"
        )

    lines.extend(
        [
            "",
            "## Per-process experience",
            "| Algorithm | PID | Waiting | Response | Turnaround | Slowdown |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for entry in comparison["algorithms"]:
        for row in entry["experience"]:
            lines.append(
                f"| {entry['label']} | {row['pid']} | {row['waiting']} | {row['response']} | {row['turnaround']} | {format_metric_value(row['slowdown'])} |"
            )

    def describe(metric: str, label: str) -> str:
        return f"- {label}: {', '.join(format_algorithm_label(name, comparison['quantum'], comparison['aging_interval']) for name in comparison['winners'][metric])}"

    lines.extend(
        [
            "",
            "## Takeaways",
            describe("avg_turnaround", "lowest average turnaround"),
            describe("avg_waiting", "lowest average waiting"),
            describe("avg_response", "lowest average response"),
            describe("max_waiting", "lowest worst-case waiting time"),
            describe("avg_slowdown", "lowest average slowdown"),
            describe("max_slowdown", "lowest worst slowdown"),
            describe("slowdown_stddev", "most even slowdown distribution"),
            describe("cpu_utilization", "highest useful CPU utilization"),
            describe("throughput", "highest throughput"),
            describe("scheduler_overhead_pct", "lowest scheduler overhead"),
            describe("total_time", "shortest total completion time"),
        ]
    )
    return "\n".join(lines)


def format_compare_html(comparison: Dict) -> str:
    rows = []
    for entry in comparison["algorithms"]:
        summary = entry["summary"]
        rows.append(
            "<tr>"
            f"<td>{html.escape(entry['label'])}</td>"
            f"<td>{summary['avg_turnaround']}</td>"
            f"<td>{summary['avg_waiting']}</td>"
            f"<td>{summary['avg_response']}</td>"
            f"<td>{summary['max_waiting']}</td>"
            f"<td>{summary['cpu_utilization']}</td>"
            f"<td>{summary['throughput']}</td>"
            f"<td>{summary['scheduler_overhead_pct']}</td>"
            f"<td>{summary['total_time']}</td>"
            "</tr>"
        )

    fairness_rows = []
    for entry in comparison["algorithms"]:
        summary = entry["summary"]
        tail = find_peak_experience(entry["experience"], "slowdown")
        fairness_rows.append(
            "<tr>"
            f"<td>{html.escape(entry['label'])}</td>"
            f"<td>{summary['avg_slowdown']}</td>"
            f"<td>{summary['max_slowdown']}</td>"
            f"<td>{summary['slowdown_spread']}</td>"
            f"<td>{summary['slowdown_stddev']}</td>"
            f"<td>{summary['waiting_stddev']}</td>"
            f"<td><strong>{html.escape(tail['pid'])}</strong> slowdown={html.escape(format_metric_value(tail['slowdown']))}, wait={tail['waiting']}</td>"
            "</tr>"
        )

    experience_cards = []
    for entry in comparison["algorithms"]:
        experience_rows = []
        for row in entry["experience"]:
            experience_rows.append(
                "<tr>"
                f"<td>{html.escape(row['pid'])}</td>"
                f"<td>{row['waiting']}</td>"
                f"<td>{row['response']}</td>"
                f"<td>{row['turnaround']}</td>"
                f"<td>{html.escape(format_metric_value(row['slowdown']))}</td>"
                "</tr>"
            )
        experience_cards.append(
            "<section class='card experience-card'>"
            f"<h3>{html.escape(entry['label'])}</h3>"
            "<table>"
            "<thead><tr><th>PID</th><th>Waiting</th><th>Response</th><th>Turnaround</th><th>Slowdown</th></tr></thead>"
            f"<tbody>{''.join(experience_rows)}</tbody>"
            "</table>"
            "</section>"
        )

    cards = []
    labels = {
        "avg_turnaround": "Lowest average turnaround",
        "avg_waiting": "Lowest average waiting",
        "avg_response": "Lowest average response",
        "max_waiting": "Lowest worst-case waiting time",
        "avg_slowdown": "Lowest average slowdown",
        "max_slowdown": "Lowest worst slowdown",
        "slowdown_stddev": "Most even slowdown distribution",
        "cpu_utilization": "Highest useful CPU utilization",
        "throughput": "Highest throughput",
        "scheduler_overhead_pct": "Lowest scheduler overhead",
        "total_time": "Shortest total completion time",
    }
    for key, title in labels.items():
        winners = ", ".join(
            format_algorithm_label(name, comparison["quantum"], comparison["aging_interval"])
            for name in comparison["winners"][key]
        )
        cards.append(
            "<div class='card'>"
            f"<h3>{html.escape(title)}</h3>"
            f"<p>{html.escape(winners)}</p>"
            "</div>"
        )

    metadata = []
    if comparison.get("preset"):
        metadata.append(
            f"<li><strong>Preset:</strong> {html.escape(comparison['preset'])} — {html.escape(WORKLOAD_PRESETS[comparison['preset']]['description'])}</li>"
        )
    if comparison.get("workload_source"):
        metadata.append(
            f"<li><strong>Workload source:</strong> <code>{html.escape(comparison['workload_source'])}</code></li>"
        )
    metadata.extend(
        [
            f"<li><strong>Processes:</strong> {comparison['process_count']}</li>",
            f"<li><strong>Algorithms:</strong> {html.escape(', '.join(entry['label'] for entry in comparison['algorithms']))}</li>",
            f"<li><strong>Round-robin quantum:</strong> {comparison['quantum']}</li>",
            f"<li><strong>Priority aging interval:</strong> {comparison['aging_interval']}</li>",
            f"<li><strong>Context-switch cost:</strong> {comparison['context_switch_cost']}</li>",
        ]
    )

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>CPU Scheduler Comparison — {html.escape(comparison['workload_label'])}</title>
  <style>
    :root {{
      color-scheme: light dark;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
      line-height: 1.45;
    }}
    body {{
      margin: 2rem auto;
      max-width: 1100px;
      padding: 0 1.25rem 3rem;
    }}
    h1, h2, h3 {{ margin-bottom: 0.45rem; }}
    ul {{ padding-left: 1.2rem; }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1rem;
      margin: 1.25rem 0 1.75rem;
    }}
    .card {{
      border: 1px solid color-mix(in srgb, currentColor 18%, transparent);
      border-radius: 14px;
      padding: 1rem;
      background: color-mix(in srgb, Canvas 92%, currentColor 3%);
    }}
    .experience-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 1rem;
      margin-top: 1rem;
    }}
    .experience-card table {{
      margin-top: 0.5rem;
      font-size: 0.95rem;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 1rem;
    }}
    th, td {{
      border-bottom: 1px solid color-mix(in srgb, currentColor 18%, transparent);
      padding: 0.65rem 0.55rem;
      text-align: right;
    }}
    th:first-child, td:first-child {{ text-align: left; }}
    code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
  </style>
</head>
<body>
  <h1>CPU Scheduler Comparison — {html.escape(comparison['workload_label'])}</h1>
  <ul>
    {''.join(metadata)}
  </ul>

  <div class=\"cards\">
    {''.join(cards)}
  </div>

  <h2>Side-by-side metrics</h2>
  <table>
    <thead>
      <tr>
        <th>Algorithm</th>
        <th>Avg turnaround</th>
        <th>Avg waiting</th>
        <th>Avg response</th>
        <th>Max wait</th>
        <th>CPU util %</th>
        <th>Throughput</th>
        <th>Overhead %</th>
        <th>Total time</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>

  <h2>Fairness and slowdown snapshot</h2>
  <table>
    <thead>
      <tr>
        <th>Algorithm</th>
        <th>Avg slowdown</th>
        <th>Max slowdown</th>
        <th>Slowdown spread</th>
        <th>Slowdown stddev</th>
        <th>Waiting stddev</th>
        <th>Most delayed process</th>
      </tr>
    </thead>
    <tbody>
      {''.join(fairness_rows)}
    </tbody>
  </table>

  <h2>Per-process experience</h2>
  <div class="experience-grid">
    {''.join(experience_cards)}
  </div>
</body>
</html>
"""


def format_compare_svg(comparison: Dict) -> str:
    entries = comparison["algorithms"]
    process_ids = sorted(
        {row["pid"] for entry in entries for row in entry["experience"]}
    )
    palette = ["#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c", "#0891b2", "#4f46e5", "#65a30d"]
    color_by_pid = {pid: palette[index % len(palette)] for index, pid in enumerate(process_ids)}

    bar_left = 260
    bar_width = 760
    bar_height = 16
    row_gap = 10
    group_gap = 22
    chart_gap = 70
    top_padding = 130
    bottom_padding = 48

    rows_per_group = len(process_ids)
    group_height = rows_per_group * (bar_height + row_gap) - row_gap if rows_per_group else 0
    chart_height = len(entries) * group_height + max(0, len(entries) - 1) * group_gap
    total_height = top_padding + chart_height * 2 + chart_gap + bottom_padding
    width = 1100

    max_slowdown = max(
        row["slowdown"] for entry in entries for row in entry["experience"]
    ) if entries else 1
    max_waiting = max(
        row["waiting"] for entry in entries for row in entry["experience"]
    ) if entries else 1
    max_slowdown = max(max_slowdown, 1)
    max_waiting = max(max_waiting, 1)

    def tick_values(max_value: float) -> List[float]:
        return [round((max_value * step) / 4, 2) for step in range(5)]

    def build_chart(metric: str, title: str, max_value: float, top: int) -> str:
        pieces = [
            f"<text x='40' y='{top - 18}' font-size='24' font-weight='700'>{html.escape(title)}</text>",
            f"<text x='40' y='{top + chart_height + 30}' font-size='14' fill='#475569'>Lower is better. Each bar is one process under one algorithm.</text>",
        ]
        for tick in tick_values(max_value):
            x = bar_left + (tick / max_value) * bar_width if max_value else bar_left
            pieces.append(
                f"<line x1='{x:.2f}' y1='{top}' x2='{x:.2f}' y2='{top + chart_height}' stroke='#cbd5e1' stroke-dasharray='4 4' />"
            )
            pieces.append(
                f"<text x='{x:.2f}' y='{top - 6}' text-anchor='middle' font-size='12' fill='#475569'>{html.escape(format_metric_value(tick))}</text>"
            )

        y = top
        for entry in entries:
            center_y = y + max(group_height / 2, bar_height / 2)
            pieces.append(
                f"<text x='40' y='{center_y:.2f}' font-size='15' font-weight='700'>{html.escape(entry['label'])}</text>"
            )
            ordered_rows = sorted(entry["experience"], key=lambda row: (-row[metric], row["pid"]))
            for row_index, row in enumerate(ordered_rows):
                row_y = y + row_index * (bar_height + row_gap)
                bar_len = (row[metric] / max_value) * bar_width if max_value else 0
                pieces.append(
                    f"<text x='{bar_left - 12}' y='{row_y + 12}' text-anchor='end' font-size='12' fill='#334155'>{html.escape(row['pid'])}</text>"
                )
                pieces.append(
                    f"<rect x='{bar_left}' y='{row_y}' width='{bar_width}' height='{bar_height}' rx='6' fill='#e2e8f0' />"
                )
                pieces.append(
                    f"<rect x='{bar_left}' y='{row_y}' width='{bar_len:.2f}' height='{bar_height}' rx='6' fill='{color_by_pid[row['pid']]}' />"
                )
                pieces.append(
                    f"<text x='{bar_left + min(bar_len + 8, bar_width - 6):.2f}' y='{row_y + 12}' font-size='12' fill='#0f172a'>{html.escape(format_metric_value(row[metric]))}</text>"
                )
            y += group_height + group_gap
        return ''.join(pieces)

    legend = []
    legend_x = 40
    legend_y = 68
    for pid in process_ids:
        if legend_x > width - 120:
            legend_x = 40
            legend_y += 24
        legend.append(f"<rect x='{legend_x}' y='{legend_y}' width='14' height='14' rx='4' fill='{color_by_pid[pid]}' />")
        legend.append(
            f"<text x='{legend_x + 22}' y='{legend_y + 12}' font-size='13' fill='#0f172a'>{html.escape(pid)}</text>"
        )
        legend_x += 82

    slowdown_chart = build_chart("slowdown", "Slowdown by process", max_slowdown, top_padding)
    waiting_top = top_padding + chart_height + chart_gap
    waiting_chart = build_chart("waiting", "Waiting time by process", max_waiting, waiting_top)

    subtitle = [
        f"workload={comparison['workload_label']}",
        f"quantum={comparison['quantum']}",
        f"aging={comparison['aging_interval']}",
        f"context_switch_cost={comparison['context_switch_cost']}",
    ]
    if comparison.get("preset"):
        subtitle.insert(1, f"preset={comparison['preset']}")

    return f"""<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{total_height}' viewBox='0 0 {width} {total_height}' role='img' aria-labelledby='title desc'>
  <title id='title'>CPU Scheduler fairness dashboard for {html.escape(comparison['workload_label'])}</title>
  <desc id='desc'>Per-process slowdown and waiting-time bars comparing {html.escape(', '.join(entry['label'] for entry in entries))}.</desc>
  <rect width='100%' height='100%' fill='#f8fafc' />
  <text x='40' y='44' font-size='30' font-weight='700' fill='#0f172a'>CPU Scheduler fairness dashboard</text>
  <text x='40' y='92' font-size='14' fill='#334155'>{html.escape(' · '.join(subtitle))}</text>
  {''.join(legend)}
  {slowdown_chart}
  {waiting_chart}
</svg>
"""


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Simulate classic CPU scheduling algorithms, list preset workloads, or compare algorithm tradeoffs"
    )
    parser.add_argument("command", choices=sorted(SUPPORTED_COMMANDS))
    parser.add_argument(
        "workload",
        nargs="?",
        type=Path,
        help="JSON file with process definitions (omit when using --preset or list-presets)",
    )
    parser.add_argument(
        "--preset",
        choices=sorted(WORKLOAD_PRESETS),
        help="use a committed preset workload instead of passing a JSON file",
    )
    parser.add_argument("--quantum", type=int, default=2, help="time quantum for round robin")
    parser.add_argument(
        "--aging-interval",
        type=int,
        default=0,
        help="priority boost interval for priority scheduling (0 disables aging)",
    )
    parser.add_argument(
        "--context-switch-cost",
        type=int,
        default=0,
        help="fixed dispatch overhead charged between two different runnable processes",
    )
    parser.add_argument(
        "--algorithms",
        nargs="+",
        choices=ALGORITHM_ORDER,
        default=ALGORITHM_ORDER,
        help="subset of algorithms to include in compare mode",
    )
    parser.add_argument("--markdown-out", type=Path, help="write a Markdown report to this path")
    parser.add_argument("--html-out", type=Path, help="write an HTML dashboard to this path")
    parser.add_argument("--svg-out", type=Path, help="write an SVG fairness dashboard to this path")
    parser.add_argument("--json-out", type=Path, help="write JSON output to this path")
    parser.add_argument("--json", action="store_true", help="print raw JSON result to stdout")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "list-presets":
        print(format_preset_catalog())
        return 0

    try:
        processes, workload_label, preset_name, workload_source = resolve_workload_source(
            args.workload,
            args.preset,
        )
    except ValueError as exc:
        parser.error(str(exc))

    if args.command == "compare":
        comparison = compare_algorithms(
            processes,
            algorithms=args.algorithms,
            quantum=args.quantum,
            aging_interval=args.aging_interval,
            context_switch_cost=args.context_switch_cost,
            workload_label=workload_label,
            workload_source=workload_source,
            preset=preset_name,
        )
        if args.markdown_out:
            write_text(args.markdown_out, format_compare_markdown(comparison))
        if args.html_out:
            write_text(args.html_out, format_compare_html(comparison))
        if args.svg_out:
            write_text(args.svg_out, format_compare_svg(comparison))
        if args.json_out:
            write_text(args.json_out, json.dumps(comparison, indent=2))
        if args.json:
            print(json.dumps(comparison, indent=2))
        elif not any([args.markdown_out, args.html_out, args.svg_out, args.json_out]):
            print(format_compare_markdown(comparison))
        return 0

    if args.html_out or args.svg_out:
        parser.error("--html-out and --svg-out are only supported with compare mode")

    result = simulate(
        processes,
        args.command,
        quantum=args.quantum,
        aging_interval=args.aging_interval,
        context_switch_cost=args.context_switch_cost,
    )
    if args.markdown_out:
        write_text(
            args.markdown_out,
            format_report(
                result,
                args.command,
                args.quantum if args.command == "rr" else None,
                aging_interval=args.aging_interval,
                context_switch_cost=args.context_switch_cost,
            ),
        )
    if args.json_out:
        write_text(args.json_out, json.dumps(result, indent=2))
    if args.json:
        print(json.dumps(result, indent=2))
    elif not any([args.markdown_out, args.json_out]):
        print(
            format_report(
                result,
                args.command,
                args.quantum if args.command == "rr" else None,
                aging_interval=args.aging_interval,
                context_switch_cost=args.context_switch_cost,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

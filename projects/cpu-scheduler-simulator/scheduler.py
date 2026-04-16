import argparse
import json
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class Process:
    pid: str
    arrival: int
    burst: int

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


SUPPORTED_ALGORITHMS = {"fcfs", "sjf", "srtf", "rr"}


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
            )
        )
    return processes


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


def finalize(processes: List[Process], timeline: List[TimelineSlice], first_start: Dict[str, int], completion: Dict[str, int]) -> Dict:
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
    busy_time = sum(slice_.duration for slice_ in timeline if slice_.pid != "IDLE")
    summary = {
        **averages,
        "cpu_utilization": round((busy_time / total_time) * 100, 2) if total_time else 0.0,
        "throughput": round(len(processes) / total_time, 4) if total_time else 0.0,
    }

    return {
        "processes": per_process,
        "timeline": [slice_.__dict__ for slice_ in timeline],
        "averages": summary,
        "total_time": total_time,
    }


def simulate_fcfs(processes: Iterable[Process]) -> Dict:
    processes = normalize_processes(processes)
    time = 0
    timeline: List[TimelineSlice] = []
    first_start: Dict[str, int] = {}
    completion: Dict[str, int] = {}

    for proc in processes:
        if time < proc.arrival:
            append_slice(timeline, time, proc.arrival, "IDLE")
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
            append_slice(timeline, time, next_arrival, "IDLE")
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
            append_slice(timeline, time, next_arrival, "IDLE")
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
            append_slice(timeline, time, next_arrival, "IDLE")
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


def simulate(processes: Iterable[Process], algorithm: str, quantum: int = 2) -> Dict:
    algorithm = algorithm.lower()
    if algorithm == "fcfs":
        return simulate_fcfs(processes)
    if algorithm == "sjf":
        return simulate_sjf(processes)
    if algorithm == "srtf":
        return simulate_srtf(processes)
    if algorithm == "rr":
        return simulate_round_robin(processes, quantum=quantum)
    raise ValueError(f"unsupported algorithm: {algorithm}")


def format_report(result: Dict, algorithm: str, quantum: Optional[int] = None) -> str:
    header = f"Algorithm: {algorithm.upper()}"
    if algorithm == "rr" and quantum is not None:
        header += f" (quantum={quantum})"

    timeline = "\n".join(
        f"  [{slice_['start']},{slice_['end']}): {slice_['pid']}"
        for slice_ in result["timeline"]
    )
    rows = "\n".join(
        "  {pid}: arrival={arrival}, burst={burst}, start={start}, completion={completion}, "
        "turnaround={turnaround}, waiting={waiting}, response={response}".format(**row)
        for row in result["processes"]
    )
    averages = result["averages"]
    return (
        f"{header}\n"
        f"Timeline:\n{timeline}\n"
        f"Per-process metrics:\n{rows}\n"
        f"Averages: turnaround={averages['turnaround']}, waiting={averages['waiting']}, response={averages['response']}\n"
        f"CPU utilization: {averages['cpu_utilization']}%\n"
        f"Throughput: {averages['throughput']} processes/unit\n"
        f"Total time: {result['total_time']}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Simulate classic CPU scheduling algorithms")
    parser.add_argument("algorithm", choices=sorted(SUPPORTED_ALGORITHMS))
    parser.add_argument("workload", type=Path, help="JSON file with process definitions")
    parser.add_argument("--quantum", type=int, default=2, help="time quantum for round robin")
    parser.add_argument("--json", action="store_true", help="print raw JSON result")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    processes = load_processes(args.workload)
    result = simulate(processes, args.algorithm, quantum=args.quantum)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_report(result, args.algorithm, args.quantum if args.algorithm == "rr" else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

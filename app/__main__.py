from __future__ import annotations

import argparse
from typing import Dict, List
from .simulation import Simulation


def parse_zone_capacities(raw: str | None) -> Dict[int, int] | None:
    if not raw:
        return None
    result: Dict[int, int] = {}
    for chunk in raw.split(","):
        if ":" not in chunk:
            continue
        source, capacity = chunk.split(":")
        result[int(source.strip())] = int(capacity.strip())
    return result or None


def format_events(events: List[Dict]) -> str:
    if not events:
        return "—"
    parts = []
    for event in events:
        call = event.get("call_id")
        payload = event["type"]
        if call is not None:
            payload += f"#{call}"
        parts.append(f"{event['time']:.2f}:{payload}")
    return "; ".join(parts)


def format_buffer(snapshot: Dict) -> str:
    buffer_state = snapshot["buffer"]
    if buffer_state["mode"] == "zonal":
        segments = [f"S{source}:{values}" for source, values in buffer_state["by_source"].items()]
        return f"{buffer_state['total']} ({', '.join(segments)})"
    return f"{buffer_state['total']} -> {buffer_state['calls']}"


def format_pointers(snapshot: Dict) -> str:
    info = snapshot["pointers"]
    if info["mode"] == "shared":
        return f"in={info['insert']} out={info['remove']}"
    zone_lines = []
    for zone, details in info["zones"].items():
        zone_lines.append(f"S{zone}(in={details.get('insert', 0)},out={details.get('remove', 0)})")
    return "; ".join(zone_lines) if zone_lines else "—"


def format_operators(snapshot: Dict) -> str:
    entries = []
    for item in snapshot["operators"]:
        if item["call_id"] is None:
            entries.append(f"O{item['id']}:free")
        else:
            entries.append(f"O{item['id']}:#{item['call_id']}→{item['release_time']:.2f}")
    return "; ".join(entries)


def run_step_mode(sim: Simulation, steps: int, delta: float) -> None:
    snapshots = sim.run_step_mode(steps, delta)
    header = (
        f"{'t':>6} | {'События':<60} | {'Буфер':<25} | {'Операторы':<35} | "
        f"{'Указатели':<25} | % отказов"
    )
    print(header)
    print("-" * len(header))
    for snapshot in snapshots:
        time_label = f"{snapshot['time']:>6.2f}"
        events = format_events(snapshot["events"])
        buffer_state = format_buffer(snapshot)
        operator_state = format_operators(snapshot)
        pointers = format_pointers(snapshot)
        reject = f"{snapshot['reject_percent']:.2f}"
        print(
            f"{time_label} | {events:<60} | {buffer_state:<25} | "
            f"{operator_state:<35} | {pointers:<25} | {reject}"
        )


def run_auto_mode(sim: Simulation, duration: float, delta: float, graph_dir: str) -> None:
    stats = sim.run_auto_mode(duration, delta, graph_dir)
    print("Автоматический режим завершен.")
    print(f"Время моделирования: {sim.clock:.2f}")
    print(f"Начато заявок: {stats['total_started']}")
    print(f"Завершено заявок: {stats['total_completed']}")
    print(f"Отказано: {stats['total_rejected']} ({stats['reject_percent']}%)")
    print(f"Среднее ожидание: {stats['avg_wait_time']:.2f}")
    print(f"Среднее обслуживание: {stats['avg_service_time']:.2f}")
    print(f"Файл с графиками: {stats['graph']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Симуляция контакт-центра")
    parser.add_argument("--mode", choices=["step", "auto"], default="step")
    parser.add_argument("--duration", type=float, default=50.0, help="Время моделирования в автоматическом режиме")
    parser.add_argument("--steps", type=int, default=30, help="Количество шагов в пошаговом режиме")
    parser.add_argument("--delta", type=float, default=0.5, help="Шаг дискретизации")
    parser.add_argument("--lambda-rate", type=float, default=0.6, help="Интенсивность поступления заявок на источник")
    parser.add_argument("--sources", type=int, default=2, help="Количество источников")
    parser.add_argument("--buffer-size", type=int, default=8)
    parser.add_argument("--operators", type=int, default=3)
    parser.add_argument("--buffer-mode", choices=["shared", "zonal"], default="shared")
    parser.add_argument("--zones", type=str, help="Пример: 1:3,2:2 для зонной памяти")
    parser.add_argument("--direct-dispatch", action="store_true", help="Передавать заявки напрямую на приборы")
    parser.add_argument("--graph-dir", default="artifacts")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    zone_capacities = parse_zone_capacities(args.zones)
    lambda_rate = [args.lambda_rate] * args.sources
    
    sim = Simulation(
        lambda_rate=lambda_rate,
        buffer_size=args.buffer_size,
        num_operators=args.operators,
        num_sources=args.sources,
        buffer_mode=args.buffer_mode,
        zone_capacities=zone_capacities,
        direct_dispatch=args.direct_dispatch,
    )
    
    if args.mode == "step":
        run_step_mode(sim, args.steps, args.delta)
    else:
        run_auto_mode(sim, args.duration, args.delta, args.graph_dir)


if __name__ == "__main__":
    main()

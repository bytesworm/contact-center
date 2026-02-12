from __future__ import annotations

import argparse
from typing import Dict, List
from .simulation import Simulation


def print_step(step_num: int, sim: Simulation, snapshot: Dict) -> None:
    cal = sim.get_calendar()

    print(f"\n{'='*60}")
    print(f"  Шаг {step_num}   t = {snapshot['time']:.2f}")
    print(f"{'='*60}")

    print(f"\n  Календарь событий")
    print(f"  {'Событие':<12} {'Время':>8} {'Число заявок':>14} {'Число отказов':>15}")
    print(f"  {'-'*12} {'-'*8} {'-'*14} {'-'*15}")
    for source_id in sorted(cal["sources"].keys()):
        t_next = cal["sources"][source_id]
        t_str = f"{t_next:.2f}" if t_next is not None else "—"
        n_gen = cal["source_generated"].get(source_id, 0)
        n_rej = cal["source_rejected"].get(source_id, 0)
        print(f"  {'И' + str(source_id):<12} {t_str:>8} {n_gen:>14} {n_rej:>15}")
    for op in cal["operators"]:
        status = "свободен" if op["call_id"] is None else f"#{op['call_id']}"
        t_str = f"{op['release_time']:.2f}"
        print(f"  {'П' + str(op['id']):<12} {t_str:>8} {status:>14}")
    print()

    slots = cal["buffer_slots"]
    ptrs = cal["pointers"]
    print(f"  Буфер (УБвст={ptrs['insert']}, УБвыб={ptrs['remove']})")
    if slots:
        print(f"  {'Позиция':>8} {'Время':>8} {'Источник':>10} {'Заявка':>8}")
        print(f"  {'-'*8} {'-'*8} {'-'*10} {'-'*8}")
        for slot in slots:
            print(f"  {slot['position']:>8} {slot['time']:>8.2f} {slot['source']:>10} {slot['call_id']:>8}")
    else:
        print("  (пусто)")
    print()

    print(f"  Текущее состояние")
    for op in cal["operators"]:
        if op["call_id"] is None:
            print(f"    П{op['id']}: свободен")
        else:
            print(f"    П{op['id']}: обслуживает #{op['call_id']} → освобождение {op['release_time']:.2f}")
    print(f"    Процент отказов: {snapshot['reject_percent']:.2f}%")

    events = snapshot["events"]
    if events:
        print(f"\n  События шага:")
        for ev in events:
            call_id = ev.get("call_id")
            label = ev["type"]
            if call_id is not None:
                label += f" #{call_id}"
            print(f"    t={ev['time']:.2f}  {label}")


def run_step_mode(sim: Simulation, steps: int, delta: float) -> None:
    for step in range(1, steps + 1):
        sim.tick(delta)
        sim._record_snapshot()
        snapshot = sim.metrics.snapshots[-1]
        print_step(step, sim, snapshot)


def print_event_log(events: List[Dict]) -> None:
    print(f"\n{'='*60}")
    print(f"  Журнал событий ({len(events)} записей)")
    print(f"{'='*60}")
    print(f"  {'t':>8}  {'Событие':<25} {'Детали'}")
    print(f"  {'-'*8}  {'-'*25} {'-'*30}")
    for ev in events:
        t = ev["time"]
        etype = ev["type"]
        parts = []
        if ev.get("call_id") is not None:
            parts.append(f"заявка #{ev['call_id']}")
        if ev.get("source") is not None:
            parts.append(f"И{ev['source']}")
        if ev.get("operator_id") is not None:
            parts.append(f"П{ev['operator_id']}")
        if ev.get("reason"):
            parts.append(ev["reason"])
        detail = ", ".join(parts)
        print(f"  {t:>8.2f}  {etype:<25} {detail}")


def run_auto_mode(sim: Simulation, duration: float, delta: float, graph_dir: str) -> None:
    stats = sim.run_auto_mode(duration, delta, graph_dir)

    print(f"\nАвтоматический режим завершён.")
    print(f"Время моделирования (реализации): {sim.clock:.2f}")
    print(f"Всего заявок: {stats['total_started'] + stats['total_rejected']}")
    print(f"Обслужено: {stats['total_completed']}")
    print(f"Отказано: {stats['total_rejected']}")
    print()

    source_stats = sim.metrics.per_source_stats()
    print("  Таблица 1. Характеристики источников")
    print(f"  {'Источник':<10} {'Заявок':>7} {'pотк':>8} {'Tпреб':>8} {'TБП':>8} {'Tобсл':>8} {'ДБП':>8} {'Добсл':>8}")
    print(f"  {'-'*10} {'-'*7} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
    for source_id, s in source_stats.items():
        print(
            f"  {'И' + str(source_id):<10} {s['count']:>7} {s['p_otk']:>8.4f} "
            f"{s['T_preb']:>8.2f} {s['T_bp']:>8.2f} {s['T_obsl']:>8.2f} "
            f"{s['D_bp']:>8.2f} {s['D_obsl']:>8.2f}"
        )
    print()

    utilization = {op.id: op.utilization(sim.clock) for op in sim.operators}
    print("  Таблица 2. Характеристики приборов")
    print(f"  {'Прибор':<10} {'Kисп':>8}")
    print(f"  {'-'*10} {'-'*8}")
    for op_id in sorted(utilization.keys()):
        print(f"  {'П' + str(op_id):<10} {utilization[op_id]:>8.4f}")
    print()

    print(f"Файл с графиками: {stats['graph']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Имитационная модель контакт-центра (СМО). "
        "Вариант 1: ИБ ИЗ1 ПЗ2 Д1ОЗ1 Д1ОО1 Д2П1 Д2Б1 ОР2 ОД1",
    )
    parser.add_argument(
        "mode", nargs="?", choices=["step", "auto"], default="step",
        help="Режим: step — пошаговый (ОД1), auto — автоматический (ОР2). По умолчанию: step",
    )

    group = parser.add_argument_group("параметры системы")
    group.add_argument("-n", "--sources", type=int, default=2, help="Количество источников (по умолчанию: 2)")
    group.add_argument("-l", "--lambda-rate", type=float, default=0.6, help="Интенсивность λ на источник (по умолчанию: 0.6)")
    group.add_argument("-m", "--operators", type=int, default=3, help="Количество приборов (по умолчанию: 3)")
    group.add_argument("-b", "--buffer-size", type=int, default=8, help="Размер буфера (по умолчанию: 8)")
    group.add_argument("-s", "--service", type=float, nargs=2, default=[1.0, 10.0],
                       metavar=("MIN", "MAX"), help="Диапазон времени обслуживания (по умолчанию: 1 10)")

    group2 = parser.add_argument_group("управление моделированием")
    group2.add_argument("--steps", type=int, default=30, help="Шагов в пошаговом режиме (по умолчанию: 30)")
    group2.add_argument("--duration", type=float, default=50.0, help="Время моделирования в auto (по умолчанию: 50)")
    group2.add_argument("--delta", type=float, default=0.5, help="Шаг Δt (по умолчанию: 0.5)")
    group2.add_argument("--graph-dir", default="artifacts", help="Папка для графиков (по умолчанию: artifacts)")
    group2.add_argument("--log", action="store_true", help="Вывести журнал событий после завершения")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    lambda_rate = [args.lambda_rate] * args.sources

    sim = Simulation(
        lambda_rate=lambda_rate,
        buffer_size=args.buffer_size,
        num_operators=args.operators,
        num_sources=args.sources,
        service_range=tuple(args.service),
    )

    if args.mode == "step":
        run_step_mode(sim, args.steps, args.delta)
    else:
        run_auto_mode(sim, args.duration, args.delta, args.graph_dir)

    if args.log:
        print_event_log(sim.metrics.events)


if __name__ == "__main__":
    main()

from __future__ import annotations
from app.simulation import Simulation

DURATION = 500.0
DELTA = 0.1
NUM_SOURCES = 10
N_DISPLAY = 10

JUNIOR = (5.0, 10.0)
SENIOR = (1.0, 5.0)

CONFIGS = [
    ("Малоопытные",   8,  3, 1, JUNIOR, 55000),
    ("Малоопытные",   8,  5, 1, JUNIOR, 55000),
    ("Профессионалы", 3,  3, 1, SENIOR, 90000),
    ("Профессионалы", 3,  5, 1, SENIOR, 90000),
    ("Профессионалы", 4,  3, 1, SENIOR, 90000),

    ("Малоопытные",  16,  5, 2, JUNIOR, 55000),
    ("Малоопытные",  16,  8, 2, JUNIOR, 55000),
    ("Малоопытные",  17,  4, 2, JUNIOR, 55000),
    ("Профессионалы", 6,  4, 2, SENIOR, 90000),
    ("Профессионалы", 7,  3, 2, SENIOR, 90000),
]


def run(ops, buf, lam_total, svc):
    lam_ps = lam_total / NUM_SOURCES
    sim = Simulation(
        lambda_rate=[lam_ps] * NUM_SOURCES, buffer_size=buf,
        num_operators=ops, num_sources=NUM_SOURCES, service_range=svc,
    )
    while sim.clock < DURATION:
        sim.tick(DELTA)
    while True:
        busy = any(not op.is_free(sim.clock) for op in sim.operators)
        if not sim.buffer.is_empty() or busy:
            sim.clock += DELTA
            sim.dispatcher.update_operators(sim.clock)
        else:
            break
    s = sim.metrics.get_stats()
    total = s["total_started"] + s["total_rejected"]
    p = s["total_rejected"] / total if total else 0
    u = sum(op.utilization(sim.clock) for op in sim.operators) / ops
    t = s["avg_wait_time"] + s["avg_service_time"]
    return round(p, 2), round(u, 2), round(t, 2)


def main():
    cur = ""
    for label, ops, buf, lam, svc, cop in CONFIGS:
        h = f"{label}, lambda = {lam}"
        if h != cur:
            cur = h
            print(f"\n{h}")
            print(f"{'Клиенты':>8} {'Спец-ты':>8} {'Буфер':>6} {'Lambda':>7}"
                  f" {'Загруж.':>8} {'p_отк':>7} {'Tсист':>7} {'Стоим.':>10}")
        p, u, t = run(ops, buf, lam, svc)
        cost = ops * cop + buf * 15000
        print(f"{N_DISPLAY:>8} {ops:>8} {buf:>6} {lam:>7}"
              f" {u:>8.2f} {p:>7.2f} {t:>7.2f} {cost:>10,}")


if __name__ == "__main__":
    main()

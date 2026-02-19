from __future__ import annotations
from app.simulation import Simulation

DURATION = 500.0
DELTA = 0.1
NUM_SOURCES = 10

JUNIOR = (5.0, 10.0)
SENIOR = (1.0, 5.0)

COST_JUNIOR = 45_000
COST_SENIOR = 80_000
COST_BUFFER = 15_000

CONFIGS = [
    ("Малоопытные",   7, 10, 1, JUNIOR, COST_JUNIOR),
    ("Малоопытные",   7, 14, 1, JUNIOR, COST_JUNIOR),
    ("Малоопытные",   8,  8, 1, JUNIOR, COST_JUNIOR),
    ("Малоопытные",   8, 14, 1, JUNIOR, COST_JUNIOR),

    ("Профессионалы", 3,  8, 1, SENIOR, COST_SENIOR),
    ("Профессионалы", 3, 10, 1, SENIOR, COST_SENIOR),
    ("Профессионалы", 3, 14, 1, SENIOR, COST_SENIOR),

    ("Малоопытные",  15, 10, 2, JUNIOR, COST_JUNIOR),
    ("Малоопытные",  15, 14, 2, JUNIOR, COST_JUNIOR),
    ("Малоопытные",  16, 10, 2, JUNIOR, COST_JUNIOR),

    ("Профессионалы", 6,  8, 2, SENIOR, COST_SENIOR),
    ("Профессионалы", 6, 10, 2, SENIOR, COST_SENIOR),
    ("Профессионалы", 6, 14, 2, SENIOR, COST_SENIOR),
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
            print(f"{'Спец-ты':>8} {'Буфер':>6} {'Загруж.':>8} {'p_отк':>7}"
                  f" {'Tсист':>7} {'Стоим.':>10}"
                  f" {'≥90%':>5} {'≤10%':>5}")
        p, u, t = run(ops, buf, lam, svc)
        cost = ops * cop + buf * COST_BUFFER
        ok_u = "✓" if u >= 0.90 else ""
        ok_p = "✓" if p <= 0.10 else ""
        print(f"{ops:>8} {buf:>6} {u:>8.2f} {p:>7.2f}"
              f" {t:>7.2f} {cost:>10,}"
              f" {ok_u:>5} {ok_p:>5}")


if __name__ == "__main__":
    main()

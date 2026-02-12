from __future__ import annotations

from typing import Dict, List, Sequence
from .buffer import Buffer
from .dispatcher import Dispatcher
from .generator import Generator
from .metrics import Metrics
from .operator import Operator


class Simulation:
    def __init__(
        self,
        lambda_rate: float | Sequence[float],
        buffer_size: int,
        num_operators: int,
        num_sources: int = 2,
        service_range: tuple[float, float] = (1.0, 10.0),
    ) -> None:
        self.clock = 0.0
        self.generator = Generator(lambda_rate, num_sources, service_range)
        self.buffer = Buffer(buffer_size)
        self.operators = [Operator(i + 1) for i in range(num_operators)]
        self.metrics = Metrics()
        self.dispatcher = Dispatcher(self.buffer, self.operators, self.metrics)
        self._event_cursor = 0

    def tick(self, delta_time: float) -> None:
        self.clock += delta_time
        calls = self.generator.generate_poisson(self.clock)
        for call in calls:
            self.dispatcher.on_arrival(call, self.clock)
        self.dispatcher.update_operators(self.clock)

    def _record_snapshot(self) -> None:
        events = self.metrics.events[self._event_cursor:]
        self._event_cursor = len(self.metrics.events)
        buffer_state = self.buffer.get_state()
        operators_state = [operator.describe(self.clock) for operator in self.operators]
        pointer_state = self.buffer.get_pointer_state()
        self.metrics.record_snapshot(self.clock, events, buffer_state, operators_state, pointer_state)
        self.metrics.record_time_series(self.clock, buffer_state["total"])

    def _has_pending_work(self) -> bool:
        operators_busy = any(not operator.is_free(self.clock) for operator in self.operators)
        return (not self.buffer.is_empty()) or operators_busy

    def _drain_system(self, delta_time: float) -> None:
        """Дорабатываем оставшиеся заявки после окончания генерации."""
        while self._has_pending_work():
            self.clock += delta_time
            self.dispatcher.update_operators(self.clock)
            self._record_snapshot()

    def run_step_mode(self, steps: int, delta_time: float) -> List[Dict]:
        for _ in range(steps):
            self.tick(delta_time)
            self._record_snapshot()
        return self.metrics.snapshots

    def run_auto_mode(self, duration: float, delta_time: float, target_dir: str) -> Dict:
        while self.clock < duration:
            self.tick(delta_time)
            self._record_snapshot()
        self._drain_system(delta_time)
        utilization = {op.id: op.utilization(self.clock) for op in self.operators}
        self.metrics.store_operator_utilization(utilization)
        plot = self.metrics.render_graphs(self.clock, target_dir)
        stats = self.metrics.get_stats()
        stats["graph"] = str(plot)
        return stats

    def get_calendar(self) -> Dict:
        return {
            "sources": self.generator.get_next_arrival_times(),
            "source_generated": dict(self.metrics._source_generated),
            "source_rejected": dict(self.metrics._source_rejected),
            "operators": [op.describe(self.clock) for op in self.operators],
            "buffer_slots": self.buffer.get_buffer_slots(),
            "pointers": self.buffer.get_pointer_state(),
        }

    def get_stats(self) -> Dict:
        return self.metrics.get_stats()

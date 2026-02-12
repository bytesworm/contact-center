from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Sequence
import matplotlib.pyplot as plt
from .call import Call


class Metrics:
    def __init__(self) -> None:
        self.events: List[Dict] = []
        self.snapshots: List[Dict] = []
        self.rejected_calls: int = 0
        self.completed_calls: int = 0
        self.started_calls: int = 0
        self._call_start_times: Dict[int, float] = {}
        self._call_wait_times: List[float] = []
        self._call_service_times: List[float] = []
        self._queue_history: List[tuple[float, int]] = []
        self._rejection_rate_history: List[tuple[float, float]] = []
        self._operator_utilization: Dict[int, float] = {}

        self._source_generated: Dict[int, int] = defaultdict(int)
        self._source_rejected: Dict[int, int] = defaultdict(int)
        self._source_completed: Dict[int, int] = defaultdict(int)
        self._source_wait_times: Dict[int, List[float]] = defaultdict(list)     # TБП
        self._source_service_times: Dict[int, List[float]] = defaultdict(list)  # Tобсл

    def log_event(self, event_type: str, time: float, **details) -> None:
        payload = {"type": event_type, "time": round(time, 4)}
        payload.update(details)
        self.events.append(payload)

    def log_generation(self, call: Call, time: float) -> None:
        self._source_generated[call.source_id] += 1
        self.log_event("generated", time, call_id=call.id, source=call.source_id)

    def log_buffer(self, call: Call, time: float, action: str) -> None:
        self.log_event(action, time, call_id=call.id, source=call.source_id)

    def log_start(self, call: Call, operator_id: int, start_time: float) -> None:
        self.started_calls += 1
        self._call_start_times[call.id] = start_time
        wait_time = start_time - call.arrival_time
        self._call_wait_times.append(wait_time)
        self._source_wait_times[call.source_id].append(wait_time)
        self.log_event("processing_started", start_time, call_id=call.id, operator_id=operator_id)

    def log_done(self, call: Call, finish_time: float) -> None:
        self.completed_calls += 1
        self._source_completed[call.source_id] += 1
        start_time = self._call_start_times.get(call.id, finish_time)
        service_time = finish_time - start_time
        self._call_service_times.append(service_time)
        self._source_service_times[call.source_id].append(service_time)
        self.log_event("processing_completed", finish_time, call_id=call.id)

    def log_reject(self, reason: str, time: float, call: Call | None = None) -> None:
        self.rejected_calls += 1
        if call is not None:
            self._source_rejected[call.source_id] += 1
        self.log_event(
            "reject",
            time,
            reason=reason,
            call_id=None if call is None else call.id,
            source=None if call is None else call.source_id,
        )

    def rejection_percent(self) -> float:
        total = self.started_calls + self.rejected_calls
        if total == 0:
            return 0.0
        return round(self.rejected_calls / total * 100.0, 2)

    def per_source_stats(self) -> Dict[int, Dict[str, float]]:
        result: Dict[int, Dict[str, float]] = {}
        for source_id in sorted(self._source_generated.keys()):
            n_gen = self._source_generated[source_id]
            n_rej = self._source_rejected.get(source_id, 0)
            waits = self._source_wait_times.get(source_id, [])
            services = self._source_service_times.get(source_id, [])

            p_otk = n_rej / n_gen if n_gen > 0 else 0.0
            t_bp = _mean(waits)
            t_obsl = _mean(services)
            t_preb = t_bp + t_obsl  # Tпреб = TБП + Tобсл
            d_bp = _variance(waits)
            d_obsl = _variance(services)

            result[source_id] = {
                "count": n_gen,
                "p_otk": round(p_otk, 4),
                "T_preb": round(t_preb, 4),
                "T_bp": round(t_bp, 4),
                "T_obsl": round(t_obsl, 4),
                "D_bp": round(d_bp, 4),
                "D_obsl": round(d_obsl, 4),
            }
        return result

    def record_snapshot(
        self,
        time: float,
        events: Sequence[Dict],
        buffer_state: Dict,
        operator_state: Sequence[Dict],
        pointer_state: Dict,
    ) -> None:
        snapshot = {
            "time": round(time, 2),
            "events": list(events),
            "buffer": buffer_state,
            "operators": list(operator_state),
            "pointers": pointer_state,
            "reject_percent": self.rejection_percent(),
        }
        self.snapshots.append(snapshot)

    def record_time_series(self, time: float, queue_length: int) -> None:
        self._queue_history.append((time, queue_length))
        self._rejection_rate_history.append((time, self.rejection_percent()))

    def store_operator_utilization(self, utilization: Dict[int, float]) -> None:
        self._operator_utilization = utilization

    def get_stats(self) -> Dict:
        avg_wait_time = _mean(self._call_wait_times)
        avg_service_time = _mean(self._call_service_times)
        return {
            "total_started": self.started_calls,
            "total_completed": self.completed_calls,
            "total_rejected": self.rejected_calls,
            "avg_wait_time": avg_wait_time,
            "avg_service_time": avg_service_time,
            "events": self.events,
            "reject_percent": self.rejection_percent(),
        }

    def render_graphs(self, total_time: float, target_dir: Path | str) -> Path:
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)
        output_file = target_path / "auto_mode_metrics.png"

        fig, axes = plt.subplots(3, 1, figsize=(10, 12))

        queue_times = [t for t, _ in self._queue_history]
        queue_values = [v for _, v in self._queue_history]
        axes[0].plot(queue_times, queue_values, color="tab:blue")
        axes[0].set_title("Длина буфера во времени")
        axes[0].set_xlabel("Время")
        axes[0].set_ylabel("Количество заявок")
        axes[0].grid(True, alpha=0.3)

        reject_times = [t for t, _ in self._rejection_rate_history]
        reject_values = [v for _, v in self._rejection_rate_history]
        axes[1].plot(reject_times, reject_values, color="tab:red")
        axes[1].set_title("Процент отказов")
        axes[1].set_xlabel("Время")
        axes[1].set_ylabel("%")
        axes[1].grid(True, alpha=0.3)

        if self._operator_utilization:
            operators = list(self._operator_utilization.keys())
            values = [round(self._operator_utilization[op] * 100.0, 2) for op in operators]
            axes[2].bar([f"П{op}" for op in operators], values, color="tab:green")
        axes[2].set_ylim(0, 100)
        axes[2].set_title("Загрузка операторов")
        axes[2].set_ylabel("% времени занятости")
        axes[2].set_xlabel("Оператор")
        axes[2].grid(True, axis="y", alpha=0.3)

        fig.tight_layout()
        fig.savefig(output_file, dpi=200)
        plt.close(fig)
        return output_file


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _variance(values: List[float]) -> float:
    """Несмещённая дисперсия (n-1)."""
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    return sum((x - m) ** 2 for x in values) / (len(values) - 1)

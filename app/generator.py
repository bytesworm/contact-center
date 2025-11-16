from __future__ import annotations

from typing import Dict, List, Sequence
import numpy as np
from .call import Call


class Generator:
    def __init__(self, lambda_rate: Sequence[float] | float, num_sources: int) -> None:
        if isinstance(lambda_rate, Sequence):
            if len(lambda_rate) != num_sources:
                raise ValueError("Количество интенсивностей не совпадает с количеством источников")
            self.lambda_rates = list(lambda_rate)
        else:
            self.lambda_rates = [float(lambda_rate)] * num_sources
        
        self.num_sources = num_sources
        self._next_arrival_time: Dict[int, float | None] = {i: None for i in range(1, num_sources + 1)}
        self._call_counter = 0
    
    def _schedule_next(self, source_id: int, now: float) -> None:
        rate = self.lambda_rates[source_id - 1]
        interval = np.random.exponential(1.0 / rate)
        self._next_arrival_time[source_id] = now + interval
    
    def generate_poisson(self, now: float) -> List[Call]:
        produced: List[Call] = []
        for source_id in range(1, self.num_sources + 1):
            if self._next_arrival_time[source_id] is None:
                self._schedule_next(source_id, now)
            
            target_time = self._next_arrival_time[source_id]
            if target_time is None:
                continue
            
            if now >= target_time:
                service_time = float(np.random.uniform(1.0, 10.0))
                call = Call(
                    call_id=self._call_counter,
                    source_id=source_id,
                    arrival_time=target_time,
                    service_time=service_time,
                )
                produced.append(call)
                self._call_counter += 1
                self._schedule_next(source_id, now)
        
        return produced

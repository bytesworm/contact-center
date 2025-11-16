from __future__ import annotations

from typing import Dict, Optional
from .call import Call


class Operator:
    def __init__(self, operator_id: int) -> None:
        self.id = operator_id
        self._busy_until: float = 0.0
        self._current_call: Optional[Call] = None
        self._total_busy_time: float = 0.0
    
    def is_free(self, now: float) -> bool:
        return now >= self._busy_until or self._current_call is None
    
    def take_call(self, call: Call, now: float) -> None:
        self._current_call = call
        self._busy_until = now + call.service_time
    
    def finish_call(self, now: float) -> Optional[Call]:
        call = self._current_call
        if call is not None:
            self._total_busy_time += call.service_time
        self._current_call = None
        return call
    
    def get_current_call(self) -> Optional[Call]:
        return self._current_call
    
    def should_finish_call(self, now: float) -> bool:
        return self._current_call is not None and now >= self._busy_until
    
    def describe(self, now: float) -> Dict:
        call = self._current_call
        return {
            "id": self.id,
            "status": "free" if call is None or self.is_free(now) else "busy",
            "call_id": None if call is None else call.id,
            "release_time": self._busy_until if call is not None else now,
        }
    
    def utilization(self, total_time: float) -> float:
        if total_time <= 0:
            return 0.0
        return min(1.0, self._total_busy_time / total_time)

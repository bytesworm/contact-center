from __future__ import annotations

from typing import Dict, List, Optional
from .call import Call


class Buffer:
    """Кольцевой буфер (Д1ОЗ1), выборка FIFO (Д2Б1)."""

    def __init__(self, size: int) -> None:
        self.size = size
        self._queue: List[Call] = []
        self._insert_pointer = 0
        self._remove_pointer = 0

    def enqueue(self, call: Call) -> bool:
        if self.is_full():
            return False
        self._queue.append(call)
        self._insert_pointer = (self._insert_pointer + 1) % self.size
        return True

    def dequeue(self) -> Optional[Call]:
        if not self._queue:
            return None
        call = self._queue.pop(0)
        self._remove_pointer = (self._remove_pointer + 1) % self.size
        return call

    def remove_call(self, call: Call) -> bool:
        try:
            self._queue.remove(call)
            self._remove_pointer = (self._remove_pointer + 1) % self.size
            return True
        except ValueError:
            return False

    def is_full(self) -> bool:
        return len(self._queue) >= self.size

    def is_empty(self) -> bool:
        return len(self._queue) == 0

    def get_queue_length(self) -> int:
        return len(self._queue)

    def get_state(self) -> Dict:
        return {
            "mode": "shared",
            "total": len(self._queue),
            "calls": [call.id for call in self._queue],
            "by_source": self._by_source(),
        }

    def get_pointer_state(self) -> Dict:
        return {
            "mode": "shared",
            "insert": self._insert_pointer,
            "remove": self._remove_pointer,
        }

    def get_buffer_slots(self) -> List[Dict]:
        slots: List[Dict] = []
        for i, call in enumerate(self._queue):
            slots.append({
                "position": i + 1,
                "time": round(call.arrival_time, 2),
                "source": call.source_id,
                "call_id": call.id,
            })
        return slots

    def _by_source(self) -> Dict[int, List[int]]:
        result: Dict[int, List[int]] = {}
        for call in self._queue:
            result.setdefault(call.source_id, []).append(call.id)
        return result

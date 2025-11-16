from __future__ import annotations

from typing import Dict, List, Optional
from .call import Call


class Buffer:
    def __init__(
        self,
        size: int,
        mode: str = "shared",
        zone_capacities: Optional[Dict[int, int]] = None,
    ) -> None:
        self.size = size
        self.mode = mode
        self.zone_capacities = zone_capacities or {}
        self._queue: List[Call] = []
        self._insert_pointer = 0
        self._remove_pointer = 0
        self._zone_pointers: Dict[int, Dict[str, int]] = {}
    
    def enqueue(self, call: Call) -> bool:
        if self.mode == "zonal":
            limit = self.zone_capacities.get(
                call.source_id,
                max(1, self.size // max(1, len(self.zone_capacities) or 1)),
            )
            if self._count_for_source(call.source_id) >= limit:
                return False
            if len(self._queue) >= self.size:
                return False
        elif self.is_full():
            return False
        
        self._queue.append(call)
        self._advance_pointer("insert", call.source_id)
        return True
    
    def dequeue(self) -> Optional[Call]:
        if not self._queue:
            return None
        call = self._queue.pop(0)
        self._advance_pointer("remove", call.source_id)
        return call
    
    def drain_for_source(self, source_id: int) -> List[Call]:
        drained: List[Call] = []
        remaining: List[Call] = []
        for call in self._queue:
            if call.source_id == source_id:
                drained.append(call)
            else:
                remaining.append(call)
        self._queue = remaining
        if drained:
            self._advance_pointer("remove", source_id, steps=len(drained))
        return drained
    
    def remove_call(self, call: Call) -> bool:
        try:
            self._queue.remove(call)
            self._advance_pointer("remove", call.source_id)
            return True
        except ValueError:
            return False
    
    def is_full(self) -> bool:
        return len(self._queue) >= self.size
    
    def is_empty(self) -> bool:
        return len(self._queue) == 0
    
    def get_queue_length(self) -> int:
        return len(self._queue)
    
    def _count_for_source(self, source_id: int) -> int:
        return sum(1 for call in self._queue if call.source_id == source_id)
    
    def get_state(self) -> Dict:
        state: Dict[str, object] = {
            "mode": self.mode,
            "total": len(self._queue),
            "calls": [call.id for call in self._queue],
            "by_source": {},
        }
        for call in self._queue:
            bucket = state["by_source"].setdefault(call.source_id, [])
            bucket.append(call.id)
        return state
    
    def get_pointer_state(self) -> Dict:
        if self.mode == "zonal":
            return {
                "mode": "zonal",
                "zones": self._zone_pointers.copy(),
            }
        return {
            "mode": "shared",
            "insert": self._insert_pointer,
            "remove": self._remove_pointer,
        }
    
    def _advance_pointer(self, pointer_type: str, source_id: int, steps: int = 1) -> None:
        if self.size == 0:
            return
        if self.mode == "zonal":
            info = self._zone_pointers.setdefault(source_id, {"insert": 0, "remove": 0})
            key = "insert" if pointer_type == "insert" else "remove"
            zone_size = self.zone_capacities.get(source_id, self.size)
            info[key] = (info[key] + steps) % max(1, zone_size)
        else:
            if pointer_type == "insert":
                self._insert_pointer = (self._insert_pointer + steps) % self.size
            else:
                self._remove_pointer = (self._remove_pointer + steps) % self.size

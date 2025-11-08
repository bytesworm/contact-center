from typing import Optional
from .call import Call


class Operator:
    def __init__(self, operator_id: int) -> None:
        self.id = operator_id
        self._busy_until: float = 0.0
        self._current_call: Optional[Call] = None
    
    def is_free(self, now: float) -> bool:
        return now >= self._busy_until
    
    def take_call(self, call: Call, now: float) -> None:
        self._current_call = call
        self._busy_until = now + call.service_time
    
    def finish_call(self) -> Optional[Call]:
        call = self._current_call
        self._current_call = None
        return call
    
    def get_current_call(self) -> Optional[Call]:
        return self._current_call
    
    def should_finish_call(self, now: float) -> bool:
        return self._current_call is not None and now >= self._busy_until


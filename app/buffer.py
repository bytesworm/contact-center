from typing import Optional, List
from .call import Call


class Buffer:
    def __init__(self, size: int):
        self.size = size
        self._queue: List[Call] = []
    
    def enqueue(self, call: Call) -> bool:
        if self.is_full():
            return False
        
        self._queue.append(call)
        return True
    
    def dequeue(self) -> Optional[Call]:
        if len(self._queue) == 0:
            return None
        
        return self._queue.pop(0)
    
    def is_full(self) -> bool:
        return len(self._queue) >= self.size
    
    def is_empty(self) -> bool:
        return len(self._queue) == 0
    
    def get_queue_length(self) -> int:
        return len(self._queue)
    
    def remove_call(self, call: Call) -> bool:
        if call in self._queue:
            self._queue.remove(call)
            return True
        return False

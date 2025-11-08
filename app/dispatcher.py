from typing import List, Optional
from .call import Call
from .buffer import Buffer
from .operator import Operator
from .metrics import Metrics


class Dispatcher:
    def __init__(self, buffer: Buffer, operators: List[Operator], metrics: Metrics):
        self.buffer = buffer
        self.operators = operators
        self.metrics = metrics
    
    def on_arrival(self, call: Call, now: float):
        if not self.buffer.enqueue(call):
            self.metrics.log_reject("overflow", now, call.id)
            return
        
        self.try_dispatch(now)
    
    def try_dispatch(self, now: float):
        while not self.buffer.is_empty():
            free_operator = self._find_free_operator(now)
            if free_operator is None:
                break
            
            call = self.buffer.dequeue()
            if call is None:
                break
            
            free_operator.take_call(call, now)
            self.metrics.log_start(call, free_operator.id)
    
    def _find_free_operator(self, now: float) -> Optional[Operator]:
        for operator in self.operators:
            if operator.is_free(now):
                return operator
        return None
    
    def update_operators(self, now: float):
        for operator in self.operators:
            if not operator.is_free(now) and operator._busy_until <= now:
                call = operator.finish_call()
                if call:
                    self.metrics.log_done(call, now)
                self.try_dispatch(now)
    
    def remove_call_from_queue(self, call: Call, now: float):
        if self.buffer.remove_call(call):
            self.metrics.log_reject("hangup", now, call.id)


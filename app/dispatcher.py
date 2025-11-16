from __future__ import annotations

from typing import List, Optional
from .buffer import Buffer
from .call import Call
from .metrics import Metrics
from .operator import Operator


class Dispatcher:
    def __init__(
        self,
        buffer: Buffer,
        operators: List[Operator],
        metrics: Metrics,
        direct_dispatch: bool = False,
    ) -> None:
        self.buffer = buffer
        self.operators = operators
        self.metrics = metrics
        self.direct_dispatch = direct_dispatch
        self.active_packet_source: Optional[int] = None
        self.packet_queue: List[Call] = []
        self._packet_in_service = 0
    
    def on_arrival(self, call: Call, now: float) -> None:
        self.metrics.log_generation(call, now)
        if self.direct_dispatch and self.active_packet_source is None:
            if self._dispatch_immediately(call, now):
                return
        
        if self.buffer.enqueue(call):
            self.metrics.log_buffer(call, now, "buffered")
        else:
            self.metrics.log_reject("buffer_overflow", now, call)
        self.try_dispatch(now)
    
    def _dispatch_immediately(self, call: Call, now: float) -> bool:
        free_operator = self._find_free_operator(now)
        if free_operator is None:
            return False
        self.metrics.log_event("sent_direct", now, call_id=call.id, operator_id=free_operator.id)
        self._start_processing(free_operator, call, now)
        return True
    
    def try_dispatch(self, now: float) -> None:
        free = self._collect_free(now)
        while free:
            if self.active_packet_source is None:
                if self.buffer.is_empty():
                    break
                if not self._start_packet(now):
                    break
            if not self.packet_queue:
                break
            operator = free.pop(0)
            call = self.packet_queue.pop(0)
            self.metrics.log_event("packet_select", now, call_id=call.id, source=call.source_id)
            self._start_processing(operator, call, now)
            self._packet_in_service += 1
    
    def _start_packet(self, now: float) -> bool:
        call = self.buffer.dequeue()
        if call is None:
            return False
        self.metrics.log_buffer(call, now, "buffer_pop")
        packet_calls = [call] + self.buffer.drain_for_source(call.source_id)
        self.active_packet_source = call.source_id
        self._packet_in_service = 0
        self.packet_queue = packet_calls
        self.metrics.log_event(
            "packet_created",
            now,
            source=self.active_packet_source,
            size=len(self.packet_queue),
        )
        return True
    
    def _start_processing(self, operator: Operator, call: Call, now: float) -> None:
        operator.take_call(call, now)
        self.metrics.log_event("sent_to_operator", now, operator_id=operator.id, call_id=call.id)
        self.metrics.log_start(call, operator.id, now)
    
    def _collect_free(self, now: float) -> List[Operator]:
        return [op for op in self.operators if op.is_free(now)]
    
    def _find_free_operator(self, now: float) -> Optional[Operator]:
        for operator in self.operators:
            if operator.is_free(now):
                return operator
        return None
    
    def update_operators(self, now: float) -> None:
        for operator in self.operators:
            if operator.should_finish_call(now):
                call = operator.finish_call(now)
                if call:
                    self.metrics.log_done(call, now)
                    if self.active_packet_source == call.source_id:
                        self._packet_in_service = max(0, self._packet_in_service - 1)
                        if self._packet_in_service == 0 and not self.packet_queue:
                            self.metrics.log_event("packet_completed", now, source=call.source_id)
                            self.active_packet_source = None
                self.try_dispatch(now)
    
    def remove_call_from_queue(self, call: Call, now: float) -> None:
        if self.buffer.remove_call(call):
            self.metrics.log_reject("hangup", now, call)

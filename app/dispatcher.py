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
    ) -> None:
        self.buffer = buffer
        self.operators = operators
        self.metrics = metrics

    def on_arrival(self, call: Call, now: float) -> None:
        self.metrics.log_generation(call, now)

        if self.buffer.enqueue(call):
            self.metrics.log_buffer(call, now, "buffered")
        else:
            self.metrics.log_reject("overflow", now, call)

        self.try_dispatch(now)

    def try_dispatch(self, now: float) -> None:
        """Д2Б1 (FIFO) + Д2П1 (приоритет по номеру прибора)."""
        while True:
            operator = self._find_free_operator(now)
            if operator is None:
                break
            call = self.buffer.dequeue()
            if call is None:
                break
            self.metrics.log_event(
                "sent_to_operator", now, operator_id=operator.id, call_id=call.id,
            )
            self._start_processing(operator, call, now)

    def update_operators(self, now: float) -> None:
        any_finished = False
        for operator in self.operators:
            if operator.should_finish_call(now):
                call = operator.finish_call(now)
                if call:
                    self.metrics.log_done(call, now)
                    any_finished = True
        if any_finished:
            self.try_dispatch(now)

    def remove_call_from_queue(self, call: Call, now: float) -> None:
        if self.buffer.remove_call(call):
            self.metrics.log_reject("hangup", now, call)

    def _find_free_operator(self, now: float) -> Optional[Operator]:
        for operator in self.operators:
            if operator.is_free(now):
                return operator
        return None

    def _start_processing(self, operator: Operator, call: Call, now: float) -> None:
        operator.take_call(call, now)
        self.metrics.log_start(call, operator.id, now)

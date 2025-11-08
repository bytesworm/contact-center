from typing import Dict
from .generator import Generator
from .dispatcher import Dispatcher
from .buffer import Buffer
from .operator import Operator
from .metrics import Metrics


class Simulation:
    def __init__(self, lambda_rate: float, buffer_size: int, num_operators: int) -> None:
        self.clock = 0.0
        self.generator = Generator(lambda_rate)
        self.buffer = Buffer(buffer_size)
        self.operators = [Operator(i + 1) for i in range(num_operators)]
        self.metrics = Metrics()
        self.dispatcher = Dispatcher(self.buffer, self.operators, self.metrics)
    
    def tick(self, delta_time: float = 0.1) -> None:
        self.clock += delta_time
        
        call = self.generator.generate_poisson(self.clock)
        if call:
            self.dispatcher.on_arrival(call, self.clock)
        
        self.dispatcher.update_operators(self.clock)
    
    def run(self, duration: float, delta_time: float = 0.1) -> None:
        while self.clock < duration:
            self.tick(delta_time)
        
        while not self.buffer.is_empty() or any(not op.is_free(self.clock) for op in self.operators):
            self.clock += delta_time
            self.dispatcher.update_operators(self.clock)
    
    def get_stats(self) -> Dict:
        return self.metrics.get_stats()


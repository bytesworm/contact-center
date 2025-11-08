import numpy as np
from typing import Optional
from .call import Call


class Generator:
    def __init__(self, lambda_rate: float) -> None:
        self.lambda_rate = lambda_rate
        self._next_arrival_time = None
        self._call_counter = 0
    
    def generate_poisson(self, now: float) -> Optional[Call]:
        if self._next_arrival_time is None:
            interval = np.random.exponential(1.0 / self.lambda_rate)
            self._next_arrival_time = now + interval
        
        if now >= self._next_arrival_time:
            service_time = np.random.uniform(1.0, 10.0)
            
            call = Call(
                call_id=self._call_counter,
                source_id=1,
                arrival_time=self._next_arrival_time,
                service_time=service_time
            )
            
            self._call_counter += 1
            
            interval = np.random.exponential(1.0 / self.lambda_rate)
            self._next_arrival_time = now + interval
            
            return call
        
        return None

from typing import List, Dict
from .call import Call


class Metrics:
    def __init__(self) -> None:
        self.events: List[Dict] = []
        self.rejected_calls: int = 0
        self.completed_calls: int = 0
        self.started_calls: int = 0
        self._call_start_times: Dict[int, float] = {}
        self._call_wait_times: List[float] = []
        self._call_service_times: List[float] = []
    
    def log_start(self, call: Call, operator_id: int, start_time: float) -> None:
        self.started_calls += 1
        self._call_start_times[call.id] = start_time
        wait_time = start_time - call.arrival_time
        self._call_wait_times.append(wait_time)
        self.events.append({
            'type': 'start',
            'call_id': call.id,
            'operator_id': operator_id,
            'time': start_time
        })
    
    def log_done(self, call: Call, finish_time: float) -> None:
        self.completed_calls += 1
        if call.id in self._call_start_times:
            service_time = finish_time - self._call_start_times[call.id]
            self._call_service_times.append(service_time)
        self.events.append({
            'type': 'done',
            'call_id': call.id,
            'time': finish_time
        })
    
    def log_reject(self, reason: str, time: float, call_id: int = None) -> None:
        self.rejected_calls += 1
        self.events.append({
            'type': 'reject',
            'reason': reason,
            'call_id': call_id,
            'time': time
        })
    
    def get_stats(self) -> Dict:
        avg_wait_time = sum(self._call_wait_times) / len(self._call_wait_times) if self._call_wait_times else 0.0
        avg_service_time = sum(self._call_service_times) / len(self._call_service_times) if self._call_service_times else 0.0
        
        return {
            'total_started': self.started_calls,
            'total_completed': self.completed_calls,
            'total_rejected': self.rejected_calls,
            'avg_wait_time': avg_wait_time,
            'avg_service_time': avg_service_time,
            'events': self.events
        }


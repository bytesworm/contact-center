from typing import List, Dict
from .call import Call


class Metrics:
    def __init__(self):
        self.events: List[Dict] = []
        self.rejected_calls: int = 0
        self.completed_calls: int = 0
        self.started_calls: int = 0
    
    def log_start(self, call: Call, operator_id: int):
        self.started_calls += 1
        self.events.append({
            'type': 'start',
            'call_id': call.id,
            'operator_id': operator_id,
            'time': call.arrival_time
        })
    
    def log_done(self, call: Call, finish_time: float):
        self.completed_calls += 1
        self.events.append({
            'type': 'done',
            'call_id': call.id,
            'time': finish_time
        })
    
    def log_reject(self, reason: str, time: float, call_id: int = None):
        self.rejected_calls += 1
        self.events.append({
            'type': 'reject',
            'reason': reason,
            'call_id': call_id,
            'time': time
        })
    
    def get_stats(self) -> Dict:
        return {
            'total_started': self.started_calls,
            'total_completed': self.completed_calls,
            'total_rejected': self.rejected_calls,
            'events': self.events
        }


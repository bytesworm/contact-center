class Call:
    def __init__(self, call_id: int, source_id: int, arrival_time: float, service_time: float) -> None:
        self.id = call_id
        self.source_id = source_id
        self.arrival_time = arrival_time
        self.service_time = service_time
    
    def __repr__(self) -> str:
        return f"Call(id={self.id}, source={self.source_id}, arrival={self.arrival_time:.2f}, service={self.service_time:.2f})"

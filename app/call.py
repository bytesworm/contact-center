from dataclasses import dataclass


@dataclass
class Call:
    call_id: int
    source_id: int
    arrival_time: float
    service_time: float
    
    @property
    def id(self) -> int:
        return self.call_id
    
    def __repr__(self) -> str:
        return (
            f"Call(id={self.call_id}, source={self.source_id}, "
            f"arrival={self.arrival_time:.2f}, service={self.service_time:.2f})"
        )

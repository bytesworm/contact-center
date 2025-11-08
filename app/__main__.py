from .simulation import Simulation


def main() -> None:
    lambda_rate = 0.5
    buffer_size = 10
    num_operators = 2
    duration = 100.0
    
    sim = Simulation(lambda_rate, buffer_size, num_operators)
    sim.run(duration)
    
    stats = sim.get_stats()
    
    print("Simulation Results:")
    print(f"Total started calls: {stats['total_started']}")
    print(f"Total completed calls: {stats['total_completed']}")
    print(f"Total rejected calls: {stats['total_rejected']}")
    print(f"Average wait time: {stats['avg_wait_time']:.2f}")
    print(f"Average service time: {stats['avg_service_time']:.2f}")
    print(f"Total events: {len(stats['events'])}")


if __name__ == "__main__":
    main()


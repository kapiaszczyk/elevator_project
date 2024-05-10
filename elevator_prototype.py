import random
import time
import threading

from queue import Queue, Empty

ELEVATOR_EVENT = 'elevator_button_press'
FLOOR_EVENT = 'floor_button_press'
FLOORS = 20
ELEVEATORS_AMOUNT = 4
ELEVATOR_SPEED = 5

class ID_Generator:
    
    def __init__(self):
        self.id = 0

    def get_next_id(self):
        self.id = self.id + 1 
        return self.id

generator = ID_Generator()

class Event:

    def __init__(self, event_type, origin, destination, direction):
        self.event_type = event_type
        self.origin = origin
        self.destination = destination
        self.direction = direction

    def get_event_type(self):
        return self.event_type

    def get_destination(self):
        return self.destination
    
    def get_direction(self):
        return self.direction
    
    def get_origin(self):
        return self.origin

class EventBus:
    def __init__(self):
        self.subscribers = {}
    
    def subscribe(self, event_type, subscriber):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(subscriber)
    
    def publish(self, obj: Event):
        event_type = obj.get_event_type()
        if event_type in self.subscribers:
            for subscriber in self.subscribers[event_type]:
                subscriber.handle_event(obj)


class State:
        """Represents a state of the elevator"""

        def __init__(self) -> None:
            self.elevator_id = None
            self.current_floor = None
            self.destination_floor = None

        def __init__(self, id, current, destination):
            self.elevator_id = id
            self.current_floor = current
            self.destination_floor = destination

        def set_current_floor(self, floor):
            self.current_floor = floor

        def set_destination_floor(self, floor):
            self.destination_floor = floor

        def get_current_floor(self):
            return self.current_floor

        def to_string(self):
            return self.elevator_id, self.current_floor, self.destination_floor


class Elevator:
    """Represents an elevator."""

    def __init__(self) -> None:
        self.id = generator.get_next_id()
        self.state = State(self.id, 0, 0)
        self.floor_queue = Queue()
        self.is_active = True
        self.elevator_thread = threading.Thread(target=self.process_jobs)
        self.elevator_thread.start()

    def print_data(self):
        print(f"I am elevetor {self.id}. My state is {self.state.to_string()}. Queue is {self.floor_queue.qsize()}.")

    def get_id(self):
        return self.id
    
    def add_request(self, requested_floor):
        self.floor_queue.put(requested_floor)
        print(f"Added request to floor {requested_floor} to the queue. Queue is {self.floor_queue.queue}")

    def process_jobs(self):
        while self.is_active:
            try:
                target_floor = self.floor_queue.get(timeout=1)
                distance = abs(self.state.current_floor - target_floor)
                needed_time = (distance / ELEVATOR_SPEED)
                print(f"Elevator {self.id} going to floor {target_floor}.")
                print(f"This will take {round(needed_time, 3)} seconds, since elevator is now at floor {self.get_state().get_current_floor()}.")

                self.state.set_destination_floor(target_floor)

                time.sleep(needed_time)
                self.floor_queue.task_done()

                self.state.set_current_floor(target_floor)
                self.state.set_destination_floor(None)

                print(f"Elevator {self.id} reached floor {target_floor}.")
            except Empty:
                continue

    def stop(self):
        self.is_active = False
        self.elevator_thread.join()
    

    def get_queue(self):
        return self.floor_queue
    
    def get_state(self) -> State:
        return self.state
    
    def set_state(self, state: State):
        self.state = state
    
    def print_queue(self):
        print(f"Queue: {list(self.floor_queue.queue)}")

class InternalDispatcher:
    """Represents dispatching requests within the elevator."""

    def __init__(self, id, obj: Elevator):
        self.elevator = obj
        self.elevator_id = obj.get_id()

    def handle_event(self, obj: Event):
        if obj.get_event_type() == ELEVATOR_EVENT:
            floor = obj.get_destination()
            elevator_id = obj.get_origin()
            print(f"The elevator {elevator_id} was requested to go to floor {floor} from inside.")
            self.elevator.add_request(floor)
        elif obj.get_event_type() == FLOOR_EVENT:
            floor = obj.get_origin()
            print(f"The elevator {self.elevator_id} was tasked to go to floor {floor} by ExternalDispatcher.")
            self.elevator.add_request(floor)

    def get_id(self):
        return self.elevator_id


class ExternalDispatcher:
    """Represents dispatching requests for all elevators."""

    def __init__(self):
        self.internal_dispatchers = []
        self.num_dispatchers = None
        self.last_called_dispatcher = -1

    def set_dispatchers(self, dispatchers: list[InternalDispatcher]):
        for d in dispatchers:
            self.internal_dispatchers.append(d)
        self.num_dispatchers = len(self.internal_dispatchers)
    
    def handle_event(self, obj: Event):
        if obj.get_event_type() == FLOOR_EVENT:
            floor = obj.get_origin()
            direction = obj.get_direction()
            print(f"ExternalDispatcher: Any elevator is called to floor {floor} was called for a destination that is {direction}")

            # Round-robin the request to the next elevator
            self.last_called_dispatcher = (self.last_called_dispatcher + 1) % self.num_dispatchers
            target_dispatcher = self.internal_dispatchers[self.last_called_dispatcher]
            target_dispatcher.handle_event(obj)

            print(f"ExternalDispatcher: Request from floor {floor} passed to elevator {target_dispatcher.get_id()}")

        elif obj.get_event_type() == ELEVATOR_EVENT:
            target_dispatcher_id = obj.get_origin()
            target_dispatcher = self.get_dispatcher_by_id(target_dispatcher_id)
            destination = obj.get_destination()
            if target_dispatcher:
                print(f"ExternalDispatcher: Button was pressed in elevator {target_dispatcher_id} with request to floor {destination}")
                target_dispatcher.handle_event(obj)
            else:
                print(f"ExternalDispatcher: Dispatcher with ID {target_dispatcher_id} not found")

    def get_dispatcher_by_id(self, id):
        for dispatcher in self.internal_dispatchers:
            if dispatcher.get_id() == id:
                return dispatcher
        return None

class ElevatorContext:
    """Holds all elevator context."""

    def __init__(self):
        self.elevators = self.initalise_elevators(ELEVEATORS_AMOUNT)
        self.external_dispatcher = ExternalDispatcher()
        self.floors = FLOORS
        self.event_bus = EventBus()

        # Generate internal_dispatchers and assign them an elevator
        int_dispatchers = [InternalDispatcher(elevator.get_id(), elevator) for elevator in self.elevators]

        # Pass the dispatchers to the ExternalDispatcher
        self.external_dispatcher.set_dispatchers(int_dispatchers)

        # Subscribe the dispatcher to the events on the bus
        self.event_bus.subscribe(FLOOR_EVENT, self.external_dispatcher)
        self.event_bus.subscribe(ELEVATOR_EVENT, self.external_dispatcher)

    def initalise_elevators(self, number_of_elevators):
        """Sets up the amount of elevators in the system"""
        print("Initalising elevators...")
        return [Elevator() for _ in range(number_of_elevators)]


    def add_elevator(self, elevator):
        self.elevators.append(elevator)

    def add_elevators(self, elevators):
        for elevator in elevators:
            self.add_elevator(elevator)

    def set_floors(self, amount):
        self.floors = amount

    def set_external_dispatcher(self, dispatcher):
        self.external_dispatcher = dispatcher

    def show_elevators(self):
        for elevator in self.elevators:
            elevator.print_data()

    def get_elevators(self):
        return self.elevators
    
    def update_elevator_status(self, elevator_id, current_floor, destination_floor):
        for elevator in self.elevators:
            if elevator.get_id() == elevator_id:
                elevator.set_state(State(elevator_id, current_floor, destination_floor))

    def publish_event(self, request_floor_origin, direction):
        event = Event(ELEVATOR_EVENT, request_floor_origin, None, direction)
        self.event_bus.publish(event)

    def stop_all(self):
        print("Stopping elevators")
        for elevator in self.elevators:
            elevator.stop()
        print("All elevators stopped")

    def generate_random_event(self):

        elevator_event = random.choice([True, False])

        if elevator_event:
            event = Event(ELEVATOR_EVENT, random.randint(1, ELEVEATORS_AMOUNT - 1), random.randint(0, FLOORS), None)
            self.event_bus.publish(event)
        else:
            event = Event(FLOOR_EVENT, random.randint(1, FLOORS), None, random.choice(["UP", "DOWN"]))
            self.event_bus.publish(event)

class ElevatorSystem:
    """Represents implementation of the interface."""

    def __init__(self, context: ElevatorContext):
        self.context = context

    def pickup(self, request_floor_origin, direction):
        """Represents a call for an elevator from a floor."""
        self.context.publish_event(request_floor_origin, direction)

    def update(self, elevator_id, current_floor, destination_floor):
        """Updates the state of an elevator."""
        self.context.update_elevator_status(elevator_id, current_floor, destination_floor)

    def status(self):
        """Returns collection of statuses"""
        states = []
        elevators = self.context.get_elevators()

        for elevator in elevators:
            states.append(elevator.get_state())
        return states
    
    def step():
        """Performs a step of the simulation"""
    
    def stop_all(self):
        self.context.stop_all()


if __name__ == "__main__":
    """Runs the program."""

    context = ElevatorContext()

    system = ElevatorSystem(context)

    try:
        while True:
            context.generate_random_event()
            time.sleep(1)
    except KeyboardInterrupt:
        system.stop_all()

import random

from queue import Queue
from enum import Enum
from queue import Queue

ELEVATOR_EVENT = 'elevator_button_press'
FLOOR_EVENT = 'floor_button_press'
FLOORS = 80
ELEVEATORS_AMOUNT = 16

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

class Elevator:
    """Represents an elevator."""

    def __init__(self) -> None:
        self.id = generator.get_next_id()
        self.state = State(self.id, 0, 0)
        self.floor_queue = Queue()
        print(f"Creating an elevator, my ID is: {self.id}")

    def print_data(self):
        print(f"I am elevetor {self.id}. My state is {self.state.to_string()}. Queue is {self.floor_queue.qsize()}.")

    def get_id(self):
        return self.id
    
    def add_request(self, requested_floor):
        self.floor_queue.put(requested_floor)
        print(f"Added request to floor {requested_floor} to the queue")
        self.print_queue()

    def get_queue(self):
        return self.floor_queue
    
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
            print(f"The elevator {elevator_id} was requested to go to floor {floor}")
            self.elevator.add_request(floor)

    def get_id(self):
        return self.elevator_id


class ExternalDispatcher:
    """Represents dispatching requests for all elevators."""

    def __init__(self):
        self.internal_dispatchers = []

    def set_dispatchers(self, dispatchers: list[InternalDispatcher]):
        for d in dispatchers:
            self.internal_dispatchers.append(d)
    
    def handle_event(self, obj: Event):
        if obj.get_event_type() == FLOOR_EVENT:
            floor = obj.get_origin()
            direction = obj.get_direction()
            print(f"ExternalDispatcher: Any elevator is called to floor {floor} was called for a destination that is {direction}")
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
        self.elevators = []
        self.external_dispatcher = None
        self.floors = None

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


class ElevatorSystem:
    """Represents implementation of the interface."""

    def __init__(self, context):
        self.context = context

    def pickup(request_floor_origin, direction):
        """Represents a call for an elevator from a floor."""

    def update(elevator_id, current_floor, destination_floor):
        """Updates the state of an elevator."""

    def status():
        """Returns collection of statuses"""
        return {State(), State()}

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

        def to_string(self):
            return self.elevator_id, self.current_floor, self.destination_floor


def initalise_elevators(number_of_elevators):
    """Sets up the amount of elevators in the system"""
    print("Initalising elevators...")
    return [Elevator() for _ in range(number_of_elevators)]


if __name__ == "__main__":
    """Runs the program."""

    event_bus = EventBus()

    external_dispatcher = ExternalDispatcher()
    context = ElevatorContext()

    elevators = initalise_elevators(ELEVEATORS_AMOUNT)

    context.add_elevators(elevators)
    context.show_elevators()
    context.set_floors(FLOORS)
    context.set_external_dispatcher(external_dispatcher)

    system = ElevatorSystem(context)

    int_dispatchers = [InternalDispatcher(elevator.get_id(), elevator) for elevator in elevators]

    external_dispatcher.set_dispatchers(int_dispatchers)

    event_bus.subscribe(FLOOR_EVENT, external_dispatcher)
    event_bus.subscribe(ELEVATOR_EVENT, external_dispatcher)

    # Number of events to generate
    num_events = 50

    # Generate and publish random events in a loop
    for _ in range(num_events):
        event = Event(ELEVATOR_EVENT, random.randint(1, ELEVEATORS_AMOUNT - 1), random.randint(0, FLOORS), None)
        event_bus.publish(event)
        event = Event(FLOOR_EVENT, random.randint(1, FLOORS), None, random.choice(["UP", "DOWN"]))
        event_bus.publish(event)








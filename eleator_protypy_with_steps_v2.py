import random
import time
import threading

from queue import Queue, Empty

ELEVATOR_EVENT = 'elevator_button_press'
FLOOR_EVENT = 'floor_button_press'
FLOORS = 10
ELEVEATORS_AMOUNT = 2
ELEVATOR_SPEED = 5

class EventExecutor:
    def __init__(self):
        self.event_queue = Queue()  # Event queue

    def schedule_event(self, event):
        self.event_queue.put(event)  # Enqueue event

    def run_next_event(self):
        if not self.event_queue.empty():
            next_event = self.event_queue.get()  # Dequeue event
            next_event.execute()  # Execute the event

executor = EventExecutor()

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

class DispatchEvent:
    def __init__(self, receiver, event):
        self.receiver = receiver
        self.event = event

    def execute(self):
        if isinstance(self.receiver, InternalDispatcher) or isinstance(self.receiver, ExternalDispatcher):
            self.receiver.handle_event(self.event)
        else:
            print(f"Error: Invalid receiver type for dispatch")

        print(f"Event dispatched to {self.receiver}")

class EventBus:
    def __init__(self):
        self.subscribers = {}

    def subscribe(self, event_type, subscriber):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(subscriber)

    def publish(self, event):
        if isinstance(event, DispatchEvent):
            receiver = event.receiver
            receiver_type = type(receiver)
            if receiver_type in self.subscribers:
                for subscriber in self.subscribers[receiver_type]:
                    subscriber.handle_event(event)
        else:
            event_type = event.get_event_type()
            if event_type in self.subscribers:
                for subscriber in self.subscribers[event_type]:
                    subscriber.handle_event(event)

event_bus = EventBus()

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

class ElevatorMoveEvent:
    def __init__(self, elevator, target_floor):
        self.elevator = elevator
        self.target_floor = target_floor

    def execute(self):
            elevator = self.elevator
            state = elevator.get_state()

            target_floor = self.target_floor
            current_floor = state.get_current_floor()

            distance = abs(current_floor - target_floor)
            needed_time = (distance / ELEVATOR_SPEED)

            print(f"[Elevator {elevator.get_id()}]: {current_floor} -> {target_floor} ({needed_time} s).")

            # Set new destination floor
            elevator.set_state(State(elevator.get_id(), current_floor, target_floor))

            # Simulate needed time to move
            time.sleep(needed_time)

            # Dequeue the request
            elevator.floor_queue.task_done()

            # Set the arrived floor as current floor and clear destination
            elevator.set_state(State(elevator.get_id(), target_floor, None))

            print(f"[Elevator {elevator.get_id()}]: Arrived at {target_floor}.")

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
                move_event = ElevatorMoveEvent(self, self.floor_queue.get(timeout=1))
                executor.schedule_event(move_event)
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

    def __init__(self, elevator):
        self.elevator = elevator
        self.elevator_id = elevator.get_id()

    def handle_event(self, event):
        if isinstance(event, DispatchEvent):
            # Extract the inner event and process it
            inner_event = event.event
            if isinstance(inner_event, Event):
                if inner_event.get_event_type() == ELEVATOR_EVENT:
                    floor = inner_event.get_destination()
                    elevator_id = inner_event.get_origin()
                    print(f"The elevator {elevator_id} was requested to go to floor {floor} from inside.")
                    self.elevator.add_request(floor)
                elif inner_event.get_event_type() == FLOOR_EVENT:
                    floor = inner_event.get_origin()
                    print(f"The elevator {self.elevator_id} was tasked to go to floor {floor} by ExternalDispatcher.")
                    self.elevator.add_request(floor)
            else:
                print("Invalid inner event type in DispatchEvent")
        else:
            print("Received non-DispatchEvent object")

    def get_id(self):
        return self.elevator_id

class ExternalDispatcher:
    """Represents dispatching requests for all elevators."""

    def __init__(self):
        self.internal_dispatchers = []

    def set_dispatchers(self, dispatchers):
        self.internal_dispatchers = dispatchers

    def handle_event(self, event):
        if isinstance(event, DispatchEvent):
            if event.receiver == ExternalDispatcher:
                print("This event is meant for the external dispatcher to be assigned to a ")
            else:
                receiver = event.receiver
                receiver.handle_event(event)
        else:
            print("Received non-DispatchEvent object")


class ElevatorContext:
    """Holds all elevator context."""

    def __init__(self):
        self.elevators = self.initalise_elevators(ELEVEATORS_AMOUNT)
        self.external_dispatcher = ExternalDispatcher()
        self.floors = FLOORS
        self.event_bus = event_bus

        # Generate internal_dispatchers and assign them an elevator
        int_dispatchers = [InternalDispatcher(elevator) for elevator in self.elevators]

        # Pass the dispatchers to the ExternalDispatcher
        self.external_dispatcher.set_dispatchers(int_dispatchers)

        # Subscribe the dispatcher to the events on the bus

        for disp in int_dispatchers:
            self.event_bus.subscribe(InternalDispatcher, disp)

        event_bus.subscribe(ExternalDispatcher, self.external_dispatcher)

        # self.event_bus.subscribe(FLOOR_EVENT, self.external_dispatcher)
        # self.event_bus.subscribe(ELEVATOR_EVENT, self.external_dispatcher)

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
        self.event_bus.publish(ExternalDispatcher, event)

    def stop_all(self):
        print("Stopping elevators")
        for elevator in self.elevators:
            elevator.stop()
        print("All elevators stopped")

    def generate_random_event(self):

        elevator_event = random.choice([True, False])
        random_floor = random.randint(0, FLOORS)

        if elevator_event:
            random_elevator = random.randint(1, ELEVEATORS_AMOUNT - 1)
            event = Event(ELEVATOR_EVENT, random_elevator, random_floor, None)
            disp_event = DispatchEvent(InternalDispatcher, event)
            self.event_bus.publish(disp_event)
        else:
            random_direction = random.choice(["UP", "DOWN"])
            event = Event(FLOOR_EVENT, random_floor, None, random_direction)
            disp_event = DispatchEvent(ExternalDispatcher, event)
            self.event_bus.publish(disp_event)

    def generate_random_events(self):

        amount = random.randint(1, 5)

        print(f"Random amount is {amount}")

        for x in range(amount):
            elevator_event = random.choice([True, False])
            random_floor = random.randint(0, FLOORS)

            if elevator_event:
                random_elevator = random.randint(1, ELEVEATORS_AMOUNT - 1)
                event = Event(ELEVATOR_EVENT, random_elevator, random_floor, None)
                self.event_bus.publish(event)
            else:
                random_direction = random.choice(["UP", "DOWN"])
                event = Event(FLOOR_EVENT, random_floor, None, random_direction)
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
            context.generate_random_events()
            while input() == "":
                executor.run_next_event()
                context.generate_random_events()
    except KeyboardInterrupt:
        system.stop_all()
    except TypeError:
        system.stop_all()
    except Exception:
        system.stop_all()

import random
import time
import threading

from queue import Queue, Empty

ELEVATOR_EVENT = 'elevator_button_press'
FLOOR_EVENT = 'floor_button_press'
FLOORS = 10
ELEVEATORS_AMOUNT = 16
ELEVATOR_SPEED = 16

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

            print(f"[Elevator {elevator.get_id()}]: {current_floor} -> {target_floor}")

            if target_floor != current_floor:

                # Set new destination floor
                elevator.set_state(State(elevator.get_id(), current_floor, target_floor))

                # Simulate needed time to move
                time.sleep(needed_time)

                # Set the arrived floor as current floor and clear destination
                elevator.set_state(State(elevator.get_id(), target_floor, None))

                print(f"[Elevator {elevator.get_id()}]: Arrived at {target_floor} ({needed_time} s)")

            else:
                print(f"[Elevator {elevator.get_id()}]: Already at {target_floor}.")


class Elevator:
    """Represents an elevator."""

    def __init__(self) -> None:
        self.id = generator.get_next_id()
        self.state = State(self.id, 0, 0)
        self.floor_queue = Queue()
        self.is_active = True        
        self.elevator_thread = threading.Thread(target=self.process_jobs)
        self.elevator_thread.start()

    def get_id(self):
        return self.id
    
    def add_request(self, requested_floor):
        self.floor_queue.put(requested_floor)
        print(f"Added request to floor {requested_floor} to the queue of elevator {self.id}.")

    def process_jobs(self):
        while self.is_active:
            try:
                move_event = ElevatorMoveEvent(self, self.floor_queue.get(timeout=1))
                executor.schedule_event(move_event)
                # print(f"Added MoveEvent to the ExecutionQueue for elevator {self.get_id()}")
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

    def update_state(self, current_floor, destination_floor):
        self.state.set_current_floor(current_floor)
        self.state.set_destination_floor(destination_floor)

class InternalDispatcher:
    """Represents dispatching requests within the elevator."""

    def __init__(self, id, obj: Elevator):
        self.elevator = obj
        self.elevator_id = obj.get_id()

    def handle_event(self, obj: Event):
        if obj.get_event_type() == ELEVATOR_EVENT:
            floor = obj.get_destination()
            elevator_id = obj.get_origin()
            # print(f"The elevator {elevator_id} was requested to go to floor {floor} from inside.")
            self.elevator.add_request(floor)
        elif obj.get_event_type() == FLOOR_EVENT:
            floor = obj.get_origin()
            # print(f"The elevator {self.elevator_id} was tasked to go to floor {floor} by ExternalDispatcher.")
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
            # print(f"ExternalDispatcher: Any elevator is called to floor {floor} was called for a destination that is {direction}")

            # Round-robin the request to the next elevator
            self.last_called_dispatcher = (self.last_called_dispatcher + 1) % self.num_dispatchers
            target_dispatcher = self.internal_dispatchers[self.last_called_dispatcher]
            target_dispatcher.handle_event(obj)

            # print(f"ExternalDispatcher: Request from floor {floor} passed to elevator {target_dispatcher.get_id()}")

        elif obj.get_event_type() == ELEVATOR_EVENT:
            target_dispatcher_id = obj.get_origin()
            target_dispatcher = self.get_dispatcher_by_id(target_dispatcher_id)
            destination = obj.get_destination()
            if target_dispatcher:
                # print(f"ExternalDispatcher: Button was pressed in elevator {target_dispatcher_id} with request to floor {destination}")
                target_dispatcher.handle_event(obj)
            else:
                print(f"ExternalDispatcher: Dispatcher with ID {target_dispatcher_id} not found")

    def get_dispatcher_by_id(self, id):
        return self.internal_dispatchers[id - 1]

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

    def get_elevators(self):
        return self.elevators

    def update_elevator_status(self, elevator_id, current_floor, destination_floor):

        print(f"Updating elevator {elevator_id} to floor {current_floor} with destination {destination_floor}")

        elevator = self.elevators[elevator_id - 1]
        elevator.update_state(current_floor, destination_floor)

    def publish_event(self, request_floor_origin, direction):
        event = Event(FLOOR_EVENT, request_floor_origin, None, direction)
        self.event_bus.publish(event)

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
            self.event_bus.publish(event)
        else:
            random_direction = random.choice(["UP", "DOWN"])
            event = Event(FLOOR_EVENT, random_floor, None, random_direction)
            self.event_bus.publish(event)

    def generate_random_events(self):

        amount = random.randint(1, 5)

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

        if direction == 1:
            direction == "UP"
        else:
            direction == "DOWN"

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
            state = elevator.get_state()
            id, curr, tar = state.to_string()
        return states

    def step():
        """Performs a step of the simulation"""

    def stop_all(self):
        self.context.stop_all()

class SystemHelper:

    @staticmethod
    def decode_update(values):
        """Gets three coma separated values"""

        elevator_id = int(values[0])
        current_floor = int(values[1])
        target_floor = int(values[2])

        return elevator_id, current_floor, target_floor

    @staticmethod
    def decode_pickup(values):
        """Gets two coma separated values"""

        floor_origin = int(values[0])
        direction = int(values[1])

        return floor_origin, direction


if __name__ == "__main__":
    """Runs the program."""

    context = ElevatorContext()

    system = ElevatorSystem(context)

    try:
        while True:
            context.generate_random_events()

            user_input = input()  # Change the variable name from 'input' to 'user_input'

            # Forward the simulation
            if user_input == "f":
                print("Forwarding...")
                executor.run_next_event()
            # See the status of the elevators
            elif user_input == "s":
                print("Getting statuses...")
                system.status()
            # Update a status of an elevator
            elif user_input == "u":
                print("Manually updating elevator's state...")
                print("Pass elevator_id,current_floor,target_floor")

                arguments = input()

                elevator_id, current_floor, destination_floor = SystemHelper.decode_update(arguments.split(","))

                system.update(elevator_id, current_floor, destination_floor)
            # Create event
            elif user_input == "e":
                print("Manually creating an event...")
                print("Pass floor_origin,direction")

                arguments = input()

                floor_origin, direction = SystemHelper.decode_pickup(arguments.split(","))

                system.pickup(floor_origin, direction)
            else:
                pass
    except KeyboardInterrupt:
        system.stop_all()
    except Exception as e:
        print(f"Exception caught: {e}")
        system.stop_all()

import random

from queue import Queue
from enum import Enum

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


class InternalDispatcher:

    def __init__(self, id):
        self.elevator_id = id

    def handle_event(self, obj: Event):
        if obj.get_event_type() == f'elevator_button_press':
            floor = obj.get_destination()
            elevator = obj.get_origin()
            print(f"The elevator {elevator} was requested to go to floor {floor}")  

    def get_id(self):
        return self.elevator_id


class ExternalDispatcher:

    def __init__(self):
        self.internal_dispatchers = []

    def set_dispatchers(self, dispatchers: list[InternalDispatcher]):
        for d in dispatchers:
            self.internal_dispatchers.append(d)
    
    def handle_event(self, obj: Event):
        if obj.get_event_type() == f'floor_button_press':
            floor = obj.get_origin()
            direction = obj.get_direction()
            print(f"ExternalDispatcher: Any elevator is called to floor {floor} was called for a destination that is {direction}")
        elif obj.get_event_type() == 'elevator_button_press':
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


if __name__ == "__main__":

    elevator_event = 'elevator_button_press'
    floor_event = 'floor_button_press'

    floors = 80
    elevators_amount = 16

    event_bus = EventBus()

    external_dispatcher = ExternalDispatcher()

    int_disp = [InternalDispatcher(n) for n in range(16)]

    external_dispatcher.set_dispatchers(int_disp)

    event_bus.subscribe(floor_event, external_dispatcher)
    event_bus.subscribe(elevator_event, external_dispatcher)

    # Number of events to generate
    num_events = 50

    # Generate and publish random events in a loop
    for _ in range(num_events):
        event = Event(elevator_event, random.randint(1, elevators_amount - 1), random.randint(0, floors), None)
        event_bus.publish(event)
        event = Event(floor_event, random.randint(1, floors), None, random.choice(["UP", "DOWN"]))
        event_bus.publish(event)

    
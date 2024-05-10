import random
import time
import threading

from queue import Queue, Empty

AMOUNT_OF_WORKERS = 3

class Worker:

    def __init__(self, id) -> None:
        self.id = id
        self.queue = Queue()
        self.is_active = True
        self.worker_thread = threading.Thread(target=self.process_jobs)
        self.worker_thread.start()

    def process_jobs(self):
        while self.is_active:
            try:
                job = self.queue.get(timeout=1) 
                print(f"Worker {self.id} processing job {job}")
                time.sleep(random.uniform(1, 2.0))
                self.queue.task_done()
            except Empty:
                continue

    def get_id(self):
        return self.id

    def add_job(self, job):
        self.queue.put(job)
        print(f"Worker {self.id} put job {job} in queue. Queue is {self.queue.queue}")

    def stop(self):
        self.is_active = False
        self.worker_thread.join() 


class Dispatcher:

    def __init__(self, amount, workers: list[Worker]) -> None:
        self.last_worker = -1
        self.num_workers = amount
        self.workers = workers

    def dispatch(self, job):
        self.last_worker = (self.last_worker + 1) % self.num_workers
        worker = self.workers[self.last_worker]
        worker.add_job(job)

    def stop(self):
        self.is_active = False
        self.worker_thread.join()

    def get_worker_by_id(self, id):
        for worker in self.workers:
            if worker.get_id() == id:
                return worker
        print(f"Worker with id {id} not found!")
        raise Exception


if __name__ == "__main__":

    workers = [Worker(id) for id in range(AMOUNT_OF_WORKERS)]

    dispatcher = Dispatcher(AMOUNT_OF_WORKERS, workers)

    try:
        while True:
            job_id = random.randint(1, 1000)
            print(f"Dispatching job {job_id}")
            dispatcher.dispatch(job_id)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopping workers...")
        for worker in workers:
            worker.stop()
        print("All workers stopped. Exiting.")

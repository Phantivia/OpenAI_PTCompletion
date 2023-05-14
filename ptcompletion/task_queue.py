import time
from datetime import datetime
from multiprocessing import Manager, Pool, Process, cpu_count, RLock
from typing import Tuple

from .task import Task


class TaskQueue:
    def __init__(self, request_per_minute: int = 60, max_rounds: int = 3, log_file: str = "tasks.log") -> None:
        self.request_per_minute = request_per_minute
        manager = Manager()
        self.token_bucket = manager.Value("i", 1)
        self.max_rounds = max_rounds
        self.log_file = log_file
        self.token_mutex = manager.Lock()
        self.log_mutex = manager.Lock()
        self.token_request_queue = manager.Queue()

    def fill_token_bucket(self, token_request_queue):
        fill_token_interval = 60 / self.request_per_minute
        while True:
            if token_request_queue.get():
                with self.token_mutex:
                    if self.token_bucket.get() < self.request_per_minute:
                        
                        self.token_bucket.set(self.token_bucket.get() + 1)
                        time.sleep(fill_token_interval)

    def fill_token_bucket_process(self):
        fill_token_process = Process(target=self.fill_token_bucket, args=(self.token_request_queue,))
        fill_token_process.daemon = True
        fill_token_process.start()

    def get_token(self):
        with self.token_mutex:
            if self.token_bucket.get() > 0:
                self.token_bucket.set(self.token_bucket.get() - 1)
                return True
            else:
                self.token_request_queue.put(True)
                return False

    def start(self, tasks: list[Task]) -> None:
        
        if not tasks:
            return
        
        self.fill_token_bucket_process()
        task_queue = tasks.copy()
        completed_tasks = []
        num_all_tasks = len(task_queue)
        
        all_start_time = time.time()

        for epoch in range(self.max_rounds):
            
            round_start_time = time.time()

            with Pool(processes=cpu_count()) as pool:
                round_tasks = []

                while task_queue:
                    if not self.get_token():  # Try to apply for token
                        time.sleep(0.01)
                        continue

                    task = task_queue.pop(0)
                    
                    round_tasks.append(pool.apply_async(self.process_task, (task, )))

                for result in round_tasks:
                    task = result.get()

                    if not task.completed:
                        task_queue.append(task)
                    if task.completed:
                        completed_tasks.append(task)

            num_remain_tasks = len(task_queue)
            self.log(f'Round {epoch+1} End in {round(time.time() - round_start_time, 3)} Seconds. {num_all_tasks - num_remain_tasks} Task Completed. {num_remain_tasks} Tasks Failed.')
            if not task_queue:
                self.log(f'All {num_all_tasks} Tasks Completed at Round {epoch+1}, in {round(time.time() - all_start_time, 3)} Seconds.')
                break
            
        return completed_tasks

    def process_task(self, task: Task) -> Tuple[Task, float]:
        start_time = time.time()
        
        self.log(f"Task {task.id} Start.")
        task.run()
        self.log(f"Task {task.id} {'Completed' if task.completed else 'Failed'} in {round(time.time() - start_time, 3)} seconds.")
        
        return task

    def log(self, msg) -> None:
        
        msg = f"[{datetime.now()}] " + msg 
        print(msg)
        
        with self.log_mutex:
            with open(self.log_file, "a") as log_file:
                log_file.write(msg + "\n")

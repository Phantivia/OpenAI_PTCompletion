import time
from datetime import datetime
from multiprocessing import Manager, Pool, Process, cpu_count, RLock
from typing import Tuple

from ptcompletion import Task


class TaskQueue:
    def __init__(self, requests_per_minute: int = 60, max_rounds: int = 3, max_requests_per_proc = 16, log_file: str = "tasks.log") -> None:
        self.requests_per_minute = requests_per_minute
        manager = Manager()
        self.quota_bucket = manager.Value("f", 1)
        self.max_rounds = max_rounds
        self.log_file = log_file
        self.token_mutex = manager.Lock()
        self.log_mutex = manager.Lock()
        self.token_request_queue = manager.Queue()
        
        self.max_requests_per_proc = max_requests_per_proc
        
        if self.requests_per_minute <= 60:
            
            self.fill_token_interval = 60 / self.requests_per_minute
            self.add = 1.0
        else:
            self.fill_token_interval = 1.0
            self.add = self.requests_per_minute / 60

    def fill_token_bucket(self, token_request_queue):
        while True:
            if token_request_queue.get():
                with self.token_mutex:
                    self.quota_bucket.set(self.quota_bucket.get() + self.add)
                    time.sleep(self.fill_token_interval)

    def fill_token_bucket_process(self):
        fill_token_process = Process(target=self.fill_token_bucket, args=(self.token_request_queue,))
        fill_token_process.daemon = True
        fill_token_process.start()

    def get_token(self):
        with self.token_mutex:
            quota = self.quota_bucket.get()
            if quota > 1.0:
                tokens = int(quota)
                self.quota_bucket.set(quota - tokens)
                return tokens
            else:
                self.token_request_queue.put(True)
                return 0

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

            with Pool(processes=cpu_count() * self.max_requests_per_proc) as pool:
                round_tasks = []

                while task_queue:
                    tokens = self.get_token()# Try to apply for token
                    if tokens == 0:  
                        time.sleep(0.01)
                    else:
                        for t in range(tokens):
                            task = task_queue.pop(0)
                            round_tasks.append(pool.apply_async(self.process_task, (task, )))
                            if not task_queue:
                                break

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
        
        msg = f"[{datetime.now()}] " + msg + "\n"
        with self.log_mutex:
            print(msg)
            with open(self.log_file, "a") as log_file:
                log_file.write(msg)

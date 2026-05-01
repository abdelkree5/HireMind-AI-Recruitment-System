import asyncio
from typing import Any, Dict
from dataclasses import dataclass, field

@dataclass
class TaskStatus:
    status: str  # "pending", "processing", "completed", "failed"
    result: Any = None
    error: str = None
    progress_messages: list[str] = field(default_factory=list)

class TaskStore:
    def __init__(self):
        self.tasks: Dict[str, TaskStatus] = {}

    def create_task(self, task_id: str):
        self.tasks[task_id] = TaskStatus(status="pending")

    def update_status(self, task_id: str, status: str):
        if task_id in self.tasks:
            self.tasks[task_id].status = status

    def set_result(self, task_id: str, result: Any):
        if task_id in self.tasks:
            self.tasks[task_id].status = "completed"
            self.tasks[task_id].result = result

    def set_error(self, task_id: str, error: str):
        if task_id in self.tasks:
            self.tasks[task_id].status = "failed"
            self.tasks[task_id].error = error
            
    def get_task(self, task_id: str) -> TaskStatus:
        return self.tasks.get(task_id)

task_store = TaskStore()

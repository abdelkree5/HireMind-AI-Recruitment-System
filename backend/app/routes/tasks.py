from fastapi import APIRouter, HTTPException
from backend.app.services.task_service import task_store

router = APIRouter()

@router.get("/{task_id}")
async def get_task_status(task_id: str):
    task = task_store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    result = {
        "task_id": task_id,
        "status": task.status,
    }
    if task.status == 'completed':
        result["result"] = task.result
    elif task.status == 'failed':
        result["error"] = task.error
    return result

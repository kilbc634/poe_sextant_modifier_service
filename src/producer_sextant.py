from consumer import my_task
from celery import Celery

# 向 Celery 发送任务
task = my_task.apply_async(args=[1])  # 发送任务到队列
print(f'Task ID: {task.id}')

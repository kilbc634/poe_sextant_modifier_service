from sextent_consumer import my_task
from celery import Celery

BROKER_URL = "redis://:cverd6632@172.17.0.1:6379/0"

# 创建一个 Celery 实例，以便与任务进行通信
app = Celery('schedule_sextent', broker=BROKER_URL)

# 向 Celery 发送任务
task = my_task.apply_async(args=[1])  # 发送任务到队列
print(f'Task ID: {task.id}')

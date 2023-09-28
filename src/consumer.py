from celery import Celery
import time
import sys 
sys.path.append("..")
from setting import BROKER_URL
import subprocess
import os

# 创建一个 Celery 实例
worker = Celery('worker', broker=BROKER_URL)

# 配置 Celery
worker.conf.task_routes = {
    'my_task': {'queue': 'my_queue'}  # 指定任务队列
}

# 定义一个简单的任务
@worker.task
def my_task(task_id):
    print(f'Starting task {task_id}')
    time.sleep(5)  # 模拟任务执行
    print(f'Completed task {task_id}')
    return f'Task {task_id} completed'

# 启动 Celery worker
if __name__ == '__main__':
    current_directory = os.path.dirname(os.path.abspath(__file__))
    command = 'celery -A "{application}" worker --loglevel=INFO'.format(
        application = os.path.basename(__file__).replace('.py', '')
    )
    process = subprocess.Popen(command, shell=True, cwd=current_directory)
    try:
        # 让Python等待，直到用户按下Ctrl+C
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        process.wait()

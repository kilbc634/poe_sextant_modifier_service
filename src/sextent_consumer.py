from celery import Celery
import time

BROKER_URL = "redis://:cverd6632@172.17.0.1:6379/0"

# 创建一个 Celery 实例
app = Celery('schedule_sextent', broker=BROKER_URL)

# 配置 Celery
app.conf.task_routes = {
    'my_task': {'queue': 'my_queue'}  # 指定任务队列
}

# 定义一个简单的任务
@app.task
def my_task(task_id):
    print(f'Starting task {task_id}')
    time.sleep(5)  # 模拟任务执行
    print(f'Completed task {task_id}')
    return f'Task {task_id} completed'

# 启动 Celery worker
if __name__ == '__main__':
    app.worker_main()

from celery import Celery
import time
import sys 
sys.path.append("..")
from setting import *
import logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__file__)
import subprocess
import os
from sextant_trade_api import search_with_stats, fetch_with_ids
import traceback
from redis_lib import push_sextant_data

# 创建一个 Celery 实例
worker = Celery('worker', broker=BROKER_URL)

# 配置 Celery
worker.conf.task_routes = {
    '*trade*': {'queue': 'trade'}  # 指定任务队列
}

@worker.task(unique=True)
def trade_sextant_task(statsList, dbKey):
    try:
        idsList = search_with_stats(statsList)

        if len(idsList) >= 10:
            idsList = idsList[0:10]
        itemsList = fetch_with_ids(idsList)

        # 取得價位資料
        priceList = []
        for item in itemsList:
            amount = item['listing']['price']['amount']
            currency = item['listing']['price']['currency']
            priceList.append({
                'amount': amount,
                'currency': currency
            })

        logger.info('got price data --> {priceList}'.format(
            priceList=str(priceList)
        ))
        
        push_sextant_data(dbKey, priceList)

        logger.info('save price data in --> {dbKey}'.format(
            dbKey=dbKey
        ))

    except Exception as e:
        logger.error('trade search ERROR')
        logger.exception(e)

    finally:
        # trade搜尋間隔30s防止超過使用頻率
        time.sleep(30)


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

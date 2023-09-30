import sys 
sys.path.append("..")
from setting import *
import redis
from datetime import datetime
import json

RedisClient = redis.Redis(host=REDIS_HOST, port=6379, password=REDIS_AUTH, decode_responses=True)

def push_sextant_data(dbKey, priceList):
    currentUtcTime = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    pushValue = json.dumps({
        'price': priceList,
        'updateTime': currentUtcTime
    })

    RedisClient.lpush(dbKey, pushValue)

def get_sextant_latest_time(dbKey):
    latestTime = ''
    resultList = RedisClient.lrange(dbKey, 0, 0)
    if resultList:
        data = json.loads(resultList[0])
        latestTime = data['updateTime']

    return latestTime

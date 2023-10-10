import sys 
sys.path.append("..")
from setting import *
import redis
from datetime import datetime
import json

RedisClient = redis.Redis(host=REDIS_HOST, port=6379, password=REDIS_AUTH, decode_responses=True)
SextantCacheKey = 'sextantCache'
CurrencyOverviewKey = 'currencyOverview'

def push_sextant_price(dbKey, priceList):
    currentUtcTime = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    pushValue = json.dumps({
        'price': priceList,
        'updateTime': currentUtcTime
    })

    RedisClient.lpush(dbKey, pushValue)

def get_sextant_price(dbKey, logCount):
    dataList = []
    resultList = RedisClient.lrange(dbKey, 0, logCount - 1)
    if resultList:
        for result in resultList:
            data = json.loads(result)
            dataList.append(data)

    return dataList

def get_sextant_latest_time(dbKey):
    latestTime = ''
    resultList = RedisClient.lrange(dbKey, 0, 0)
    if resultList:
        data = json.loads(resultList[0])
        latestTime = data['updateTime']

    return latestTime

def check_sextant_task_pending(dbKey):
    isPending = False
    cache = RedisClient.get(SextantCacheKey)
    if cache:
        cacheData = json.loads(cache)
        if dbKey in cacheData:
            isPending = True

    return isPending

def set_sextant_task_pending(dbKey, data={}):
    currentUtcTime = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    cache = RedisClient.get(SextantCacheKey)
    if cache:
        cacheData = json.loads(cache)
        if dbKey in cacheData:
            data['modifyTime'] = currentUtcTime
            cacheData[dbKey].update(data)
            RedisClient.set(SextantCacheKey, json.dumps(cacheData))
        else:
            data['modifyTime'] = currentUtcTime
            cacheData[dbKey] = data
            RedisClient.set(SextantCacheKey, json.dumps(cacheData))
        
    else:
        cacheData = {}
        data['modifyTime'] = currentUtcTime
        cacheData[dbKey] = data
        RedisClient.set(SextantCacheKey, json.dumps(cacheData))

def del_sextant_task_pending(dbKey):
    cache = RedisClient.get(SextantCacheKey)
    if cache:
        cacheData = json.loads(cache)
        cacheData.pop(dbKey, None)
        RedisClient.set(SextantCacheKey, json.dumps(cacheData))

def get_currency_overview():
    currencyData = RedisClient.get(CurrencyOverviewKey)
    if currencyData:
        currencyData = json.loads(currencyData)

    return currencyData

def update_currency_overview(data):
    currentUtcTime = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    data['modifyTime'] = currentUtcTime

    currencyData = RedisClient.get(CurrencyOverviewKey)
    if currencyData:
        currencyData = json.loads(currencyData)
        currencyData.update(data)
    else:
        currencyData = data

    RedisClient.set(CurrencyOverviewKey, json.dumps(currencyData))

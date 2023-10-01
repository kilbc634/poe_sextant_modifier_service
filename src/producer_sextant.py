from consumer import trade_sextant_task
from sextant_parser import sextant_data_to_stats_list, sextant_data_to_db_key, get_sextant_data_from_excel
from redis_lib import get_sextant_latest_time
from datetime import datetime, timedelta
import os

def run_schedule():
    # 從excel去load六分儀資料，並將資料解析成List格式
    excelFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sextant_mapping.xlsx')
    sextantData = get_sextant_data_from_excel(excelFile)
    for data in sextantData:
        # 遍歷list，產出第N筆資料對應的 statsList,dbKey
        statsList = sextant_data_to_stats_list(data)
        dbKey = sextant_data_to_db_key(data)

        # 根據dbKey到DB取得最後更新時間
        latestTime = get_sextant_latest_time(dbKey)

        doTask = False
        if latestTime:
            latestTime = datetime.strptime(latestTime, '%Y-%m-%d %H:%M:%S')
            nowTime = datetime.utcnow()
            
            # 如果當前時間和最後更新時間相差3hr以上，則安排task
            if (nowTime - latestTime) > timedelta(hours=3):
                doTask = True

        # 如果latestTime不存在(dbKey還沒有資料)，也是安排task
        else:
            doTask = True


        if doTask:
            print('Send task for -> \n' + data['sextant'])
            task = trade_sextant_task.apply_async(args=[statsList, dbKey])


if __name__ == "__main__":
    from sextant_test_data import SextantTestData
    # 使用測試資料
    for data in SextantTestData:
        statsList = sextant_data_to_stats_list(data)
        dbKey = sextant_data_to_db_key(data)
        # 向 Celery 发送任务
        task = trade_sextant_task.apply_async(args=[statsList, dbKey])
        print(f'Send Task ID: {task.id}')

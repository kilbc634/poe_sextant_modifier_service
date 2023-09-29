from consumer import trade_sextent_task
from sextant_test_data import SextantTestData
from sextant_parser import sextant_data_to_stats_list, sextant_data_to_db_key

if __name__ == "__main__":
    # 使用測試資料
    for data in SextantTestData:
        statsList = sextant_data_to_stats_list(data)
        dbKey = sextant_data_to_db_key(data)
        # 向 Celery 发送任务
        task = trade_sextent_task.apply_async(args=[statsList, dbKey])
        print(f'Send Task ID: {task.id}')

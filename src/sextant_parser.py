import json
import logging
import traceback


SEXTANT_USES_STAT_ID = 'enchant.stat_290368246'

## 將 六分儀搜尋規則 轉換成搜尋用 過濾器
def sextant_data_to_stats_list(sextantData, full=True):
    sextant = sextantData['sextant']
    keyword = sextantData['keyword']  # list for more
    stat = sextantData['stat']  # list for more
    value = sextantData['value']  # not value, or list for more

    statsList = []
    for index in range(len(keyword)):
        s = {}
        s['id'] = stat[index]
        if value:
            if value[index]:
                s['value'] = value[index]

        statsList.append(s)

    if '3 uses remaining' in sextant:
        s = {}
        s['id'] = SEXTANT_USES_STAT_ID
        if full:
            s['value'] = {
                'min': 4,
                'max': 4
            }
        else:
            s['value'] = {
                'min': 1,
                'max': 3
            }
        statsList.append(s)

    if '15 uses remaining' in sextant:
        s = {}
        s['id'] = SEXTANT_USES_STAT_ID
        if full:
            s['value'] = {
                'min': 16,
                'max': 16
            }
        else:
            s['value'] = {
                'min': 1,
                'max': 15
            }
        statsList.append(s)

    return statsList



# db key sample
# sextant:{enchant_id}&{enchant_id}={min}-{max}&uses=4-4
# sextant:{enchant_id}&{enchant_id}={min}-{max}&uses=1-3
# sextant:{enchant_id}&{enchant_id}={min}-{max}&uses=16-16
# sextant:{enchant_id}&{enchant_id}={min}-{max}&uses=1-15
# 將 六分儀搜尋規則 轉換成DB存檔key
def sextant_data_to_db_key(sextantData, full=True):
    sextant = sextantData['sextant']
    keyword = sextantData['keyword']  # list for more
    stat = sextantData['stat']  # list for more
    value = sextantData['value']  # not value, or list for more

    dbKey = 'sextant:'
    for index in range(len(keyword)):
        k = ''
        k = k + stat[index]
        if value:
            if value[index]:
                v = value[index]
                if 'min' in v and 'max' in v:
                    k = k + '={min}-{max}'.format(
                        min=str(v['min']),
                        max=str(v['max'])
                    )
                elif 'option' in v:
                    k = k + '={option}'.format(
                        option=str(v['option'])
                    )
        k = k + '&'
        dbKey = dbKey + k

    if '3 uses remaining' in sextant:
        k = ''
        if full:
            k = k + 'uses=4-4'
        else:
            k = k + 'uses=1-3'
        dbKey = dbKey + k

    if '15 uses remaining' in sextant:
        k = ''
        if full:
            k = k + 'uses=16-16'
        else:
            k = k + 'uses=1-15'
        dbKey = dbKey + k

    return dbKey


if __name__ == "__main__":
    from sextant_test_data import SextantTestData
    # 遍歷六分儀搜尋規則
    for data in SextantTestData:
        # 解析出 statsList 和 dbKey (full)
        statsList1 = sextant_data_to_stats_list(data)
        dbKey1 = sextant_data_to_db_key(data)
        # 解析出 statsList 和 dbKey (non-full)
        statsList2 = sextant_data_to_stats_list(data, full=False)
        dbKey2 = sextant_data_to_db_key(data, full=False)

        print('\n\n')
        print('[sextant] = \n' + data['sextant'])
        print('==================================================')
        print('[statsList with full] = \n' + json.dumps(statsList1, indent=4))
        print('[dbKey with full] = \n' + dbKey1)
        print('[statsList with non-full] = \n' + json.dumps(statsList2, indent=4))
        print('[dbKey with non-full] = \n' + dbKey2)

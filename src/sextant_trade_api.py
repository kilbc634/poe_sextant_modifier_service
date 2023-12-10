import requests
import json
import logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__file__)
import traceback
import time

session = requests.Session()
session.headers.update({
    'content-type': 'application/json',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
})

# statsList = [
#     {
#         "id": "enchant.stat_3844573517"
#     },
#     {
#         "id": "enchant.stat_3844573518",
#         "value": {
#             "min": 5,
#             "max": 5
#         }
#     }
# ]
def search_with_stats(statsList):
    resultList = []
    try:
        logger.info('trade search for --> {statsList}'.format(
            statsList=str(statsList)
        ))
        resp = session.post('https://www.pathofexile.com/api/trade/search/Affliction', json={
            "query": {
                "status": {
                    "option": "online"
                },
                "stats": [
                    {
                        "type": "and",
                        "filters": statsList
                    }
                ]
            },
            "sort": {
                "price": "asc"
            }
        }).json()

        if 'error' in resp:
            raise RuntimeError(resp['error']['message'])

        resultList = resp['result']

    except Exception as e:
        logger.error('trade search ERROR')
        logger.exception(e)

    finally:
        return resultList


# idsList = [
# 		"62e3c29c966b4bd18770694e5c06b8c6a99bd06537568ded7e3ce51503a6e00c",
# 		"9cb4b79d2452c5536633cd51e5b5017d7a4f4b82b41ec08281196fdf0cf6b144",
# 		"e7b9cc93f8dde895419f479add11c34cf5b5717f81b670538a9e7a8c785c783e",
# 		"20cc4ed377dca11725e4dbd5c11b278774917181a0358363e17d3d60d4bfc764",
# 		"a814d51aec94a2917ef02e0ac6e78a855f90faaf3eebba84f696bc3016ba61bd",
# 		"03398f6945fab986dc89c88edcfbdfc8cf6490dcefe58b2939eb8340a9b2bc31",
# 		"57f0b34cf03058c29144477afe7c04d781214017fcc9f37275d9597ab5af1ea3",
# 		"f4273a964535913e050873b7ef1496492ba02654b7c6d2798a87d490e00d404f",
# 		"31a9f162b47d1ba1d940fa1126f2f92d8abe40b0f86968e4556de6b85ba83f84",
# 		"b962c67c219fd6826083fc5d3412cb3ba26f10f6c32fed8adbe74b54686a190e"
# ]
def fetch_with_ids(idsList):
    resultList = []
    try:
        logger.info('trade fetch for --> {idsList}'.format(
            idsList=str(idsList)
        ))
        resp = session.get('https://www.pathofexile.com/api/trade/fetch/{fetchIds}'.format(
            fetchIds=','.join(idsList)
        )).json()

        if 'error' in resp:
            raise RuntimeError(resp['error']['message'])

        resultList = resp['result']

    except Exception as e:
        logger.error('trade fetch ERROR')
        logger.exception(e)

    finally:
        return resultList


if __name__ == "__main__":
    from sextant_test_data import SextantTestData
    from sextant_parser import sextant_data_to_stats_list
    # 遍歷六分儀搜尋規則
    for data in SextantTestData:
        # 從 搜尋規則 解析出 過濾器
        statsList = sextant_data_to_stats_list(data)

        # 使用 過濾器 進行搜尋，並取前10個結果
        idsList = search_with_stats(statsList)
        if len(idsList) >= 10:
            idsList = idsList[0:10]

        itemsList = fetch_with_ids(idsList)

        # 取得價位資料
        priceList = []
        for item in itemsList:
            amount = item['listing']['price']['amount']
            currency = item['listing']['price']['currency']
            priceList.append('{amount} {currency}'.format(amount=amount, currency=currency))
            
        print('\n\n')
        print('[sextant] = \n' + data['sextant'])
        print('==================================================')
        print('[price] = \n' + '\n'.join(priceList))
        time.sleep(3)


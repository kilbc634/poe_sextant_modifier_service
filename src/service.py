from flask import Flask, jsonify, request
from sextant_parser import get_sextant_data_from_excel, sextant_data_to_db_key
import os
import logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__file__)
import re
from redis_lib import get_sextant_price, get_currency_overview, update_currency_overview
import requests
from datetime import datetime, timedelta


def update_currency_overview_via_api():
    logger.info('Will get currency overview by ninja API')
    resp = requests.get('https://poe.ninja/api/data/currencyoverview?league=Ancestor&type=Currency')
    currencyOverview = resp.json()

    priceAsChaos = {}
    for detail in currencyOverview['currencyDetails']:
        name = detail['name']
        if 'tradeId' in detail:
            tradeId = detail['tradeId']

            for line in currencyOverview['lines']:
                if name == line['currencyTypeName']:
                    chaosValue = line['receive']['value']
                    priceAsChaos[tradeId] = chaosValue

    update_currency_overview({'priceAsChaos': priceAsChaos})
    logger.info('Updated currency overview by ninja API')

def list_currency_price_as_chaos():
    data = get_currency_overview()

    doUpdateFirst = False
    if data:
        latestTime = data['modifyTime']
        latestTime = datetime.strptime(latestTime, '%Y-%m-%d %H:%M:%S')
        nowTime = datetime.utcnow()
        
        # 如果當前時間和最後更新時間相差1hr以上，則自動更新數據
        if (nowTime - latestTime) > timedelta(hours=1):
            doUpdateFirst = True

    # 如果沒有數據
    else:
        doUpdateFirst = True

    if doUpdateFirst:
        update_currency_overview_via_api()
        data = get_currency_overview()

    priceAsChaos = data['priceAsChaos']

    return priceAsChaos


Service = Flask('Service')

# Copy Keywrod template:

# Item Class: Stackable Currency
# Rarity: Normal
# Charged Compass
# --------
# Item Level: 60
# --------
# Your Maps contain 2 additional Strongboxes (enchant)
# Strongboxes in your Maps are Corrupted (enchant)
# Strongboxes in your Maps are at least Rare (enchant)
# 4 uses remaining (enchant)
# --------
# Right click on this item then left click on a Voidstone to apply the itemised Sextant Modifier to the Voidstone.

# Item Class: Atlas Upgrade Items
# Rarity: Quest
# Grasping Voidstone
# --------
# Item Level: 83
# --------
# Your Maps contain Niko (enchant)
# 11 uses remaining (enchant)
# --------
# Maps Dropped in Areas have 25% chance to be 1 tier higher
# --------
# The Eater of Worlds consumed for countless
# eons to satiate the desperation of masters
# that could never be satisfied.
# --------
# Socket this into your Atlas to increase the Tier of all Maps.
@Service.route("/sextant/price/getByCopyText", methods=["POST"])
def sextant_price_get_by_copy_text():
    payload = request.json
    copyText = payload['copyText']  # 來自copy文字的查詢
    logCount = 1  # 預設只拿最新的1個
    if 'logCount' in payload:
        logCount = payload['logCount']
    
    # 從copy文字取出sextant詞墜的描述
    matches = re.findall(r'.*\(enchant\)\n', copyText)
    sextantText = ''.join(matches).replace(' (enchant)\n', '\n').strip()
    # 將次數的部分做調整
    # 如果該數字介於1~4之間，則將這個字串中的數字替換成"3"
    # 如果該數字介於5~16之間，則將這個字串中的數字替換成"15"
    usesNum = re.findall(r'(\d+) uses remaining', sextantText)[0]
    usesInt = int(usesNum)
    if 1 <= usesInt <= 4:
        replaceNum = '3'
    elif 5 <= usesInt <= 16:
        replaceNum = '15'
    sextantText = sextantText.replace(f'{usesNum} uses remaining', f'{replaceNum} uses remaining')

    # 讀取excel檔案，遍歷並比對出sextant詞墜描述相同的項目
    excelFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sextant_mapping.xlsx')
    sextantData = get_sextant_data_from_excel(excelFile)
    
    priceDatas = []
    print('search with -------')
    print(sextantText)
    for data in sextantData:
        if data['sextant'] == sextantText:
            # 匹配成功，取得dbKey進行查詢
            dbKey = sextant_data_to_db_key(data)
            priceDatas = get_sextant_price(dbKey, logCount)

    # 為每個price資料都加上 asChaos 欄位
    chaosPrice = list_currency_price_as_chaos()
    for d in priceDatas:
        for p in d['price']:
            amount = p['amount']
            currency = p['currency']
            asChaos = amount * chaosPrice[currency]
            p['asChaos'] = asChaos

    response = jsonify(priceDatas)

    return response


if __name__ == "__main__":
    Service.run(host='0.0.0.0', debug=True, port=16666, use_reloader=False)    

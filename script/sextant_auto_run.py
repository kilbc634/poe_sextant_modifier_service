from ahk import AHK, MsgBoxButtons
import requests
import json
import time
import os
import sys
sys.path.append("..")
from setting import *
import traceback
import logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__file__)
import re
import numpy as np
from datetime import datetime

SELL_PRICE = 4.0
SELL_PRICE_ELEVATED = 30.0
SELL_CASE_NOTHING = 0
SELL_CASE_NORMAL = 1
SELL_CASE_ELEVATED = 2
SELL_CASE_ELEVATED_OTHER = 3
Ahk = AHK(executable_path=AHK_EXE)

# 從當前路徑的json檔去load座標設定值資料，如果不存在會初始化一個新的
Pos = {}
JsonFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'position.json')
if os.path.exists(JsonFile):
    with open(JsonFile, 'r', encoding='utf-8') as file:
        Pos = json.load(file)
    logger.info('Loaded settings success')
else:
    with open(JsonFile, 'w') as file:
        json.dump(Pos, file)
    logger.info('Not found setting, init setting file')

PosList = ['sextant', 'voidstone', 'stash', 'compass', 'selltab', 'othertab', 'inventory', 'maintab']

def check_window_active():
    isActive = False
    win = Ahk.active_window
    if win.title == 'Path of Exile':
        isActive = True

    return isActive

def check_position_ready():
    isReady = True
    for index in range(len(PosList)):
        if PosList[index] not in Pos:
            isReady = False
            break

    return isReady

def update_position(positionName, positionXY):
    global Pos
    Pos[positionName] = positionXY
    with open(JsonFile, 'w') as file:
        json.dump(Pos, file)
    
    logger.info(f'Set position [ {positionName} ] is {str(positionXY)}')

def reset_all_position():
    global Pos
    Pos = {}
    with open(JsonFile, 'w') as file:
        json.dump(Pos, file)

def copy_item_to_text():
    itemText = ''
    clipboardText = Ahk.get_clipboard()
    
    Ahk.set_clipboard('')
    Ahk.send('^c')
    time.sleep(0.1)
    Ahk.send('^c')
    time.sleep(0.1)

    itemText = Ahk.get_clipboard()
    Ahk.set_clipboard(clipboardText)

    return itemText

def get_sextant_stack_size(itemText):
    stackSize = None
    pattern = r"Item Class: Stackable Currency\r\nRarity: Currency\r\n(?:Awakened|Elevated) Sextant\r\n(?:.*\r\n)*?Stack Size: (\d+)/\d+"
    match = re.search(pattern, itemText)
    stackSize = int(match.group(1))

    return stackSize

def get_compass_stack_size(itemText):
    stackSize = None
    pattern = r"Item Class: Stackable Currency\r\nRarity: Currency\r\nSurveyor's Compass\r\n(?:.*\r\n)*?Stack Size: (\d+)/\d+"
    match = re.search(pattern, itemText)
    stackSize = int(match.group(1))

    return stackSize

def clip_sextant_quick_name(itemText):
    itemText = itemText.replace('\r\n', '\n')
    match = re.findall(r'.*\(enchant\)\n', itemText)
    firstEnchantLine = match[0]
    quickName = firstEnchantLine.replace(' (enchant)\n', '').strip()
    
    return quickName

def check_pricing_sell_case(itemText):
    sellData = dict()
    sellData['sellCase'] = SELL_CASE_NOTHING
    sellData['sellPrice'] = None

    logger.info('will check price for -->\n' + itemText)
    resp = requests.post(SERVICE_HOST + 'sextant/price/getByCopyText',
        json = {
            'copyText': itemText,
            'logCount': 1
        }
    ).json()

    if len(resp) >= 1:
        priceList = resp[0]['price']

        # 遍歷 priceList 的 asChaos 欄位，計算 avg
        numberList = []
        for price in priceList:
            numberList.append(price['asChaos'])
        logger.info('get price -->\n' + str(numberList))

        # 先過濾掉極值，排除掉2倍標準差之外值
        median = np.median(numberList)
        std = np.std(numberList)
        threshold = 2
        filteredList = [x for x in numberList if abs(x - median) <= threshold * std]
        logger.info('filteredList -->\n' + str(filteredList))

        # 取價位平均值
        avgPrice = np.mean(filteredList)
        logger.info(f'avg price --> {str(avgPrice)}')

        # 價位大於特定數字才進行擺賣，如果是高尚六分儀則無條件擺賣
        if '15 uses remaining' in itemText or '16 uses remaining' in itemText:
            if avgPrice >= SELL_PRICE_ELEVATED:
                sellData['sellCase'] = SELL_CASE_ELEVATED
            else:
                sellData['sellCase'] = SELL_CASE_ELEVATED_OTHER
            logger.info('must sell it if Elevated')
        elif avgPrice >= SELL_PRICE:
            sellData['sellCase'] = SELL_CASE_NORMAL
            logger.info('price is good, you can sell it')

        sellData['sellPrice'] = avgPrice

    else:
        logger.warning('Check sextant price is Non-Data, skip it')

    return sellData

def ctrl_click():
    Ahk.key_down('Ctrl')
    time.sleep(0.2)
    Ahk.click()
    time.sleep(0.1)
    Ahk.key_up('Ctrl')

StopSignal = False
def check_stop_signal():
    global StopSignal
    if StopSignal == True:
        StopSignal = False
        raise RuntimeError('Check the STOP signal, will stop script')


# bind with F11
def end_auto_run():
    global StopSignal
    StopSignal = True

# bind with F9
def position_setting():
    if check_window_active() == False:
        return

    x, y = Ahk.get_mouse_position(coord_mode='Screen')
    currentPosition = {
        'x': x,
        'y': y
    }

    positionListHint = ''
    for index in range(len(PosList)):
        existedIcon = ''
        if PosList[index] in Pos:
            existedIcon = ' [v]'
        positionListHint = positionListHint + '{id}: {name}\n'.format(
            id=str(index),
            name=PosList[index] + existedIcon
        )
    positionListHint = positionListHint + '{id}: {name}'.format(
        id=str(len(PosList)),
        name='reset all'
    )

    positionId = Ahk.input_box(
        prompt=f'What is this position? (please input ID number)\n\n{positionListHint}',
        title='Position Setting',
        default='0',
        height=300
    )
    positionName = ''
    try:
        if positionId:
            positionId = int(positionId)
            if positionId == len(PosList):
                reset_all_position()
            else:
                positionName = PosList[positionId]
    except Exception as e:
        traceback.print_exc()
        Ahk.msg_box(
            text='Invalid ID',
            title='Error'
        )

    if positionName:
        update_position(positionName, currentPosition)


# bind with F10
def start_auto_run():
    if StopSignal == True:
        return
    if check_window_active() == False:
        return
    if check_position_ready() == False:
        Ahk.msg_box(
            text='Position setting not completed\nPress [F9] to set it',
            title='Error'
        )
        return

    # 建立一個report，用來存放有價物品list
    sellList = {}
    totalPrice = 0

    currentTime = datetime.now().strftime('%Y%m%d-%H%M%S')
    fileName = f'sextent_{currentTime}.txt'
    reportFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), fileName)
    with open(reportFile, 'w') as file:
        file.write('Sextant Store Sell List\n-------------------------------------')

    Ahk.show_info_traytip(
        title='Sextant Auto Run',
        text='will start auto run after 3 sec'
    )
    time.sleep(3)
    logger.info('Start auto run')

    while True:
        try:
            # (停留在通貨頁)
            check_stop_signal()
            # 1. 移動到 ${位置.六分儀}，確認六分儀剩餘數量
            Ahk.mouse_move(x = Pos['sextant']['x'], y = Pos['sextant']['y'], speed=10)
            sextantText = copy_item_to_text()
            sextantCount = get_sextant_stack_size(sextantText)
            if sextantCount < 3:
                raise RuntimeError('sextant count less than 10')
            # 2. 右鍵
            check_stop_signal()
            Ahk.click(button='R')
            time.sleep(0.3)
            # 3. 按G
            Ahk.send('g')
            time.sleep(0.5)
            # 4. 移動到 ${位置.守望石}
            Ahk.mouse_move(x = Pos['voidstone']['x'], y = Pos['voidstone']['y'], speed=10)
            # 5. 左鍵
            check_stop_signal()
            Ahk.click()
            time.sleep(0.5)
            # 6. 查價func -> ${有價 / 無價}
            voidstoneText = copy_item_to_text()
            sellData = check_pricing_sell_case(voidstoneText)
            time.sleep(2)
            # 7. 按ESC
            Ahk.key_press('Escape')
            time.sleep(0.5)
            # 8. 移動到 ${位置.倉庫}
            Ahk.mouse_move(x = Pos['stash']['x'], y = Pos['stash']['y'], speed=10)
            # 9. 左鍵
            check_stop_signal()
            Ahk.click()
            time.sleep(1)
            # ( 無價，則在這裡結束 )
            # 10.  if 有價，則追加以下步驟
            if sellData['sellCase'] != SELL_CASE_NOTHING:
                # 11. 移動到 ${位置.羅盤}，確認羅盤剩餘數量
                Ahk.mouse_move(x = Pos['compass']['x'], y = Pos['compass']['y'], speed=10)
                compassText = copy_item_to_text()
                compassCount = get_compass_stack_size(compassText)
                if compassCount < 3:
                    raise RuntimeError('compass count less than 10')
                # 12. 右鍵
                check_stop_signal()
                Ahk.click(button='R')
                time.sleep(0.3)
                # 13. 按G
                Ahk.send('g')
                time.sleep(0.5)
                # 14. 移動到 ${位置.守望石}
                Ahk.mouse_move(x = Pos['voidstone']['x'], y = Pos['voidstone']['y'], speed=10)
                # 15. 左鍵
                check_stop_signal()
                Ahk.click()
                time.sleep(1)
                # 16. 按ESC
                Ahk.key_press('Escape')
                time.sleep(0.5)
                # 17. 移動到 ${位置.倉庫}
                Ahk.mouse_move(x = Pos['stash']['x'], y = Pos['stash']['y'], speed=10)
                # 18. 左鍵
                check_stop_signal()
                Ahk.click()
                time.sleep(1)
                if sellData['sellCase'] == SELL_CASE_NORMAL or sellData['sellCase'] == SELL_CASE_ELEVATED:
                    # 19-1. 移動到 ${位置.SELL頁籤}
                    Ahk.mouse_move(x = Pos['selltab']['x'], y = Pos['selltab']['y'], speed=10)
                    # 20. 左鍵
                    check_stop_signal()
                    Ahk.click()
                    time.sleep(1)
                elif sellData['sellCase'] == SELL_CASE_ELEVATED_OTHER:
                    # 19-2. 移動到 ${位置.OTHER頁籤}
                    Ahk.mouse_move(x = Pos['othertab']['x'], y = Pos['othertab']['y'], speed=10)
                    # 20. 左鍵
                    check_stop_signal()
                    Ahk.click()
                    time.sleep(1)
                # 21. 移動到 ${位置.背包}
                Ahk.mouse_move(x = Pos['inventory']['x'], y = Pos['inventory']['y'], speed=10)
                # 22. 左鍵
                check_stop_signal()
                Ahk.click()
                time.sleep(0.5)
                # 23. 按Ctrl+左鍵，確認當前位置沒有物品
                check_stop_signal()
                ctrl_click()
                time.sleep(1)
                inventoryText = copy_item_to_text()
                if inventoryText:
                    raise RuntimeError('inventory item not clear')
                # 24. 移動到 ${位置.MAIN頁籤}
                Ahk.mouse_move(x = Pos['maintab']['x'], y = Pos['maintab']['y'], speed=10)
                # 25. 左鍵
                check_stop_signal()
                Ahk.click()
                time.sleep(1)
                # ( 追加步驟結束 )
                logger.info('save compass in store')

                # 將有價物統計進report
                quickName = clip_sextant_quick_name(voidstoneText)
                if quickName in sellList:
                    sellList[quickName] = sellList[quickName] + 1
                else:
                    sellList[quickName] = 1

                totalPrice = totalPrice + sellData['sellPrice']

        except Exception as e:
            traceback.print_exc()
            break

    # 將report寫入檔案
    reportText = '\n'
    for key in sellList.keys():
        lineText = '{name} - {count}\n'.format(
            name=key,
            count=str(sellList[key])
        )
        reportText = reportText + lineText

    totalMsg = '\nTotal Price : {totalPrice} chaos'.format(totalPrice=str(totalPrice))
    reportText = reportText + totalMsg

    with open(reportFile, 'a') as file:
        file.write(reportText)

    Ahk.msg_box(
        text=reportText,
        title='Auto run stop'
    )

SellItemNote = ''
# bind with "[" key
def sell_item_sampling():
    global SellItemNote
    compassText = copy_item_to_text()
    pattern = r"Item Class: Stackable Currency\r\nRarity: Normal\r\nCharged Compass\r\n(?:.*\r\n)*?Note: (.*)"
    match = re.search(pattern, compassText)
    if match:
        SellItemNote = match.group(1)

# bind with "]" key
def sell_item_same():
    # compassText = copy_item_to_text()
    # if 'Note: ' in compassText:
    #     return

    Ahk.click(button='R')
    time.sleep(0.2)

    clipboardText = Ahk.get_clipboard()

    Ahk.set_clipboard(SellItemNote)
    Ahk.send('^v')
    time.sleep(0.2)
    Ahk.key_press('Enter')

    Ahk.set_clipboard(clipboardText)


Ahk.add_hotkey('F9', callback=position_setting)
Ahk.add_hotkey('F10', callback=start_auto_run)
Ahk.add_hotkey('F11', callback=end_auto_run)
Ahk.add_hotkey('[', callback=sell_item_sampling)
Ahk.add_hotkey(']', callback=sell_item_same)


if __name__ == "__main__":
    Ahk.start_hotkeys()
    Ahk.show_info_traytip(
        title='Sextant Auto Run',
        text='script is ready'
    )
    logger.info('Script is ready')
    Ahk.block_forever()

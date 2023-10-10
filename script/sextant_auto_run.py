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


Ahk = AHK(executable_path=AHK_EXE)

# 從當前路徑的json檔去load座標設定值資料，如果不存在會初始化一個新的
Pos = {}
JsonFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'position.json')
if os.path.exists(JsonFile):
    with open(JsonFile, 'r', encoding='utf-8') as file:
        Pos = json.load(file)
else:
    with open(JsonFile, 'w') as file:
        json.dump(Pos, file)

PosList = ['sextant', 'voidstone', 'stash', 'compass', 'selltab', 'inventory', 'maintab']
# 位置.六分儀
# Pos['sextant']['x']
# Pos['sextant']['y']

# 位置.守望石
# Pos['voidstone']['x']
# Pos['voidstone']['y']

# 位置.倉庫
# Pos['stash']['x']
# Pos['stash']['y']

# 位置.羅盤
# Pos['compass']['x']
# Pos['compass']['y']

# 位置.SELL頁籤
# Pos['selltab']['x']
# Pos['selltab']['y']

# 位置.背包
# Pos['inventory']['x']
# Pos['inventory']['y']

# 位置.MAIN頁籤
# Pos['maintab']['x']
# Pos['maintab']['y']

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
    Ahk.send('^c')
    Ahk.send('^c')

    itemText = Ahk.get_clipboard()
    Ahk.set_clipboard(clipboardText)

    return itemText

def get_sextant_stack_size(itemText):
    stackSize = None
    pattern = r"Item Class: Stackable Currency\r\nRarity: Currency\r\nAwakened Sextant\r\n(?:.*\r\n)*?Stack Size: (\d+)/\d+"
    match = re.search(pattern, itemText)
    stackSize = int(match.group(1))

    return stackSize

def get_compass_stack_size(itemText):
    stackSize = None
    pattern = r"Item Class: Stackable Currency\r\nRarity: Currency\r\nSurveyor's Compass\r\n(?:.*\r\n)*?Stack Size: (\d+)/\d+"
    match = re.search(pattern, itemText)
    stackSize = int(match.group(1))

    return stackSize

def check_price_if_sell(itemText):
    ifSell = False

    resp = requests.post(SERVICE_HOST + 'sextant/price/getByCopyText',
        json = {
            'copyText': itemText.replace('\r\n', '\n'),
            'logCount': 1
        }
    )
    priceList = resp.json()[0]['price']
    # 遍歷 priceList 的 asChaos 欄位，計算 avg

    # 價位大於特定數字才進行擺賣
    # if avgPrice >= 6:
    #     ifSell = True

    return ifSell



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
        Ahk.msg_box(
            text='Invalid ID',
            title='Error'
        )
        traceback.print_exc()

    if positionName:
        update_position(positionName, currentPosition)


# bind with F10
def start_auto_run():
    if check_window_active() == False:
        return
    if check_position_ready() == False:
        Ahk.msg_box(
            text='Position setting not completed\nPress [F9] to set it',
            title='Error'
        )
        return

    # (停留在通貨頁)
    # 1. 移動到 ${位置.六分儀}，確認六分儀剩餘數量
    Ahk.mouse_move(x = Pos['sextant']['x'], y = Pos['sextant']['y'], speed=10)
    sextantText = copy_item_to_text()
    sextantCount = get_sextant_stack_size(sextantText)
    # 2. 右鍵
    Ahk.click(button='R')
    time.sleep(0.3)
    # 3. 按G
    Ahk.send('g')
    time.sleep(0.5)
    # 4. 移動到 ${位置.守望石}
    Ahk.mouse_move(x = Pos['voidstone']['x'], y = Pos['voidstone']['y'], speed=10)
    # 5. 左鍵
    Ahk.click()
    time.sleep(0.5)
    # 6. 查價func -> ${有價 / 無價}
    voidstoneText = copy_item_to_text()
    doSell = check_price_if_sell(voidstoneText)
    # 7. 按ESC
    Ahk.send('Esc')
    time.sleep(0.5)
    # 8. 移動到 ${位置.倉庫}
    Ahk.mouse_move(x = Pos['stash']['x'], y = Pos['stash']['y'], speed=10)
    # 9. 左鍵
    Ahk.click()
    time.sleep(1)
    # ( 無價，則在這裡結束 )
    # 10.  if 有價，則追加以下步驟
    if doSell:
        # 11. 移動到 ${位置.羅盤}，確認羅盤剩餘數量
        Ahk.mouse_move(x = Pos['compass']['x'], y = Pos['compass']['y'], speed=10)
        compassText = copy_item_to_text()
        compassCount = get_compass_stack_size(compassText)
        # 12. 右鍵
        Ahk.click(button='R')
        time.sleep(0.3)
        # 13. 按G
        Ahk.send('g')
        time.sleep(0.5)
        # 14. 移動到 ${位置.守望石}
        Ahk.mouse_move(x = Pos['voidstone']['x'], y = Pos['voidstone']['y'], speed=10)
        # 15. 左鍵
        Ahk.click()
        time.sleep(1)
        # 16. 按ESC
        Ahk.send('Esc')
        time.sleep(0.5)
        # 17. 移動到 ${位置.倉庫}
        Ahk.mouse_move(x = Pos['stash']['x'], y = Pos['stash']['y'], speed=10)
        # 18. 左鍵
        Ahk.click()
        time.sleep(1)
        # 19. 移動到 ${位置.SELL頁籤}
        Ahk.mouse_move(x = Pos['selltab']['x'], y = Pos['selltab']['y'], speed=10)
        # 20. 左鍵
        Ahk.click()
        time.sleep(2)
        # 21. 移動到 ${位置.背包}
        Ahk.mouse_move(x = Pos['inventory']['x'], y = Pos['inventory']['y'], speed=10)
        # 22. 左鍵
        Ahk.click()
        time.sleep(0.5)
        # 23. 按Ctrl+左鍵，確認當前位置沒有物品
        Ahk.send('^Lbutton')
        time.sleep(0.2)
        Ahk.send('^Lbutton')
        time.sleep(1)
        inventoryText = copy_item_to_text()
        if inventoryText:
            raise RuntimeError('inventory item not clear')
        # 24. 移動到 ${位置.MAIN頁籤}
        Ahk.mouse_move(x = Pos['maintab']['x'], y = Pos['maintab']['y'], speed=10)
        # 25. 左鍵
        Ahk.click()
        time.sleep(1)
        # ( 追加步驟結束 )


Ahk.add_hotkey('F9', callback=position_setting)
Ahk.add_hotkey('F10', callback=start_auto_run)


if __name__ == "__main__":
    Ahk.start_hotkeys()
    Ahk.show_info_traytip(
        title='Sextant Auto Run',
        text='script is ready'
    )
    Ahk.block_forever()

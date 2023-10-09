from ahk import AHK, MsgBoxButtons
import requests
import json
import time
import os
import sys
sys.path.append("..")
from setting import *
import traceback

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


# bind with F9
def position_setting():
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
    pass

Ahk.add_hotkey('F9', callback=position_setting)
Ahk.add_hotkey('F10', callback=start_auto_run)


if __name__ == "__main__":
    Ahk.start_hotkeys()
    Ahk.show_info_traytip(
        title='Sextant Auto Run',
        text='script is ready'
    )
    Ahk.block_forever()

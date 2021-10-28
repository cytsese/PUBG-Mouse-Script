

from pynput.mouse import Button, Controller,Listener
from pynput import keyboard
import time
import json
import os
import psutil
from multiprocessing import Process
from multiprocessing.managers import BaseManager
from threading import Thread

class Multipro_manager(BaseManager): 
    pass

class Cfg:
    path = './cfg.json'
    data = {}
    def load():
        if os.path.exists(Cfg.path):
            Cfg.data = json.load(open(Cfg.path,'r',encoding='utf-8'))
        else:
            with open(Cfg.path,'w',encoding='utf-8') as f:
                json.dump(Cfg.data,f)
        return Cfg.data
    def save(data):
        with open(Cfg.path,'w',encoding='utf-8') as f:
            json.dump(data,f,indent='    ')
   
class State:
    """
    监听键盘和鼠标事件来控制状态标识符，所有的标识符包含在self.data字典中，
    根据鼠标和键盘事件驱动来改变标识（切换配置方案），其目的在于动态变更鼠标移动距离[dy]和间隔时间[dt]
    自动变更遵循以下原则：
    鼠标移动距离[dy]取决于后坐力大小
    间隔时间[dt]取决于武器射速，公式未知
    """    
    def __init__(self):
        self.data = {
                'used' : True, #开启使用,由self.detect_game()判断决定
                'aimed' : False, #判断瞄准
                'fire' : False, #正在开火
                'plan' : 'plan1'
            }
        self.key_press_list = set() #以按键释放为信号 记录组合键
        def cfg_load():
            plan = self.cfg['plans'][self.data['plan']]
            self.data['dy'] = plan['dy'] # 压枪幅度
            self.data['dt'] = plan['dt'] # 时间间隔
            self.data['gun'] = plan['gun'] # 武器
            self.data['mirror'] = plan['mirror'] # 瞄准镜
        def on_key_press(key):
            self.key_press_list.add(str(key))
        def on_key_release(key):
            k = self.key_press_list
            self.data['plan'] = ['plan1','plan2','plan3'][[k == {'Key.ctrl_l','<49>'},k == {'Key.ctrl_l','<50>'},k == {'Key.ctrl_l','<50>'}].index(True)]
            
            print(self.key_press_list)
            self.key_press_list.clear()
            cfg_load()

        def on_click(x, y, button, pressed):
            self.data['aimed'] = [self.data['aimed'],not self.data['aimed']][(button == Button.right) and pressed]
            self.data['fire'] = [False,True][(button == Button.left) and pressed]
            # s = ['','\nfiring...'][self.fire]
            # s = f'fire:{self.fire}  amied:{self.aimed} {s}'
            # print(s)
        def detect_game():
            """
            每隔10s检测一次游戏是否在运行，以此改变data['used']的状态
            与鼠标键盘的监听线程一样，现场启动后不管
            """            
            def search():
                pids = psutil.pids()
                for pid in pids:
                    if 'PUBG' in psutil.Process(pid).name():return pid
            while 1:
                self.data['used'] = search()
                print('game state：not run')
                time.sleep(10)
        self.cfg = Cfg.load()
        cfg_load()
        listener = Listener(on_click=on_click)
        listener.start()
        listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
        listener.start()
        listener = Thread(target=detect_game)
        listener.start()
    def getdata(self):
        return self.data



        



class Manager:
    def __init__(self) -> None:
        Multipro_manager.register('State',State)
        multipro_manager = Multipro_manager()
        multipro_manager.start()
        self.state = multipro_manager.State()  #注册共享实列
    def down_fire(self):
        """
        压枪核心，在一个单独的进程中运行
        为精确控制频率和延迟，不建议插入更多代码
        """
        mouse = Controller()
        while 1:
            data = self.state.getdata() #约需要0.0005s
            if data['used'] and data['fire']:
                mouse.move(0, data['dy'])
                time.sleep(data['dt'])
            time.sleep(0.0005) #占用下降90%

if __name__ =="__main__":
    m = Manager()
    p = Process(target=m.down_fire)
    p.start()
    time.sleep(30)






        

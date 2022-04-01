import os
import pickle
import keyboard
from collections import OrderedDict


def clear_screen(func):
    # subprocess.run("clear", shell=True, stdout=subprocess.PIPE)
    def wrapper(*args,**kwargs):
        os.system('cls' if os.name == 'nt' else "printf '\033c'")
        return func(*args,**kwargs)
    return wrapper

class movingAgent(object):
    key_bind = {
        'w':'w',
        's':'s',
        'a':'a',
        'd':'d',
        'jump':'f',
        'crouch':'x',
        'dash':'space',
        'walk':'left alt',
        'camera_up':'o',
        'camera_down':'p',
        'camera_left':'k',
        'camera_right':'l',
        'camera_lockon':'i',
        'up':'up',
        'down':'down',
        'left':'left',
        'right': 'right',
        'w_attack':'q',
        's_attack':'n',
        'guard':'b',
        'skill':'m',
        'item':'r',
        'event':'e',
        'confirm': 'enter'
    }


    def __init__(self):
        self.bind_key = {k: v for k, v in self.key_bind.items()}
        self.key_bind = {k: keyboard.key_to_scan_codes(v) for k, v in self.key_bind.items()}
        self.speed_factor = 1.3
        self.all_block = False
        self.recording_running = False

    def __getattr__(self,item):
        key = self.key_bind.get(item)
        if key is None:
            raise AttributeError
        return key
    @staticmethod
    def make_key(key, last_key=None, key_time_after=1, key_interval=0.5):
        if type(key) is str:
            scan = keyboard.key_to_scan_codes(key)
            qdown = keyboard.KeyboardEvent('down', scan, key)
            qup = keyboard.KeyboardEvent('up', scan, key)
        else:
            scan = key
            qdown = keyboard.KeyboardEvent('down', scan, 'key')
            qup = keyboard.KeyboardEvent('up', scan, 'key')
        qup.time += key_interval
        if last_key is not None:
            qdown.time += last_key.time
            qup.time += last_key.time
        return qdown, qup

    @staticmethod
    def time_check(new_move):
        for i in range(1, len(new_move)):
            a = new_move[i].time - new_move[i - 1].time
            print(
                f"{new_move[i]}:{i}th - {new_move[i - 1]}:{i - 1}th \n{a}, {new_move[i].time} - {new_move[i - 1].time}")

    def keypress(self,key,key_interval=0.3,quantity=1,key_time_after=0.3,force=False):
        if quantity ==1:
            key = self.make_key(key, key_interval=key_interval)
        else:
            key = list(self.make_key(key, key_interval=key_interval))
            for i in range(1,quantity):
                key.extend(self.make_key(key,last_key=key[-1],key_time_after=key_time_after,key_interval=key_interval))
        key = self.clean_keys(key)
        #self.time_check(key)
        if ((not self.all_block) and (not self.recording_running)) or force:
            keyboard.play(key, speed_factor=self.speed_factor)

    @staticmethod
    def clean_keys(key):
        key = [i for i in key if i.name != 'key']
        return key


class recordAgent(movingAgent):
    record_key = {'record': '7',
                  'record_stop': 'esc',
                  'play_record': '5',
                  'delete_record': '2',
                  'switch_next_record': '6',
                  'switch_before_record': '4',
                  'speed_faster': '3',
                  'speed_slower': '1',
                  'record_info_print':'shift',
                  'input_block/release':'home',
                  'set_focus':'insert',
                  'key_bind_edit':"pgup"
                  }
    def __init__(self,parent,recording=True):
        movingAgent.__init__(self)
        self.recorded = OrderedDict()
        self.parent = parent
        self.__record_idx = 0
        record_key = {k: keyboard.key_to_scan_codes(v) for k, v in self.record_key.items()}
        self.key_bind.update(record_key)
        self.record_key =  {k:str(v) for k,v in self.record_key.items()}
        self.key_record = {str(v):k for k,v in self.record_key.items()}
        self.one_press_signal_count = 0
        self.__press_count = 0
        self.__b_pressed = 'enter'
        self.__n_pressed = ''
        self.recording_running = False
        self.all_block = True
        self.load_record()
        if recording:
            print("Please press enter after type 5")
            while True:
                key = keyboard.read_key()
                if key == '5':
                    self.one_press_signal_count += 1
                if key == 'enter':
                    break
        else:
            self.one_press_signal_count = 2

    def key_binding_edit(self):
        key = keyboard.read_key()
        if self.real_count(key):
            pass
        else:
            print("wrong key selectd")
            return
        print(f"Selected key for edit : {key}\n confirm to press {self.key_bind_edit}")
        confirm = keyboard.read_key()
        self.record_key.values()
        if confirm ==self.key_bind_edit:
            newly_edit = keyboard.read_key()

            print(f"Selected key for edit : {key}, change {key} to {newly_edit}")
            record = self.key_record[key]
            self.record_key[record] = newly_edit
            self.key_record[newly_edit] = record
            del self.key_record[key]

    def real_count(self,key):
        self.__n_pressed = key
        if self.__press_count == 0:
            self.__press_count += 1
            self.__b_pressed = key
            return True
        else:
            if self.__b_pressed == self.__n_pressed:
                self.__press_count += 1
                if self.__press_count <= self.one_press_signal_count:
                    return False
                else:
                    self.__press_count = 1
                    return True
            else:
                self.__press_count = 1
                self.__b_pressed = key
                return True

    @property
    def record_num(self):
        return len(self.recorded)
    def run(self):
        self.record_info()
        while True:
            key = keyboard.read_key()
            if not self.real_count(key):
                continue
            if key == self.key_bind_edit:
                self.key_binding_edit()
            if key == self.record_key.get('input_block/release'):
                if self.all_block:
                    self.all_block = False
                    print("All key is released!!")
                else:
                    self.all_block = True
                    print("All key is blocked!!")
            if key == self.set_focus:  #insert
                self.parent.debug_send()
            if key == self.record_info_print:
                self.record_info()
            if key == self.record:
                self.recording()
                self.record_info()
            if key == self.play_record:
                self.play()
                self.record_info()
            if key == self.record_stop:
                os.system('cls' if os.name == 'nt' else "printf '\033c'")
            if key == self.delete_record:
                self.deleting_record()
                if self.record_num >=1:
                    print(f"Delete {self.__record_idx}th record\n",self.recorded[self.__record_idx],'\n')
                    del self.recorded[self.__record_idx]
                    if self.record_num:
                        self.__record_idx = min(self.recorded)
                    else:
                        self.__record_idx = 0
                else:
                    print("No record for delete")
                self.record_info()
            if key == self.switch_next_record:
                self.get_record(1)
            if key == self.switch_before_record:
                self.get_record(-1)
            if key == self.speed_faster:
                self.speed_factor += 0.05
                print(f"Speed factor increase to %.2f" %self.speed_factor)
            if key == self.speed_slower:
                self.speed_factor -= 0.05
                print("Speed factor decrease to %.2f" %self.speed_factor)

    def recording(self):
        if not self.all_block:
            print(f"Please press {self.record_key['input_block/release']} key to block all key before recording.")
            return
        print("Recording Start!!!!!!!!!!!")
        record = self.clean_record(keyboard.record(until=self.record_stop))
        if len(self.recorded):
            self.__record_idx = max(self.recorded)+1
        else:
            self.__record_idx = 1
        self.recorded[self.__record_idx] = record
        with open(f'records/{self.__record_idx}.p', 'wb') as f:
            pickle.dump(record, f)


    def clean_record(self,record):
        st_id = 1 if (record[0].name == self.record) & (record[0].event_type == 'up') else 0
        ed_id = -1 if (record[-1].name == self.record_stop) & (record[-1].event_type == 'down') else len(record)+1
        return record[st_id:ed_id]

    def play(self):
        self.recording_running = True
        if not self.all_block and self.__record_idx in self.recorded:
            print(f"play the {self.__record_idx}th record!!!!!")
            keyboard.play(self.recorded[self.__record_idx], speed_factor=self.speed_factor)
            print(f"record {self.__record_idx}th complete")
        self.recording_running = False


    @clear_screen
    def record_info(self):
        len("-------"*8+"RECORD INFO"+"-------"*8)
        print("-------"*8+f"RECORD INFO"+"-------"*8)
        print(f"# {self.record_num} , SELECTED : {self.__record_idx}th".center(123))
        for n in sorted(self.recorded):
            print(n, "th record \n", self.recorded[n], '\n')
        print(self.record_key)
        print("-"*123)


    def get_record(self,num):
        sorted_key =sorted(self.recorded)
        if not len(sorted_key):
            return
        origin_idx = sorted_key.index(self.__record_idx)
        origin_idx += num
        if origin_idx >= 0:
            self.__record_idx = sorted_key[origin_idx  if origin_idx < self.record_num else 0]
        else:
            self.__record_idx = sorted_key[-1]
        if self.record_num >= 1:
            print(f"Selected record : {self.__record_idx}th\n",self.recorded[self.__record_idx],'\n')

    def deleting_record(self):
        if not os.path.exists('records'):
            os.mkdir('records')
        if (os.path.exists(f'records/{self.__record_idx}.p')) and not self.all_block:
            os.remove(f'records/{self.__record_idx}.p')

    def load_record(self):
        if not os.path.exists('records'):
            os.mkdir('records')
        for file_name in os.listdir('records'):
            if '.p' in file_name:
                with open(f'records/{file_name}', 'rb') as f:
                    self.recorded[int(file_name.split(".")[0])] = pickle.load(f)
                self.__record_idx =int(file_name.split(".")[0])



    def __getattr__(self,item):
        key = self.record_key.get(item)
        if key is not None:
            return key
        key = self.key_bind.get(item)
        if key is None:
            raise AttributeError
        return key


if __name__ == "__main__":
    ma = recordAgent()
    ma.run()


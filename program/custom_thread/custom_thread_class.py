from threading import Thread
from time import sleep
from .waiting_obj_class import WaitingObject

class CustomThread(Thread):
    def __init__(self, get_results):
        super(CustomThread, self).__init__()
        self.value = None
        self.value_set = False
        self.get_results = get_results
        self.waiting_obj = WaitingObject()
        self.waiting_thread = Thread(target=self.waiting_msg, args=(self.waiting_obj, self))
        self.waiting_thread.setDaemon(True)
        self.waiting_thread.start()
    
    def run(self):
        self.value = self.get_results()
        self.value_set = True
        self.waiting_thread.join()
    
    @staticmethod
    def waiting_msg(waiting_obj, original_object):
        printed_waiting_msg = False
        while original_object.value_set is False:
            if waiting_obj.waiting:
                printed_waiting_msg = True
                print(".", end="")
                sleep(1)
        if printed_waiting_msg:
            print()  # give newline to line above if printed
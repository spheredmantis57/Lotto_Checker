import datetime
import requests
import sys
from time import sleep
from datetime import datetime, timedelta

from simple_term_menu import TerminalMenu

from custom_thread import CustomThread

MIN = 1
MM_PRIM_MAX = 70
MM_MULTI_MAX = 25
PB_PRIM_MAX = 69
PB_MULTI_MAX = 26

MM_WINNING_LIST = [2,4,10,10,200,500,10000,1000000, "Jackpot"]

class LottoNums:
    """Lotto number class"""
    
    def __init__(self, type, nums=None):
        """Creates a Lotto number listing

        Arguments:
        type -- 0 for MegaMillions; non-zero for Powerball
        nums -- List (ie: [prim_nums, multi]) where prim_nums is a set of the
                   primary 5 nums, and multi is a set of the multiplier
                   NOTE: both sets should be sets of string repr of ints

        returns:
            LottoNums object
        """
        self.prim_nums = None
        if type == 0:
            prim_max = MM_PRIM_MAX
            multi_max = MM_MULTI_MAX
        else:
            prim_max = PB_PRIM_MAX
            multi_max = PB_MULTI_MAX
            
        if nums is None:
            while self.prim_nums is None:
                self.get_entry(prim_max, multi_max)
        else:
            self.prim_nums = nums[0]
            self.multi = nums[1]

    def get_entry(self, prim_max, multi_max):
        while True:
            unparsed_entry = input("Enter entry: ").strip()
            parsed_entry = unparsed_entry.split(" ")
            if len(parsed_entry) != 6:
                print("Only 5 nums may be played.")
            else:
                prim_nums_str = parsed_entry[:5]
                multi_str = parsed_entry[-1]
                # check nums
                if len(set(prim_nums_str)) != 5:
                    print("Primary nums must be unique.")
                else:
                    self.cast_primary_nums(prim_nums_str, prim_max)

                    multi = self.chech_num("Multiplier", multi_str, multi_max)
                    if (multi is not None) and (self.prim_nums is not None):
                        break
            print("Try again.")

        self.prim_nums = set(prim_nums_str)
        self.multi = {multi_str}
    
    @staticmethod
    def chech_num(num_name, str_num, max):
        range_err = ValueError(f"{num_name} {str_num} is not in the range of {MIN} and {max}")
        try:
            num = int(str_num)
            if not MIN <= num <= max:
                raise range_err
            return num
        except ValueError as ex:
            if ex is not range_err:
                print(f"{num_name} {str_num} is not a number.")
            else:
                print(ex)
    
    def cast_primary_nums(self, prim_nums_str, prim_max):
        prim_nums = list()
        for num in prim_nums_str:
            num = self.chech_num("Primary", num, prim_max)
            if num is None:
                return None
            prim_nums.append(num)
        self.prim_nums = prim_nums

class Lotto:
    WIN_NUMS = None
    LAST_PULL_DATE = None

    def __init__(self):
        self.update_lotto()
    
    def update_lotto(self):
        # todo lock thread if it is not None
        today = datetime.today()
        age_of_pull = 0
        if Lotto.LAST_PULL_DATE is not None:
            print(f"{today = }")
            print(f"{Lotto.LAST_PULL_DATE = }")
            age_of_pull = today - Lotto.LAST_PULL_DATE
            print(f"{age_of_pull = }")
            age_of_pull = age_of_pull.days
            sleep(2)
        if (Lotto.WIN_NUMS is not None) and (age_of_pull <= 5):
            return
        self.mm_thread = CustomThread(self.pull_mm)
        self.mm_thread.setDaemon(True)  # allow for early Ctrl+C
        self.mm_thread.start()
        # todo unlock
        # todo take out
        print("Updating nums!!!!!!!!")
        sleep(2)
    
    def check_entries(self, entries):
        if self.mm_thread is None:
            self.update_lotto()
        if self.mm_thread is not None:
            self.mm_thread.waiting_obj.set_waiting()
            self.mm_thread.join()
            self.game_name, self.win_prim, self.win_multi = self.mm_thread.value
            self.mm_thread = None
        Lotto.WIN_NUMS = LottoNums(type=0, nums=[self.win_prim, self.win_multi])
        print(f"{self.game_name} win: {Lotto.WIN_NUMS.prim_nums} {Lotto.WIN_NUMS.multi}")

        for entry in entries:
            winnings = self.check_wins(MM_WINNING_LIST, entry)
            print(f"Played: {entry.prim_nums} {entry.multi}")
            print(f"Won: {winnings}")

    # self not used but needed to be used with Custom
    def pull_mm(self):
        jackpot = requests.get('https://lottery.sd.gov/api/igt/v2/draw-games/draws/?game-names=Mega%20Millions').json()['draws'][1]

        game_name = jackpot['gameName']
        results = jackpot['results'][0]
        prim_nums = results['primary']
        multi = results['secondary'][0]

        # set time of last pull to last draw 
        # (+23 hours to get to correct time, they do midnight for the time stamp 
        # not 2300)
        Lotto.LAST_PULL_DATE = datetime.fromtimestamp(int(str(jackpot['drawTime'])[:10])) + timedelta(hours=23)

        return game_name, set(prim_nums), {multi}

    def check_wins(self, winning_list, played_nums):
        # todo include powerplay option for powerball
        matching = len(played_nums.prim_nums & Lotto.WIN_NUMS.prim_nums)
        jackpot_matching = Lotto.WIN_NUMS.multi & played_nums.multi
        # not using match case for backwards compatability down till 3.6
        winnings = 0
        if matching == 0:
            if jackpot_matching:
                winnings = winning_list[0]
        elif matching == 1:
            if jackpot_matching:
                winnings = winning_list[1]
        elif matching == 2:
            if jackpot_matching:
                winnings = winning_list[2]
        elif matching == 3:
            if not jackpot_matching:
                winnings = winning_list[3]
            else:
                winnings = winning_list[4]
        elif matching == 4:
            if not jackpot_matching:
                winnings = winning_list[5]
            else:
                winnings = winning_list[6]
        elif matching == 5:
            if not jackpot_matching:
                winnings = winning_list[7]
            else:
                winnings = winning_list[8]
        if isinstance(winnings, int):
            winnings = f"${winnings:,}"
        return winnings

class LottoMenu:
    def __init__(self):
        # set up lottos
        self.mega_millions = Lotto()
        self.mm_entries = list()
        # todo add powerball
        self.pb_entries = list()
        self.main_menu()
    
    def main_menu(self):
        prompt = "Which lotto do you want to check?"
        options = {"Mega Millions": self.mega_millions_view}
        self.funct_menu(options, prompt)
    
    def mega_millions_view(self):
        self.current_type = 0  # mega millions
        self.new_entry()
    
    @classmethod
    def pass_option(cls):
        pass

    def funct_menu(self, options, prompt=None):
        while True:
            key_list = list(options.keys())
            if prompt is not None:
                terminal_menu = TerminalMenu(key_list, title=prompt)
            else:
                terminal_menu = TerminalMenu(key_list)
            menu_entry_index = terminal_menu.show()
            if menu_entry_index is None:
                # Ctrl+C/D
                quit_prompt = "Quit?"
                quit_options = ["Cancel", "Yes"]
                terminal_menu = TerminalMenu(quit_options, title=quit_prompt)
                menu_entry_index = terminal_menu.show()
                if menu_entry_index == 1:
                    return
            else:
                break
        options[key_list[menu_entry_index]]()
    
    def mm_menu(self):
        options = {"New Entry": self.new_entry, "Done": self.check_entries}
        self.funct_menu(options)

    def new_entry(self):
        # todo make sure it is not a dup entry
        try:
            played_nums = LottoNums(type=self.current_type)
        except (KeyboardInterrupt, EOFError):  # todo do this better?
            sys.exit()
        if self.current_type == 0:
            self.mm_entries.append(played_nums)
        else:
            self.pb_entries.append(played_nums)
        self.mm_menu()

    def check_entries(self):
        self.mega_millions.check_entries(self.mm_entries if self.current_type == 0 else self.pb_entries)
        self.main_menu()
        

def main():
    #todo list the jackpot
    #todo multiple entries
    #todo make sure game name is used
    #todo use terminal menu to select type as well as ask if this is the last listing
    LottoMenu()

if __name__ == "__main__":
    main()

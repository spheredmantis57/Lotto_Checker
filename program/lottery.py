import datetime
import os
from time import sleep
import abc
from datetime import datetime, timedelta
import signal

from pick import pick
import requests

from custom_thread import CustomThread

MIN = 1
MM_PRIM_MAX = 70
MM_MULTI_MAX = 25
PB_PRIM_MAX = 69
PB_MULTI_MAX = 26

def noop(*args, **kwargs):
    return

class LottoNums:
    """Lotto number class"""
    MM = 0
    PB = 1
    
    def __init__(self, type, nums=None):
        """Creates a Lotto number listing

        Arguments:
        type -- class viariables of MM and PB
        nums -- List (ie: [prim_nums, multi]) where prim_nums is a set of the
                   primary 5 nums, and multi is a set of the multiplier
                   NOTE: both sets should be sets of string repr of ints

        returns:
            LottoNums object
        """
        self.prim_nums = None
        # set max depending on which lotto
        if type == LottoNums.MM:
            prim_max = MM_PRIM_MAX
            multi_max = MM_MULTI_MAX
        else:
            prim_max = PB_PRIM_MAX
            multi_max = PB_MULTI_MAX
        
        # see if user needs to enter the entry or if it was given
        if nums is None:
            while self.prim_nums is None:
                self.get_entry(prim_max, multi_max)
        else:
            self.prim_nums = nums[0]
            self.multi = nums[1]
    
    def __str__(self):
        """gives the string rep of the object"""
        strng = str(" ".join(self.prim_nums))
        return f"{strng} {list(self.multi)[0]}"
    
    def __eq__(self, other):
        """determines if LottoNums are equal"""
        prims_match = self.prim_nums == other.prim_nums
        multi_match = self.multi == other.multi
        return prims_match and multi_match

    def get_entry(self, prim_max, multi_max):
        """gets user input to make a new entry

        Arguments:
        prim_max -- Int the max value that a primary number can be
        multi_max -- Int the max value that a multiplier can be
        """
        # loop till valid lotto number
        while True:
            unparsed_entry = input("Enter entry: ").strip()
            parsed_entry = unparsed_entry.split(" ")
            if len(parsed_entry) != 6:
                print("Exactly 5 nums may be played.")
            else:
                prim_nums_str = parsed_entry[:5]
                multi_str = parsed_entry[-1]
                # check nums validity
                if len(set(prim_nums_str)) != 5:
                    print("Primary nums must be unique.")
                else:
                    self.validate_prims(prim_nums_str, prim_max)

                    multi = self.chech_num("Multiplier", multi_str, multi_max)
                    if (multi is not None) and (self.prim_nums is not None):
                        break
            print("Try again.")

        # set the lotto numbers of the entry
        self.prim_nums = set(prim_nums_str)
        self.multi = {multi_str}
    
    @staticmethod
    def chech_num(num_name, str_num, max):
        """checks the validity of a specific number of an entry
        
        Arguments:
        str_num -- the string of the number being played
        max -- Int the max value that the num can be

        Returns:
        The number as an int if valid; None if invalid
        """
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
    
    def validate_prims(self, prim_nums_str, prim_max):
        """checks each primary number is valid

        NOTE: validation of only 5 unique numbers must have already been done
        
        Arguments:
        prim_nums -- string of the primary numbers being played
        prim_max -- Int the max a primary number can be
        """
        prim_nums = list()
        for num in prim_nums_str:
            num = self.chech_num("Primary", num, prim_max)
            if num is None:
                return
            prim_nums.append(num)
        self.prim_nums = prim_nums

class IndividualLotto(abc.ABC):
    # NOTE: must make child classes singletons
    WINNING_LIST: str = NotImplemented
    WIN_NUMS: LottoNums = NotImplemented
    LAST_PULL_DATE: datetime = NotImplemented
    THREAD: CustomThread = NotImplemented
    TYPE: int = NotImplemented  # from LottoNums

    def __init__(self):
        super().__init__()

    @abc.abstractmethod
    def pull(self):
        pass

    def update_lotto(self):
        """makes sure the lotto is the most up-to-date listing"""
        today = datetime.today()
        age_of_pull = 0
        if self.LAST_PULL_DATE is not None:
            # calculate the age since the last pull if it has already been set
            age_of_pull = today - self.LAST_PULL_DATE
            age_of_pull = age_of_pull.days
        if (self.WIN_NUMS is not None or self.THREAD is not None) and (age_of_pull <= 7):
            # lotto is up-to-date, does not need to be pulled again
            return
        # the lotto needs to be pulled again
        self.THREAD = CustomThread(self.pull)
        self.THREAD.deamon = True  # allow for early Ctrl+C
        self.THREAD.start()
    
    def check_entries(self, entries):
        """checks a list of entries to find out winnings
        
        Arguments:
        entries -- List of LottoNums that have been played
        """
        # update the lotto if needed
        if self.THREAD is None:
            self.update_lotto()
        else:
            # still waiting on the most recent lotto pulling
            print("INFO: Waiting on win numbers")
            self.THREAD.waiting_obj.set_waiting()
            self.THREAD.join()
            self.game_name, self.win_prim, self.win_multi = self.THREAD.value
            self.THREAD = None
        # save the winning numbers
        self.WIN_NUMS = LottoNums(type=self.TYPE, nums=[self.win_prim, self.win_multi])

        # check each entry for its winnings
        for entry in entries:
            winnings = self.check_wins(self.WINNING_LIST, entry)
            print(f"Played: {entry.prim_nums} {entry.multi}")
            print(f"Won: {winnings}")

    def check_wins(self, winning_list, played_nums):
        """checks the winning money of a single entry
        
        Arguments:
        winning_list -- list of possible winnings, from least to most
        played_nums -- LottoNums object of the entry to check
        
        Returns:
        str - the won amount (can be 'Jackpot')
        """
        # todo include powerplay option for powerball
        matching = len(played_nums.prim_nums & self.WIN_NUMS.prim_nums)
        jackpot_matching = self.WIN_NUMS.multi & played_nums.multi
        # not using match case for backwards compatability down till 3.6
        winnings = 0
        # get the winning money amount
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

class MegaMillions(IndividualLotto):
    # todo doc strings
    WIN_NUMS = None
    LAST_PULL_DATE = None
    WINNING_LIST = [2,4,10,10,200,500,10000,1000000, "Jackpot"]
    THREAD = None
    TYPE = LottoNums.MM

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(MegaMillions, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        super().__init__()
        self.update_lotto()

    def pull(self):
        """pulls the most up-to-date mega millions drawing
        
        Returns:
        tuple -- game name(string), set of prim_nums, set of multi
        Note: Each set element is an string
        """
        jackpot = requests.get('https://lottery.sd.gov/api/igt/v2/draw-games/draws/?game-names=Mega%20Millions').json()['draws'][1]

        game_name = jackpot['gameName']
        results = jackpot['results'][0]
        prim_nums = results['primary']
        multi = results['secondary'][0]

        # set time of last pull to last draw 
        # (+23 hours to get to correct time, they do midnight for the time stamp 
        # not 2300)
        self.LAST_PULL_DATE = datetime.fromtimestamp(int(str(jackpot['drawTime'])[:10])) + timedelta(hours=23)

        return game_name, set(prim_nums), {multi}



class LottoMenu:
    """class for the Menu"""
    def __init__(self):
        """creates a LottoMenu object"""
        # self.orig_handler = signal.signal(signal.SIGINT, self.handler)
        # self.allow_sigint = False
        # set up lottos
        MegaMillions()
        self.current_lotto = MegaMillions
        self.mm_entries = list()
        # todo add powerball
        self.pb_entries = list()
        self._menu = None
        sleep(1)  # give small amount of time to load up
        self.allow_sigint = True
        self.main_menu()
    
    # def handler(self, signum, frame):
    #     if self.allow_sigint:
    #         raise KeyboardInterrupt()
    #         # self.orig_handler(signum, frame)
    #     else:
    #         pass
    
    def main_menu(self):
        # todo ask if they would like to clear the previous entires
        """displayes the main menu"""
        prompt = "Which lotto do you want to check?"
        # todo add powerball
        options = {"Mega Millions": self.mega_millions_view}
        self.funct_menu(options, prompt)
    
    def mega_millions_view(self):
        """displays the mm menu"""
        self._menu = self.mega_millions_view
        self.mm_menu()

    def funct_menu(self, options, prompt=None):
        """used by other functions to display a pick
        
        Aruments:
        options -- Dict key is the label for the option, the value is the funct
                   to call if the option is selected
        prompt -- if give: will be a prompt for the menu options
        """
        os.system("clear") if os.name == "posix" else os.system("cls")
        # look to account for cancels with Ctrl+C/D
        while True:
            # display menu and get choice
            key_list = list(options.keys())
            try:
                if prompt is not None:
                    choice_tuple = pick(key_list, title=prompt)
                else:
                    choice_tuple = pick(key_list)
                break
            except KeyboardInterrupt:
                try:
                    # verify quit
                    self.quit_funct()
                except KeyboardInterrupt:
                    return
        
        # goes to the next function depending on the choice
        options[choice_tuple[0]]()

    def quit_funct(self):
        # todo make a previous menu option
        """verifies if a user wants to quit or not
        
        Raises:
        Keyboard Interrupt -- user Ctrl+C/D
        """
        quit_prompt = "Quit?"
        quit_options = ["Cancel", "Yes"]
        choice_tuple = pick(quit_options, title=quit_prompt)
        if choice_tuple[1] == 1:
            raise KeyboardInterrupt("User Quit")
    
    def mm_menu(self):
        """displays the main menu"""
        # build out options
        options = {"New Entry": self.new_entry}
        if self._menu is self.mega_millions_view:
            current_list = self.mm_entries
        else:
            current_list = self.pb_entries
        if len(current_list) != 0:
            options["Done"] = self.check_entries
        # get choice
        try:
            self.funct_menu(options)
        except KeyboardInterrupt:
            pass

    def verify_dup(self, played_nums):
        """check if the entry has already been submitted
        
        Arguments:
        played_nums -- LottoNumbs object of entry

        Raises:
        ValueError -- played nums is a duplicate
        """
        if self._menu is self.mega_millions_view:
            current_list = self.mm_entries
        else:
            current_list = self.pb_entries
        if played_nums in current_list:
            raise ValueError(f"{played_nums} has already been played.")

    def new_entry(self):
        """gets a new entry from user"""
        # todo allow for a back out on top of quit or cancel
        if self._menu is self.mega_millions_view:
            current_type = LottoNums.MM
        else:
            current_type = LottoNums.PB
        while True:
            try:
                played_nums = LottoNums(type=current_type)
                self.verify_dup(played_nums)
                break
            except (KeyboardInterrupt, EOFError):
                self.quit_funct()
            except ValueError as ex:
                options = {"Submit Duplicate": noop, "Try again": self.dup_retry}
                try:
                    self.funct_menu(options, prompt=str(ex))
                    break
                except ValueError:
                    # user wants to try again
                    pass
        if self._menu is self.mega_millions_view:
            self.mm_entries.append(played_nums)
        else:
            self.pb_entries.append(played_nums)
        self.mm_menu()
    
    def dup_retry(self):
        """used in new_entry to alert that a user wants to try again with a
        duplicate entry. This is needed because funct_menu needs a function
        
        Raises:
        ValueError -- always
        """
        raise ValueError("User trying again.")

    def check_entries(self):
        """checks entries then goes back to the main menu"""
        current_list = self.pb_entries
        if self._menu is self.mega_millions_view:
            current_list = self.mm_entries
        self.current_lotto().check_entries(current_list)
        self.disp_continue()
        self.main_menu()
    
    def disp_continue(self):
        try:
            input("CONTINUE?")
        except (KeyboardInterrupt, EOFError):
            try:
                self.quit_funct()
            except (KeyboardInterrupt, EOFError):
                raise KeyboardInterrupt("User quitting")
        

def main():
    """main function of the program"""
    #todo list the jackpot
    #todo make sure game name is used
    LottoMenu()

if __name__ == "__main__":
    main()

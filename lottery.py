import requests
import sys

from custom_thread import CustomThread, WaitingObject

MIN = 1
MM_PRIM_MAX = 70
MM_MULTI_MAX = 25
PB_PRIM_MAX = 69
PB_MULTI_MAX = 26

MM_WINNING_LIST = [2,4,10,10,200,500,10000,1000000, "Jackpot"]

class LottoNums:
    """Lotto number class"""
    
    def __init__(self, type, numbers=None):
        """Creates a Lotto number listing

        Arguments:
        type -- 0 for MegaMillions; non-zero for Powerball
        numbers -- List (ie: [prim_nums, multi]) where prim_nums is a set of the
                   primary 5 numbers, and multi is a set of the multiplier
                   NOTE: both sets should be sets of string repr of ints

        returns:
            LottoNums object
        """
        if type == 0:
            prim_max = MM_PRIM_MAX
            multi_max = MM_MULTI_MAX
        else:
            prim_max = PB_PRIM_MAX
            multi_max = PB_MULTI_MAX
            
        if numbers is None:
            self.get_entry(prim_max, multi_max)
        else:
            self.prim_nums = numbers[0]
            self.multi = numbers[1]

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
    def __init__(self):
        pass



def pull_mm():
    jackpot = requests.get('https://lottery.sd.gov/api/igt/v2/draw-games/draws/?game-names=Mega%20Millions').json()['draws'][1]

    game_name = jackpot['gameName']
    results = jackpot['results'][0]
    prim_nums = results['primary']
    multi = results['secondary'][0]

    return game_name, set(prim_nums), {multi}

def check_wins(name, winning_list, win_numbers, played_numbers):
    # todo include powerplay option for powerball
    print(f"{name} win: {win_numbers.prim_nums} {win_numbers.multi}")
    matching = len(played_numbers.prim_nums & win_numbers.prim_nums)
    print(f"{matching = }")
    jackpot_matching = win_numbers.multi & played_numbers.multi
    if not jackpot_matching:
        print("MATCHING JACKPOT")
    # not using match case for backwards compatability down till 3.6
    winnings = 0
    if matching == 0:
        if not jackpot_matching:
            winnings = winning_list[0]
    elif matching == 1:
        if not jackpot_matching:
            winnings = winning_list[1]
    elif matching == 2:
        if not jackpot_matching:
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


def main():
    #todo list the jackpot
    #todo multiple entries
    #todo add powerball without powerplay
    #todo make sure game name is used
    #todo use terminal menu to select type as well as ask if this is the last listing
    mm_thread = CustomThread(pull_mm)
    mm_thread.setDaemon(True)  # allow for early Ctrl+C
    mm_thread.start()

    try:
        played_numbers = LottoNums(type=0)
    except (KeyboardInterrupt, EOFError):
        sys.exit()
    print(f"Played: {played_numbers.prim_nums} {played_numbers.multi}")

    mm_thread.join_result()
    game_name, win_prim, win_multi = mm_thread.value
    winning_numbers = LottoNums(type=0, numbers=[win_prim, win_multi])
    winnings = check_wins(game_name, MM_WINNING_LIST, winning_numbers, played_numbers)
    print(f"Won: {winnings}")


if __name__ == "__main__":
    main()

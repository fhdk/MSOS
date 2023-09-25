#  Copyright (c) 2023.
#  Original project: https://github.com/lambdanil/astOS
#  License: GNU GPL, version 3 or later; https://www.gnu.org/licenses/gpl.html
#  Fork: https://github.com/fhdk/astOS
#  Modified by @linux-aarhus at ${DATE}

class BColors:
    HEADER = '\033[95m'
    OK_BLUE = '\033[94m'
    OK_CYAN = '\033[96m'
    OK_GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END_C = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    NORMAL = "\033[1;37m"


def debug(where: str, what: str, value: str) -> None:
    print("{} {} >>>> '{} = {}'".format(BColors.WARNING, where, what, value))


def underline(message: str) -> None:
    print("{}{}{}".format(BColors.UNDERLINE, message, BColors.END_C))


def default(message: str) -> None:
    print("{}{}{}".format(BColors.NORMAL, message, BColors.END_C))


def header(message: str) -> None:
    print("{}:: {} {}".format(BColors.HEADER, message, BColors.END_C))


def attention(message: str) -> None:
    print("{}  ->{} {}".format(BColors.OK_CYAN, BColors.END_C, message))


def success(message: str) -> None:
    print("{}[ OK ] {}{}".format(BColors.OK_GREEN, BColors.END_C, message))


def fail(message: str) -> None:
    print("{}[FAIL]{} {}".format(BColors.FAIL, BColors.END_C, message))


def warning(message: str) -> None:
    print("{}[WARN]{} {}".format(BColors.WARNING, BColors.END_C, message))

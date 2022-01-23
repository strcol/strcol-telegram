import datetime
import threading
import time

import colorama


LOGGER_INSTANCE = None


class LoggerLevel:
    LEVEL_NONE = 0
    LEVEL_ERROR = 1
    LEVEL_WARNING = 2
    LEVEL_INFO = 3
    LEVEL_DEBUG = 4

    @classmethod
    def from_string(cls, string):
        levels = {
            'none': cls.LEVEL_NONE,
            'error': cls.LEVEL_ERROR,
            'warning': cls.LEVEL_WARNING,
            'info': cls.LEVEL_INFO,
            'debug': cls.LEVEL_DEBUG
        }
        return levels.get(string.strip().lower()) or cls.LEVEL_INFO


class Logger:
    def __init__(
            self, level=LoggerLevel.LEVEL_DEBUG, file=None,
            print_function=print):
        global LOGGER_INSTANCE
        LOGGER_INSTANCE = self

        self.level = level
        self.file = file
        self.print = print_function

        self.queue = []
        self.running = False

        if not isinstance(self.level, int):
            self.level = LoggerLevel.from_string(self.level)

        colorama.init(autoreset=True)

        self.start()

    @staticmethod
    def clear_message(message):
        chars = (
            colorama.Fore.BLACK, colorama.Fore.RED, colorama.Fore.GREEN,
            colorama.Fore.YELLOW, colorama.Fore.BLUE, colorama.Fore.MAGENTA,
            colorama.Fore.CYAN, colorama.Fore.WHITE, colorama.Fore.RESET,
            colorama.Back.BLACK, colorama.Back.RED, colorama.Back.GREEN,
            colorama.Back.YELLOW, colorama.Back.BLUE, colorama.Back.MAGENTA,
            colorama.Back.CYAN, colorama.Back.WHITE, colorama.Back.RESET,
            colorama.Style.DIM, colorama.Style.NORMAL, colorama.Style.BRIGHT,
            colorama.Style.RESET_ALL
        )
        for char in chars:
            message = message.replace(char, '')
        return message

    def start(self):
        self.running = True
        thread = threading.Thread(target=self._service)
        thread.daemon = True
        thread.start()

    def _service(self):
        while self.running:
            if self.queue:
                print(self.queue.pop(0))
            time.sleep(.0001)

    def _log(self, max_level, level_color, level_name, message):
        if self.level < max_level:
            return
        message = (
            f'{colorama.Fore.CYAN}[{datetime.datetime.now().isoformat()}] ' +
            f'{level_color}[{level_name}] ' +
            f'{colorama.Fore.WHITE}{message}'
        )
        if self.file:
            with open(self.file, 'a', encoding='utf-8') as file:
                file.write(self.clear_message(message) + '\n')
        self.queue.append(message)

    def error(self, message):
        self._log(
            max_level=LoggerLevel.LEVEL_ERROR,
            level_color=colorama.Fore.RED,
            level_name='ERROR',
            message=message
        )

    def warning(self, message):
        self._log(
            max_level=LoggerLevel.LEVEL_WARNING,
            level_color=colorama.Fore.YELLOW,
            level_name='WARNING',
            message=message
        )

    def info(self, message):
        self._log(
            max_level=LoggerLevel.LEVEL_INFO,
            level_color=colorama.Fore.GREEN,
            level_name='INFO',
            message=message
        )

    def debug(self, message):
        self._log(
            max_level=LoggerLevel.LEVEL_DEBUG,
            level_color=colorama.Fore.MAGENTA,
            level_name='DEBUG',
            message=message
        )

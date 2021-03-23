import logging
import os
import time


class Log:

    def __init__(self, filename="log"):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        self.filename = filename

        # 格式化日志输出
        formatter = logging.Formatter('[%(asctime)s]----%(message)s')

        # 使用StreamHandler输出到屏幕
        terminal = logging.StreamHandler()
        terminal.setLevel(logging.DEBUG)
        terminal.setFormatter(formatter)

        # 仅当日志名称为log时输出到屏幕，否则在/logs下新建对应名称的文件夹，且不输出到屏幕
        filedir = r"%s\\logs" % os.getcwd()
        if self.filename != "log":
            filedir += r"\\%s" % self.filename
        else:
            self.logger.addHandler(terminal)
        if not os.path.exists(filedir):
            os.mkdir(filedir)
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        logfile = r"%s\\%s_%s.log" % (filedir, self.filename, timestamp)

        # 使用FileHandler输出到文件
        into_file = logging.FileHandler(logfile)
        into_file.setLevel(logging.DEBUG)
        into_file.setFormatter(formatter)
        self.logger.addHandler(into_file)

    def info(self, msg):
        self.logger.info(msg)

    def warn(self, msg):
        self.logger.warning(msg)

    def debug(self, msg):
        self.logger.debug(msg)

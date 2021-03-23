from tools import *
from para_data import *
"""通用函数----function.py"""

from telnet import TelnetClient, log


# 建立telnet连接实例
def open_device(para_info):
    if len(para_info) < 5:
        host, port = para_info[:2]
        switch = TelnetClient(host, port)
    else:
        host, port, prompt, user, pwd = para_info
        switch = TelnetClient(host, port, prompt, user, pwd)
    return switch







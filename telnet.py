import re
import time
import socket
import telnetlib
from log import Log


log = Log()
RECONNECT_TIME = 3


class TelnetClient:

    def __init__(self, host, port=23, prompt="", user=None, pwd=None):
        self.host = host
        self.port = port
        self.user = user
        self.pwd = pwd
        self.prompt = prompt
        self.tn = telnetlib.Telnet()
        self._open()

    def _open(self):
        global RECONNECT_TIME
        if RECONNECT_TIME > 0:
            try:
                self.tn.open(self.host, self.port, timeout=3)
            except socket.timeout:
                RECONNECT_TIME -= 1
                time.sleep(10)
                self._open()
            else:
                msg = u"%s-%d telnet连接成功！" % (self.host, self.port)
                # 针对Centos7的if分支
                if self.user and self.pwd:
                    self.tn.read_until(b"localhost login: ", timeout=3)
                    self.sendcmd(self.user, expect="Password: ", timeout=3, spaceflag=False)
                    login_result = self.prompt in self.sendcmd(self.pwd, timeout=3, spaceflag=False)
                    if login_result:
                        log.info(msg)
                    else:
                        raise ConnectionRefusedError(u"%s-%d telnet连接失败，用户名或密码错误！" \
                                                             % (self.host, self.port))
                else:
                    log.info(msg)
                    self.initial()
        else:
            raise ConnectionError(u"%s-%d 没有响应，请检查网络配置" % (self.host, self.port))

    def initial(self):
        self.changeview("enable")
        self.sendcmd("terminal length 0")
        self.changeview()
        # time.sleep(0.1)
        prompt = self.sendcmd(timeout=0.5)
        try:
            self.prompt = re.match(r"(.*\n)?(\S+)\(config\)\#", prompt).group(2)
        except AttributeError:
            pass
        # print(self.prompt)
        self.sendcmd("exec 0 0", timeout=0.5)


    def close(self):
        self.changeview()
        self.sendcmd("no exec-timeout", timeout=0.5)
        self.tn.close()
        log.info(u"%s-%d telnet连接关闭！" % (self.host, self.port))

    # 发送命令并获取回显
    def sendcmd(self, cmd="", expect=None, timeout=10, spaceflag=True, logflag=False):
        self.tn.read_very_eager()
        try:
            self.tn.write("{}\n".format(cmd).encode("ascii"))
        except socket.timeout:
            time.sleep(5)
            self._open()
            self.tn.read_very_eager()
            self.sendcmd(cmd, expect, timeout, logflag)
        if not expect:
            r1 = re.compile((re.escape(self.prompt) + r"([#>]|\(config.*\)#)").encode("ascii"))
            r2 = re.compile(r"/ # |BCM\.0> ".encode("ascii"))
            expect = [r1, r2]
        elif isinstance(expect, str):
            expect = [re.escape(expect).encode("ascii")]
        else:
            expect = [re.escape(i).encode("ascii") for i in expect]
        # 若buffer中没有预期字符串，则每隔0.5s向屏幕发送空格（可通过spaceflag控制是否发送）
        b, c, d = self.tn.expect(expect, timeout=timeout)
        result = d.decode()
        result = re.sub(r"\r{1,2}", "", result).strip()
        if logflag:
            log.info(result)
        return result

    # 操作模式切换
    def changeview(self, view="config"):
        current_view = self.sendcmd(timeout=0.5).split("\n")[-1]
        bcm_flag = "BCM" in current_view
        linux_flag = "/ #" in current_view
        if view == "bcm":
            if linux_flag:
                self.tn.write(b"exit\n")
                time.sleep(1)
                log.info(u"退出Linux模式！")
            self.sendcmd("\36bcm")
            log.info(u"进入BCM模式！")
        elif view == "linux":
            if bcm_flag:
                self.tn.write(b"exit\n")
                time.sleep(1)
                log.info(u"退出BCM模式！")
                self.tn.write(b"\n\n\n")
            self.sendcmd("\36ma")
            log.info(u"进入Linux模式！")
        elif view == "enable":
            if bcm_flag or linux_flag:
                self.tn.write(b"exit\n")
                time.sleep(1)
                log.info(u"退出非用户界面")
                self.tn.write(b"\n\n\n")
            current_view = self.sendcmd("\32", timeout=0.5).split("\n")[-1]
            if ">" in current_view:
                self.sendcmd("enable", timeout=0.5)
            # log.info(u"进入特权模式")
        else:
            self.changeview("enable")
            if view == "normal":
                self.sendcmd("exit", timeout=0.5)
                # log.info(u"进入一般模式")
            else:
                self.sendcmd("config", timeout=0.5)
                # log.info(u"进入配置模式")

    def collect_info(self):
        log = Log("version&config")
        self.changeview("enable")
        version = self.sendcmd("show version")
        log.info(version)
        config = self.sendcmd("show run")
        log.info(config)

    def set_hostname(self, hostname):
        self.changeview("config")
        self.prompt = hostname
        self.sendcmd("hostname %s" % hostname)

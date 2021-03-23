"""from tools import *
from para_data import *
from telnet import TelnetClient, log"""
"""case.py---测试用例"""
from function import *

# 0--单元测试
def unit_test(para):
    print("unit test!")
    switch = open_device(para)
    log.info(switch.sendcmd('show slot'))
    # for i in range(1, 1001):
    #     switch.changeview("enable")
    #     switch.sendcmd("reload", spaceflag=False, timeout=0.5)
    #     switch.sendcmd("Y")
    #     switch.tn.read_until(b"HA batch backup has finished!", timeout=120)
    #     msg = switch.sendcmd("show slot", logflag=True)
    #     res = re.findall(r"Work mode\s+:\s(\S+)", msg)
    #     res_s = re.findall(r"Work state\s+:\s(\S+)", msg)
    #     if len(res) == 4:
    #         if res[0]=="ACTIVE" and res[1]=="STANDBY" and res[2]=="SLAVE" and res[3]=="SLAVE" and res_s[0]=="RUNNING" and res_s[1]=="RUNNING" and res_s[2]=="RUNNING" and res_s[3]=="RUNNING":
    #             log.info(u"第 %d 次重启成功" % i)
    #         else:
    #             log.info(u"第 %d 次重启失败" % i)
    #             break
    #     else:
    #         log.info(u"第 %d 次重启失败" % i)
    #         break
    switch.close()

# 1--向控制台发送Ctrl+B
def send_ctrl_b(para):
    switch = open_device(para)
    while True:
        msg = switch.sendcmd("\2", expect=["[Boot]", "[boot]"], timeout=0.5)
        if "[Boot]" in msg or "[boot]" in msg:
            log.info(u"向控制台发送Ctrl+B成功")
            break
    switch.tn.close()

# "2--查看接口速率"接口速率监控，只检查5秒内的统计数据
def check_int_rate(para, care="both", ports=None, interval=60, tolerance=1):
    care = care.upper()
    switch = open_device(para)
    switch.changeview("enable")
    cmd = "show interface ethernet counter rate"
    first_check = get_rate_or_packet(switch.sendcmd(cmd, logflag=True))[1]
    if ports:
        port_list = port_str_to_array(ports)
    else:
        port_list = first_check.keys()
    for check_time in range(1, 1001):
        second_check = get_rate_or_packet(switch.sendcmd(cmd, logflag=True))[1]
        errport = []
        for port in port_list:
            in_wave = compare_data(first_check[port]["IN(pkts/s)"], second_check[port]["IN(pkts/s)"], tolerance)
            out_wave = compare_data(first_check[port]["OUT(pkts/s)"], second_check[port]["OUT(pkts/s)"], tolerance)
            if in_wave and care in ["IN", "BOTH"]:
                errport.append(port)
                log.info(u"端口 %s 入方向出现速率波动" % port)
            if out_wave and care in ["OUT", "BOTH"]:
                errport.append(port)
                log.info(u"端口 %s 出方向出现速率波动" % port)
        if errport:
            log.info(u"第%d次检查，端口 %s 速率异常" % (check_time, port_array_to_str(errport)))
        else:
            log.info(u"第%d次检查，所有端口速率正常" % check_time)
        first_check = second_check
        time.sleep(interval)
        # sendmail(subject, body)
        # break
    switch.close()

# 3--查看CPU/内存使用率
def check_cpu_mem(para):
    switch = open_device(para)
    switch.changeview("enable")
    cpu_data = switch.sendcmd("show cpu usage")
    log.info(cpu_data)
    mem_data = switch.sendcmd("show memory usage")
    log.info(mem_data)
    switch.close()

# 4--通过ftp反复升降级img
def upgrade_byftp(para, target_dir="flash"):
    log.info(u"%s开始执行反复升降级操作%s" % ("#"*20, "#"*20))
    upgrade_times = 1001
    version1 = "R0002.0023"
    version2 = "R0002.0024"

    import random
    last_ip = int(random.random() * 255)
    patten = re.compile(r"(.*\n)*\s+SoftWare Package Version.*\((\S+)\)")

    switch = open_device(para)
    current_version = patten.match(switch.sendcmd("show version")).group(2)
    switch.sendcmd("int e 0\nip ad 10.1.1.%d 255.255.255.0" % last_ip)
    for upgrade_time in range(1, upgrade_times):
        version = version1 if current_version != version1 else version2
        switch.changeview("enable")
        cmd = "copy ftp://image:image@10.1.1.254/0guoge/%s_%s.img %s:/nos.img" % (para[2], version, target_dir)
        conn_res = switch.sendcmd(cmd, expect=["[Y/N]", "successful"], timeout=2, logflag=True)
        if "[Y/N]" in conn_res:
            conn_res = switch.sendcmd("y", expect="successful", timeout=2)
        if "successful" in conn_res:
            wt_result = switch.tn.read_until(b"Write ok", timeout=180).decode()
            if "Write ok" in wt_result:
                log.info(u"版本 %s 成功写入%s！" % (version, target_dir))
                time.sleep(5)
                switch.sendcmd("boot img %s:/nos.img primary" % target_dir)
                switch.sendcmd("write\ny\nreload\ny")
                log.info(u"设备重启...")
            else:
                raise EnvironmentError(u"版本未成功写入，请手动检查环境")
        else:
            log.info(conn_res)
            raise ConnectionRefusedError(u"版本获取失败，请检查环境配置")
        time.sleep(130)
        switch.sendcmd("\n")
        current_version = patten.match(switch.sendcmd("show version", logflag=True)).group(2)
        if current_version == version:
            log.info(u"第 %d 次升级成功" % upgrade_time)
        else:
            log.info(u"第 %d 次升级失败" % upgrade_time)
            break
    switch.close()

# 反复读DDM
def show_transceiver(para, ports):
    switch = open_device(para)
    port_list = port_str_to_array(ports)
    show_times = 1001
    for i in range(1, show_times):
        time.sleep(5)
        data = switch.sendcmd("show transceiver", logflag=True)
        check_result = True
        for port in port_list:
            tmp = re.findall(r"%s\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)" % port, data)
            if not tmp or len(tmp[0]) < 5:
                check_result = False
                log.info(u"第 %d 次读取，端口 %s 异常" % (i, port))
        if check_result:
            log.info(u"第 %d 次读取DDM信息正常" % i)
        else:
            break
    switch.close()

# telnet/ssh连接与断开
def conn_disconn(para, user="admin", passwd="admin", ip="10.1.1.2", vrf="", by="telnet"):
    if vrf:
        cmd = "%s vrf %s %s" % (by, vrf, ip)
    else:
        cmd = "%s %s" % (by, ip)
    switch = open_device(para)
    switch.changeview("enable")
    if by == "telnet":
        conn = switch.sendcmd(cmd, expect="login:", timeout=3, spaceflag=False, logflag=True)
        if "Unable" in conn:
            raise ConnectionRefusedError(u"目标不可达，请检查网络配置")
        switch.sendcmd(user, expect="Password:", timeout=3, spaceflag=False, logflag=True)
        pwd_check = switch.sendcmd(passwd, timeout=3, spaceflag=False, logflag=True)
        if "login:" in pwd_check:
            raise PermissionError(u"用户名或密码错误")
        log.info(u"telnet连接成功！")
        time.sleep(1)
        disconn = switch.sendcmd("exit", logflag=True)
        if "Connection closed." in disconn:
            log.info(u"退出telnet连接！")
    else:
        conn = switch.sendcmd(cmd, expect="username:", timeout=3, spaceflag=False, logflag=True)
        if "Unable" in conn:
            raise ConnectionRefusedError(u"目标不可达，请检查网络配置")
        switch.sendcmd(user, expect="password:", timeout=3, spaceflag=False, logflag=True)
        pwd_check = switch.sendcmd(passwd, timeout=3, spaceflag=False, logflag=True)
        if "Authentication Failure." in pwd_check:
            raise PermissionError(u"用户名或密码错误")
        log.info(u"ssh连接成功！")
        time.sleep(1)
        disconn = switch.sendcmd("exit", logflag=True)
        if "Connection closed." in disconn:
            log.info(u"退出ssh连接！")
    switch.close()


def reload(para, by="reload"):
    switch = open_device(para)
    if by == "reload":
        view = "normal"
        by += "\ny"
    else:
        view = "linux"
    for reload_time in range(1, 1001):
        switch.changeview(view)
        time.sleep(1)
        switch.sendcmd(by, logflag=True)

# 检查ipv4 ping包结果
def check_ping(para, dip, sip="", vrf="", repeat=5, bytes=56, timeout=2000):
    switch = open_device(para)
    switch.changeview("enable")
    switch.sendcmd("ping", expect="VRF name")
    switch.sendcmd(vrf, expect="Use IP Address")
    switch.sendcmd(expect="Target IP address")
    switch.sendcmd(dip, expect="Use source address option")
    if sip:
        switch.sendcmd("y", expect="Source IP address")
        switch.sendcmd(sip, expect="Repeat count")
    else:
        switch.sendcmd("n", expect="Repeat count")
    switch.sendcmd(str(repeat), expect="Datagram size in byte")
    switch.sendcmd(str(bytes), expect="Timeout in milli-seconds")
    switch.sendcmd(str(timeout), expect="Extended commands")
    waittime = repeat + 2
    data = switch.sendcmd(timeout=waittime, spaceflag=False)
    switch.close()
    result = re.match(r"(.*\n)*Success rate is (\d+) percent", data).group(2)
    if int(result) >= 98:
        return True
    return False


# 检查ipv6 ping包结果
def check_ping6(para, dip, sip="", repeat=5, bytes=56, timeout=2000):
    switch = open_device(para)
    switch.changeview("enable")
    switch.sendcmd("ping6", expect="Use IPv6 Address")
    switch.sendcmd(expect="Target IPv6 address")
    switch.sendcmd(dip, expect="Use source address option")
    if sip:
        switch.sendcmd("y", expect="Source IPv6 address")
        switch.sendcmd(sip, expect="Repeat count")
    else:
        switch.sendcmd("n", expect="Repeat count")
    switch.sendcmd(str(repeat), expect="Datagram size in byte")
    switch.sendcmd(str(bytes), expect="Timeout in milli-seconds")
    switch.sendcmd(str(timeout), expect="Extended commands")
    waittime = repeat + 2
    data = switch.sendcmd(timeout=waittime, spaceflag=False)
    switch.close()
    result = re.match(r"(.*\n)*Success rate is (\d+) percent", data).group(2)
    if int(result) >= 98:
        return True
    return False

def check_poe(para):
    switch = open_device(para)
    for i in range(1, 1001):
        switch.changeview()
        switch.sendcmd("int e 1/0/25\nshut")
        time.sleep(3)
        switch.sendcmd("no shut")
        time.sleep(150)
        check_member4 = ""
        wait_time = 120
        while wait_time > 0 and ("00-03-0f-bb-56-cc" not in check_member4):
            check_member4 = switch.sendcmd("show vsf", logflag=True)
            wait_time -= 5
            time.sleep(5)
        if wait_time <= 0:
            log.info(u"第%d次测试，member4状态异常" % i)
            break
        else:
            switch.sendcmd("\n\n\n")
            msg = switch.sendcmd("show power inline member 4", logflag=True)
            check_poe = int(re.match(r".*Power Used: (\d+)\s", msg, re.S).group(1))
            if check_poe == 0:
                log.info(u"第%d次测试，member4 POE供电异常" % i)
                break
        log.info(u"第%d次测试，member4 POE供电正常" % i)
    switch.close()

def vsf_to_alone(para):
    switch2 = open_device(para)
    switch1 = open_device(TOPO)
    for i in range(1, 1001):
        log.info(u"S4堆叠切独立")
        switch1.changeview()
        switch1.sendcmd("switch convert mode stand-alone", logflag=True)
        switch1.sendcmd("n")
        time.sleep(240)
        log.info(u"S4独立切堆叠，同时S3重启")
        switch1.changeview()
        switch1.sendcmd("switch convert mode vsf", logflag=True)
        switch1.sendcmd("n")
        switch2.changeview("enable")
        switch2.sendcmd("reload", logflag=True)
        switch2.sendcmd("y")
        time.sleep(240)
        log.info(u"第%d次测试完成" % i)
    switch1.close()
    switch2.close()

def cmd_test(para):
    switch = open_device(para)
    support = switch.sendcmd("?")
    result = re.findall(r"\s+(\S+)\s+", support)
    print(support)
    switch.close()

def reload_1U_VSF_repeatly(para):
    print("----------reload_1U_VSF_repeatly!-------------")
    switch = open_device(para)
    for i in range(1, 1001):
        switch.changeview("enable")
        switch.sendcmd("reload", spaceflag=False, timeout=0.5)
        switch.sendcmd("Y")
        switch.tn.read_until(b"HA batch backup has finished!", timeout=120)
        msg = switch.sendcmd("show slot", logflag=True)
        res = re.findall(r"Work mode\s+:\s(\S+)", msg)
        res_s = re.findall(r"Work state\s+:\s(\S+)", msg)
        if len(res) == 4:
            if res[0]=="ACTIVE" and res[1]=="STANDBY" and res[2]=="SLAVE" and res[3]=="SLAVE" and res_s[0]=="RUNNING" and res_s[1]=="RUNNING" and res_s[2]=="RUNNING" and res_s[3]=="RUNNING":
                log.info(u"第 %d 次重启成功" % i)
            else:
                log.info(u"第 %d 次重启失败" % i)
                break
        else:
            log.info(u"第 %d 次重启失败" % i)
            break
    switch.close()

def forceswitch_1U_VSF_repeatly(para):
    print("--------------forceswitch_1U_VSF_repeatly----------------")
    switch = open_device(para)
    for i in range(1, 1001):
        switch.changeview("enable")
        switch.sendcmd("force switchover", spaceflag=False, timeout=0.5)

        switch.sendcmd("Y")
        switch.tn.read_until(b"HA batch backup has finished!", timeout=120)
        msg = switch.sendcmd("show slot", logflag=True)
        res = re.findall(r"Work mode\s+:\s(\S+)", msg)
        res_s = re.findall(r"Work state\s+:\s(\S+)", msg)
        if len(res) == 4:
            if res[0]=="ACTIVE" and res[1]=="STANDBY" and res[2]=="SLAVE" and res[3]=="SLAVE" and res_s[0]=="RUNNING" and res_s[1]=="RUNNING" and res_s[2]=="RUNNING" and res_s[3]=="RUNNING":
                log.info(u"第 %d 次重启成功" % i)
            else:
                log.info(u"第 %d 次重启失败" % i)
                break
        else:
            log.info(u"第 %d 次重启失败" % i)
            break
    switch.close()

def affirm_4_56(para):
    print("affirm_4_56!")
    switch = open_device(para)
    for i in range(1, 200):
        print("----------------------------------", i ,"st-------------------------------------")
        #step 1
        switch.sendcmd("exit")
        print("******************step1 watchdog enable*******************")
        switch.sendcmd("******************step1 watchdog enable*******************")
        switch.changeview("enable")
        switch.changeview("config")
        switch.sendcmd("no vsf mac-address persistent", spaceflag=False, timeout=0.5)
        switch.sendcmd("watchdog enable", spaceflag=False, timeout=0.5)
        switch.changeview("enable")
        switch.sendcmd("terminal length 0")
        switch.sendcmd("su mem 2", spaceflag=False, timeout=0.5)
        switch.sendcmd("tshell debug call taskList", spaceflag=True, timeout=0.5)
        data = switch.tn.read_until(b"execute <debug call taskList> returned 0", timeout=60).decode("utf-8")
        taskname = "0x" + re.findall(r"tL2Input\sth:(\w+)\s", data)[0]
        # taskname ="0xe28c2b70"
        print("1-taskname = ",taskname)

       #step 2&3
        print("******************step2&3 kill tL2Input*******************")
        switch.sendcmd("******************step2&3 kill tL2Input*******************")
        switch.sendcmd("tshell debug call pthread_kill "+taskname+" 11", spaceflag=False, timeout=0.5)
        # switch.tn.read_until(b"interrupt: member 2, slot 1 PUSH IN.", timeout=60)
        switch.sendcmd("exit")
        time.sleep(60)
        flag=1
        while flag==1:
            msg = switch.sendcmd("show slot", logflag=False)
            res = re.findall(r"Work mode\s+:\s(\S+)", msg)
            res_s = re.findall(r"Work state\s+:\s(\S+)", msg)

            if len(res) == 4:
                if res_s[0] == "RUNNING" and res_s[1] == "RUNNING" and res_s[2] == "RUNNING" and res_s[3] == "RUNNING" :
                    flag=0
            time.sleep(10)
       #
       #
        #step 4
        print("******************step 4 watchdog disable*******************")
        switch.sendcmd("******************step 4 watchdog disable*******************")
        # switch.sendcmd("exit", spaceflag=False, timeout=0.5)
        switch.changeview("config")
        switch.sendcmd("watchdog disable", spaceflag=False, timeout=0.5)

        #step 5
        print("******************step 5 kill tL2Input*******************")
        switch.sendcmd("******************step 5 kill tL2Input*******************")
        switch.changeview("enable")
        switch.sendcmd("terminal length 0")
        switch.sendcmd("su mem 2", spaceflag=False, timeout=0.5)
        switch.sendcmd("tshell debug call taskList", spaceflag=False)
        # data = switch.tn.read_until(b"execute <debug call taskList> returned 0", timeout=60).decode("utf-8")
        # taskname = "0x" + re.findall(r"tL2Input\sth:(\w+)\s", data)[0]
        # taskname = "0x" +"e28c2b70"
        time.sleep(10)
        print("5-taskname = ", taskname)
        switch.sendcmd("tshell debug call pthread_kill " + taskname + " 11", spaceflag=False, timeout=0.5)
        # switch.tn.read_until(b"HA batch backup has finished!", timeout=120)
        # switch.tn.read_until(b"CS6580-48S6CQ-SI", timeout=60)
        time.sleep(10)
        # switch.changeview("enable")

        #step 6
        print("******************step 6 relaod*******************")
        switch.sendcmd("******************step 6 relaod*******************")
        switch.sendcmd("exit", spaceflag=False, timeout=0.5)
        switch.changeview("enable")
        switch.sendcmd("reload", spaceflag=False, timeout=0.5)
        switch.sendcmd("Y")
        switch.tn.read_until(b"HA batch backup has finished!")
        msg = switch.sendcmd("show slot", logflag=False)
        res = re.findall(r"Work mode\s+:\s(\S+)", msg)
        res_s = re.findall(r"Work state\s+:\s(\S+)", msg)
        if len(res) == 4:
            if res[0] == "ACTIVE" and res[1] == "STANDBY" and res[2] == "SLAVE" and res[3] == "SLAVE" and res_s[
                0] == "RUNNING" and res_s[1] == "RUNNING" and res_s[2] == "RUNNING" and res_s[3] == "RUNNING":
                log.info(u"第 %d 次重启成功" % i)
            else:
                log.info(u"第 %d 次重启失败" % i)
                break
        else:
            log.info(u"第 %d 次重启失败" % i)
            break

    switch.close()

def affirm_4_56_sof(para):
    print("affirm_4_56!")
    svstr="7.5.3.2(R0019.0057)"
    switch = open_device(para)
    for i in range(1, 200):
        print("----------------------------------", i ,"st-------------------------------------")
        #step 1
        switch.sendcmd("exit")
        print("******************step1 watchdog enable*******************")
        switch.sendcmd("******************step1 watchdog enable*******************")
        switch.changeview("enable")
        switch.changeview("config")
        switch.sendcmd("no vsf mac-address persistent", spaceflag=False, timeout=0.5)
        switch.sendcmd("watchdog enable", spaceflag=False, timeout=0.5)
        switch.changeview("enable")
        switch.sendcmd("terminal length 0")
        switch.sendcmd("su mem 2", spaceflag=False, timeout=0.5)
        switch.sendcmd("tshell debug call taskList", spaceflag=True, timeout=0.5)
        data = switch.tn.read_until(b"execute <debug call taskList> returned 0", timeout=60).decode("utf-8")
        taskname = "0x" + re.findall(r"tL2Input\sth:(\w+)\s", data)[0]
        # taskname ="0xe28c2b70"
        print("1-taskname = ",taskname)

       #step 2&3
        print("******************step2&3 kill tL2Input*******************")
        switch.sendcmd("******************step2&3 kill tL2Input*******************")
        switch.sendcmd("tshell debug call pthread_kill "+taskname+" 11", spaceflag=False, timeout=0.5)
        # switch.tn.read_until(b"interrupt: member 2, slot 1 PUSH IN.", timeout=60)
        switch.sendcmd("exit")
        time.sleep(60)
        flag=1
        while flag==1:
            msg = switch.sendcmd("show slot", logflag=False)
            res = re.findall(r"Work mode\s+:\s(\S+)", msg)
            res_s = re.findall(r"Work state\s+:\s(\S+)", msg)
            res_sversion1 = re.findall(r"Software package version\s+:\s(\S+)" , msg)
            res_sversion2 = re.findall(r"Local software version\s+:\s(\S+)",msg)
            res_sversionall=res_sversion1+res_sversion2
            if len(res) == 4:
                if res_s[0] == "RUNNING" and res_s[1] == "RUNNING" and res_s[2] == "RUNNING" and res_s[3] == "RUNNING":
                    flag=0
            if len(res_sversionall)==4:
                if res_sversionall[0] == svstr and res_sversionall[1] == svstr \
                        and res_sversionall[2] == svstr and res_sversionall[3] == svstr:
                    flag=0
            time.sleep(10)
       #
       #
        # #step 4
        # print("******************step 4 watchdog disable*******************")
        # switch.sendcmd("******************step 4 watchdog disable*******************")
        # # switch.sendcmd("exit", spaceflag=False, timeout=0.5)
        # switch.changeview("config")
        # switch.sendcmd("watchdog disable", spaceflag=False, timeout=0.5)
        #
        # #step 5
        # print("******************step 5 kill tL2Input*******************")
        # switch.sendcmd("******************step 5 kill tL2Input*******************")
        # switch.changeview("enable")
        # switch.sendcmd("terminal length 0")
        # switch.sendcmd("su mem 2", spaceflag=False, timeout=0.5)
        # switch.sendcmd("tshell debug call taskList", spaceflag=False)
        # # data = switch.tn.read_until(b"execute <debug call taskList> returned 0", timeout=60).decode("utf-8")
        # # taskname = "0x" + re.findall(r"tL2Input\sth:(\w+)\s", data)[0]
        # # taskname = "0x" +"e28c2b70"
        # time.sleep(10)
        # print("5-taskname = ", taskname)
        # switch.sendcmd("tshell debug call pthread_kill " + taskname + " 11", spaceflag=False, timeout=0.5)
        # # switch.tn.read_until(b"HA batch backup has finished!", timeout=120)
        # # switch.tn.read_until(b"CS6580-48S6CQ-SI", timeout=60)
        # time.sleep(10)
        # # switch.changeview("enable")

        #step 6
        print("******************step 6 relaod*******************")
        switch.sendcmd("******************step 6 relaod*******************")
        switch.sendcmd("exit", spaceflag=False, timeout=0.5)
        switch.changeview("enable")
        switch.sendcmd("reload", spaceflag=False, timeout=0.5)
        switch.sendcmd("Y")
        switch.tn.read_until(b"HA batch backup has finished!")
        msg = switch.sendcmd("show slot", logflag=False)
        res = re.findall(r"Work mode\s+:\s(\S+)", msg)
        res_s = re.findall(r"Work state\s+:\s(\S+)", msg)
        res_sversion = re.findall(r"Software package version\s+:\s(\S+)" or r"Local software version\s+:\s(\S+)", msg)
        if len(res) == 4:
            if res[0] == "ACTIVE" and res[1] == "STANDBY" and res[2] == "SLAVE" and res[3] == "SLAVE" and res_s[
                0] == "RUNNING" and res_s[1] == "RUNNING" and res_s[2] == "RUNNING" and res_s[3] == "RUNNING":
                log.info(u"第 %d 次重启成功" % i)
            else:
                log.info(u"第 %d 次重启失败" % i)
                break
        else:
            log.info(u"第 %d 次重启失败" % i)
            break

    switch.close()

#8-reset_member_slot
def reset_member_slot(para):
    print("----------reset_member_slot-------------")
    switch = open_device(para)
    timeinit=time.time()
    print("start time = ",timeinit)
    switch.changeview("enable")
    switch.sendcmd("terminal length 0", spaceflag=False, timeout=0.5)
    switch.changeview("config")
    switch.sendcmd("exec-timeout 0", spaceflag=False, timeout=0.5)
    time.sleep(2)
    msg = switch.sendcmd("show slot", logflag=False)
    res = re.findall(r"Work state\s+:\s(\S+)", msg)
    lres_init=len(res)
    for i in range(1, 60):
        switch.changeview("enable")
        switch.sendcmd("reset member 2 slot 15", spaceflag=False, timeout=0.5)
        switch.tn.read_until(b"HA batch backup has finished!")
        switch.sendcmd("\n\n\n")
        time.sleep(2)
        msg = switch.sendcmd("show slot", timeout=20, logflag=False)
        res = re.findall(r"Work state\s+:\s(\S+)", msg)
        lres=len(res)
        if lres!=lres_init:
            log.info(u"第 %d 次重启失败1" % i)
            break
        elif len(set(res))!=1 or res[0]!="RUNNING":
            log.info(u"第 %d 次重启失败2" % i)
            break
        else:
            log.info(u"第 %d 次重启成功" % i)
        timediff=time.time()-timeinit
        if timediff >= 12*60*60:
            print("exectime = ",int(timediff/60/60),"h")
            log.info("-----end because of time over----------")
            break
    switch.close()

def shutdown_vsfport(para):
    print("----------shutdown_vsfport-------------")
    switch = open_device(para)
    timeinit = time.time()
    print("start time = ", timeinit)
    switch.changeview("enable")
    switch.sendcmd("terminal length 0", spaceflag=False, timeout=0.5)
    switch.changeview("config")
    switch.sendcmd("exec-timeout 0", spaceflag=False, timeout=0.5)
    time.sleep(2)
    msg = switch.sendcmd("show slot", logflag=False)
    res = re.findall(r"Work state\s+:\s(\S+)", msg)
    lres_init = len(res)
    for i in range(1, 60):
        switch.changeview("config")
        switch.sendcmd("interface ethernet 1/7/21", spaceflag=False, timeout=0.5)
        switch.sendcmd("shutdown", spaceflag=False, timeout=0.5)
        switch.tn.read_until(b"HA batch backup has finished!")
        switch.sendcmd("\n\n\n")
        time.sleep(2)
        msg = switch.sendcmd("show slot", timeout=20, logflag=False)
        res = re.findall(r"Work state\s+:\s(\S+)", msg)
        lres = len(res)
        if lres != lres_init:
            log.info(u"第 %d 次重启失败1" % i)
            break
        elif len(set(res)) != 1 or res[0] != "RUNNING":
            log.info(u"第 %d 次重启失败2" % i)
            break
        else:
            log.info(u"第 %d 次重启成功" % i)
        timediff = time.time() - timeinit
        if timediff >= 12 * 60 * 60:
            print("exectime = ", int(timediff / 60 / 60), "h")
            log.info("-----end because of time over----------")
            break
    switch.close()

def reset_other_slot(para):
    print("----------reset_member_slot-------------")
    switch = open_device(para)
    timeinit=time.time()
    print("start time = ",timeinit)
    switch.changeview("enable")
    switch.sendcmd("terminal length 0", spaceflag=False, timeout=0.5)
    switch.changeview("config")
    switch.sendcmd("exec-timeout 0", spaceflag=False, timeout=0.5)
    time.sleep(2)
    msg = switch.sendcmd("show slot", logflag=False)
    res = re.findall(r"Work state\s+:\s(\S+)", msg)
    lres_init=len(res)
    for i in range(1, 60):
        switch.changeview("enable")
        switch.sendcmd("reset member 2 slot 13", spaceflag=False, timeout=0.5)
        switch.tn.read_until(b" Line protocol on Interface Ethernet1/13/24, changed state to DOWN")
        switch.sendcmd("\n\n\n")
        time.sleep(2)
        msg = switch.sendcmd("show slot", timeout=20, logflag=False)
        res = re.findall(r"Work state\s+:\s(\S+)", msg)
        lres=len(res)
        if lres!=lres_init:
            log.info(u"第 %d 次重启失败1" % i)
            break
        elif len(set(res))!=1 or res[0]!="RUNNING":
            log.info(u"第 %d 次重启失败2" % i)
            break
        else:
            log.info(u"第 %d 次重启成功" % i)
        timediff=time.time()-timeinit
        if timediff >= 12*60*60:
            print("exectime = ",int(timediff/60/60),"h")
            log.info("-----end because of time over----------")
            break
    switch.close()

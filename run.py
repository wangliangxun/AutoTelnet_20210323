from case import *


DUT = DCRS_9816
indicates = ["0--单元测试",
             "1--向控制台发送Ctrl+B",
             "2--查看接口速率",
             "3--查看CPU/内存使用率",
             "4--通过ftp反复升降级img",
             "5--反复重启堆叠环境",
             "6--affirm 4.56",
             "7--affirm_4_56_sof",
             "8--reset_member_slot"]
print("\n".join(indicates))
#action = input(u"请输入要执行的操作：")
action ='8'
if action == "0":
    unit_test(DUT)
elif action == "1":
    send_ctrl_b(DUT)
elif action == "2":
    check_int_rate(DUT)
elif action == "3":
    check_cpu_mem(DUT)
elif action == "4":
    upgrade_byftp(DUT)
elif action == "5":
    reload_1U_VSF_repeatly(DUT)
elif action == "6":
    affirm_4_56(DUT)
elif action == "7":
    affirm_4_56_sof(DUT)
elif action == "8":
    reset_member_slot(DUT)
elif action=="9":
    shutdown_vsfport(DUT)
elif action == "10":
    reset_other_slot(DUT)
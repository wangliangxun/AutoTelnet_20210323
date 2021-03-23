import re
import time


# 接口字符串转化为列表
def port_str_to_array(port_id):
    reg = re.match(r"(\d+/\d+/)(\S+)", port_id)
    prefix, ports = reg.group(1), reg.group(2)
    port_array = []
    for i in ports.split(";"):
        if "-" not in i:
            port_array.append(prefix+i)
        else:
            tmp = re.findall(r"(\d+)", i)
            port_array += [prefix+str(j) for j in range(int(tmp[0]), int(tmp[1])+1)]
    return port_array


# 接口列表转化为命令行字符串
def port_array_to_str(port_list):
    ports = re.findall(r"(\d+/\d+/)(\d+)", ";".join(port_list))
    port_map = {}
    for port in ports:
        if port[0] not in port_map:
            port_map[port[0]] = [int(port[1])]
        else:
            port_map[port[0]].append(int(port[1]))
    result = ""
    for prefix, nums in port_map.items():
        port_num = sorted(set(nums))
        port_str = str(port_num[0])
        for i in range(1, len(port_num)):
            if port_num[i] == port_num[i-1]+1:
                if "-"+str(port_num[i-1]) not in port_str:
                    port_str += "-%d" % port_num[i]
                else:
                    port_str = port_str.replace(str(port_num[i-1]), str(port_num[i]))
            else:
                port_str += ";%d" % port_num[i]
        result += "%s%s、" % (prefix, port_str)
    return result[:-1]


# 传入原始数据，返回字典结构的端口及对应的速率或包数
def get_rate_or_packet(data, norm="rate"):
    data = re.sub(r",", "", data)
    cooked_data1 = re.findall(r"(\d+/\d+/\d+)\s+[IN5m]{2}\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", data)
    cooked_data2 = re.findall(r"[OUT5s]{2,3}\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", data)
    result1, result2 = {}, {}
    if norm == "rate":
        index = ["IN(pkts/s)", "IN(bits/s)", "OUT(pkts/s)", "OUT(bits/s)"]
        for i in range(len(cooked_data1)):
            result1[cooked_data1[i][0]] = dict(zip(index, [int(j) for j in cooked_data1[i][1:]]))
            result2[cooked_data1[i][0]] = dict(zip(index, [int(j) for j in cooked_data2[i]]))
    else:
        index = ["Unicast(pkts)", "BroadCast(pkts)", "MultiCast(pkts)", "Err(pkts)"]
        for i in range(len(cooked_data1)):
            result1[cooked_data1[i][0]] = dict(zip(index, [int(j) for j in cooked_data1[i][1:]]))
            result2[cooked_data1[i][0]] = dict(zip(index, [int(j) for j in cooked_data2[i]]))
    return result1, result2


def compare_data(data1, data2, tolerance):
    if data1 == 0 or data2 == 0:
        ratio = tolerance - 1
    else:
        ratio = abs(data1-data2)/data1*100
    return False if ratio <= tolerance else True


def generate_ipaddr(num):
    third = num % 256
    second = num // 256
    return "210.%d.%d.1" % (second, third)


def generate_ip6addr(num):
    pass


def generate_checksum(data):
    pass



if __name__ == "__main__":
    # a = "1;20"
    # print(port_id_to_array(""))
    print(port_str_to_array("1/0/25-26"))
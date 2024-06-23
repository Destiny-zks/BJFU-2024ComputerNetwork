from socket import *
import sys
import struct
import time

if len(sys.argv) != 3:
    print("请正确输入目的IP地址和端口号")
    sys.exit(1)

serverIP = sys.argv[1]
serverPort = int(sys.argv[2])

clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.settimeout(0.1)  # 设置超时时间为100ms

version = 2
max_resends = 2

in_packets = 0
out_packets = 0

min_rtt = float('inf')
max_rtt = 0.0000
sum_rtt = 0

number = 12

beginning_time = 0


# 定义报文格式编码函数
def encode_message(seq_no, ver, msg_type, data):
    time_filler = "Marshiro"  # Client不发时间该处用无意义字母序列填充
    header = struct.pack('!HB3s8s', seq_no, ver, msg_type.encode('utf-8'), time_filler.encode('utf-8'))
    return header + data.encode()


# 定义报文格式解码函数
def decode_message(message):
    header = struct.unpack('!HB3s8s', message[:14])
    data = message[14:].decode()
    return {
        "seq_no": header[0],
        "ver": header[1],
        "type": header[2].decode('utf-8'),
        "server_time": header[3].decode('utf-8'),
        "data": data
    }


# 模拟三次握手
seq_no = 1
msg_type = "SYN"
enco_message = encode_message(seq_no, version, msg_type, '')
clientSocket.sendto(enco_message, (serverIP, serverPort))
resend_times = 0
while resend_times < max_resends:
    try:
        data, server_address = clientSocket.recvfrom(1024)
        deco_message = decode_message(data)
        if deco_message['type'] == 'ACK':
            seq_no += 1
            ack_message = encode_message(seq_no, version, 'ACK', '')
            clientSocket.sendto(ack_message, (serverIP, serverPort))
            print("成功与服务器建立连接")
            break
    except timeout:
        resend_times += 1
        print(f"发生超时 第 {resend_times} 次重传SYN")
        clientSocket.sendto(enco_message, (serverIP, serverPort))
else:
    print("未能与服务器建立连接")
    clientSocket.close()
    sys.exit(1)

# 进入数据传输阶段
seq_no = 1
for i in range(12):
    resend_times = 0
    message_data = f"Request {i + 1}"
    data_message = encode_message(seq_no, version, 'MSG', message_data)
    start_time = time.time()  # 记录发送时间
    clientSocket.sendto(data_message, (serverIP, serverPort))
    out_packets += 1
    if i == 0:
        beginning_time = start_time

    while resend_times < max_resends:
        try:
            data, server_address = clientSocket.recvfrom(1024)
            end_time = time.time()  # 记录接收时间
            rtt = end_time * 1000 - start_time * 1000  # 计算RTT，单位为毫秒
            min_rtt = min(min_rtt, rtt)
            max_rtt = max(max_rtt, rtt)
            sum_rtt += rtt
            in_packets += 1
            deco_message = decode_message(data)
            if deco_message['type'] == 'MSG':
                print(f"sequence no{seq_no}, {server_address}, RTT = {rtt} ms")
                seq_no += 1
                break
        except timeout:
            print(f"sequence no{seq_no}, request time out")
            clientSocket.sendto(data_message, (serverIP, serverPort))
            out_packets += 1
            resend_times += 1
    else:
        print("重传两次也未收到回复")
        number -= 1
        seq_no += 1

# 输出汇总信息
loss_rate = float((1 - in_packets / out_packets)) * 100
average_rtt = sum_rtt / number
print(f"udp packets:{in_packets}")
print(f"丢包率:{loss_rate}%")
print(f"最大rtt:{max_rtt}     最小rtt:{min_rtt}")
print(f"平均rtt:{average_rtt:.2f}ms")
print(f"server的整体响应时间:{(end_time - beginning_time) * 1000}ms")


# 模拟四次挥手
# 客户端发送FIN
fin_message = encode_message(seq_no, version, 'FIN', '')
clientSocket.sendto(fin_message, (serverIP, serverPort))
while True:
    try:
        data, server_address = clientSocket.recvfrom(1024)
        deco_message = decode_message(data)
        if deco_message['type'] == 'ACK':
            seq_no += 1
            break
    except timeout:
        resend_times += 1
        clientSocket.sendto(fin_message, (serverIP, serverPort))

# 接收服务器的FIN
while True:
    try:
        data, server_address = clientSocket.recvfrom(1024)
        deco_message = decode_message(data)
        if deco_message['type'] == 'FIN':
            ack_message = encode_message(seq_no, version, 'ACK', '')
            clientSocket.sendto(ack_message, (serverIP, serverPort))
            print("连接已关闭")
            break
    except timeout:
        pass

clientSocket.close()

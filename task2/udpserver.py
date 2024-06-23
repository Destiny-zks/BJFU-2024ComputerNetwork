from socket import *
import random
import time
import struct

serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('localhost', serverPort))
print("服务已启动")

drop_rate = 0.2  # 丢包率，可以调整
Flag = 0

# 定义报文格式解码函数
def decode_message(message):
    header = struct.unpack('!HB3s8s', message[:14])
    data = message[14:].decode()
    return {
        "seq_no": header[0],
        "ver": header[1],
        "type": header[2].decode('utf-8'),
        "time": header[3].decode('utf-8'),
        "data": data
    }


# 定义报文格式编码函数
def encode_message(seq_no, ver, msg_type, data):
    server_time = time.strftime('%H:%M:%S')  # 获取当前时间，格式为HH:MM:SS
    header = struct.pack('!HB3s8s', seq_no, ver, msg_type.encode('utf-8'), server_time.encode('utf-8'))
    return header + data.encode()


while True:
    data, client_address = serverSocket.recvfrom(1024)
    message = decode_message(data)

    # 模拟丢包
    if random.random() < drop_rate:
        continue

    if message['type'] == 'SYN':
        seq_no = message['seq_no']
        syn_ack_message = encode_message(seq_no, message['ver'], 'ACK', '')
        serverSocket.sendto(syn_ack_message, client_address)

    elif message['type'] == 'ACK':
        if Flag == 0:
            print(f"三次握手完毕，与 {client_address} 连接已经建立")
        else:
            print("连接已关闭")

    elif message['type'] == 'MSG':
        seq_no = message['seq_no']
        data_message = encode_message(seq_no, message['ver'], 'MSG', f"{message['data']}")
        serverSocket.sendto(data_message, client_address)

    elif message['type'] == 'FIN':
        Flag = 1
        seq_no = message['seq_no']
        syn_ack_message = encode_message(seq_no, message['ver'], 'ACK', '')
        serverSocket.sendto(syn_ack_message, client_address)
        syn_ack_message = encode_message(seq_no + 1, message['ver'], 'FIN', '')
        serverSocket.sendto(syn_ack_message, client_address)

serverSocket.close()
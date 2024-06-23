from socket import *
import sys
import struct
import random

if len(sys.argv) != 5:
    print("请正确输入目的IP地址 端口号 最小长度 最大长度")
    sys.exit(1)

serverIP = sys.argv[1]
serverPort = int(sys.argv[2])
Lmin = int(sys.argv[3])
Lmax = int(sys.argv[4])

# 文件路径固定为当前目录中的File.txt
file_path = 'File.txt'

# 读取文件内容
try:
    with open(file_path, 'r') as file:
        file_content = file.read()
except FileNotFoundError:
    print("文件未找到，请检查文件路径")
    sys.exit(1)

# 计算文件长度
file_length = len(file_content)

blocks = []
total_length = 0

# 实现块随机截取
while total_length < file_length:
    block_length = random.randint(Lmin, Lmax)
    if total_length + block_length > file_length:
        block_length = file_length - total_length
    blocks.append(block_length)
    total_length += block_length

# 计算块数
N = len(blocks)
print(f'总块数: {N}')

clientSocket = socket(AF_INET, SOCK_STREAM)


# 定义报文格式编码函数
def encode_message(type, length, data):
    header = struct.pack('!HI', type, length)
    return header + data.encode()


# 定义报文格式解码函数
def decode_message(message):
    header = struct.unpack('!HI', message[:6])
    data = message[6:].decode()
    return {
        "type": header[0],
        "length": header[1],
        "data": data
    }


# 连接服务器
try:
    clientSocket.connect((serverIP, serverPort))
    print(f'连接到 {serverIP} 的 {serverPort} 端口')

    # 发送Initialization
    encoded_message = encode_message(1, N, '')
    clientSocket.sendall(encoded_message)

    # 等待服务器回应agreement
    try:
        data = clientSocket.recv(1024)
        decoded_message = decode_message(data)

        if decoded_message['type'] == 2:
            print("成功接收到服务器agreement")

        # 发送要反转的内容
        start = 0
        for i, block_length in enumerate(blocks):
            end = start + block_length
            chunk = file_content[start:end]

            # 编码消息
            encoded_message = encode_message(3, block_length, chunk)

            # 发送块数据
            clientSocket.sendall(encoded_message)
            print(f'发送长度为 {len(chunk)} 数据块（{i + 1}/{N}） : {chunk[:50]}')

            # 等待服务器响应
            try:
                data = clientSocket.recv(1024)
                decoded_message = decode_message(data)
                print('收到反转后的数据块:', decoded_message['data'])

            except Exception as e:
                print("未能接收到服务器的回应:", e)

            start = end

    except Exception as e:
        print("未能接收到服务器的回应:", e)

except Exception as e:
    print("连接服务器失败:", e)

finally:
    # 清理连接
    clientSocket.close()

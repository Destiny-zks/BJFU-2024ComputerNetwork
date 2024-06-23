from socket import *
import select
import sys
import struct

serverIP = '0.0.0.0'  # 监听所有接口
serverPort = 12000

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind((serverIP, serverPort))
serverSocket.listen(5)

inputs = [serverSocket]
outputs = []
message_queues = {}


# 定义报文格式解码函数
def decode_message(message):
    header = struct.unpack('!HI', message[:6])
    data = message[6:].decode()
    return {
        "type": header[0],
        "length": header[1],
        "data": data
    }


while inputs:
    readable, writable, exceptional = select.select(inputs, outputs, inputs)

    for s in readable:
        if s is serverSocket:
            # 新连接
            connection, clientAddress = s.accept()
            print(f"接受来自 {clientAddress} 的连接")
            connection.setblocking(0)  # 设置为非阻塞
            inputs.append(connection)
            message_queues[connection] = b''  # 初始化消息队列

        else:
            # 有数据可读
            data = s.recv(1024)
            if data:
                # 收到数据
                decoded_message = decode_message(data)
                if decoded_message['type'] == 1:
                    print(f"收到来自 {s.getpeername()} 的Initialization")
                    header = struct.pack('!HI', 2, decoded_message['length'])
                    answer_data = header + data
                    message_queues[s] += answer_data
                    if s not in outputs:
                        outputs.append(s)
                elif decoded_message['type'] == 3:
                    print(f"收到来自 {s.getpeername()} 的数据:", decoded_message['data'])
                    # 编码数据，并修改 type 字段为 4，将数据反转
                    header = struct.pack('!HI', 4, decoded_message['length'])
                    reversed_data = header + data[6:][::-1]  # 将前6字节的type字段变为3，保持length不变，其余数据反转
                    message_queues[s] += reversed_data
                    if s not in outputs:
                        outputs.append(s)
            else:
                # 客户端断开连接
                print(f"客户端 {s.getpeername()} 断开连接")
                if s in outputs:
                    outputs.remove(s)
                inputs.remove(s)
                s.close()
                del message_queues[s]

    for s in writable:
        try:
            next_msg = message_queues[s]
            s.send(next_msg)
            message_queues[s] = b''  # 清空消息队列
            outputs.remove(s)
        except Exception as e:
            print("发送数据时发生错误:", e)
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()
            del message_queues[s]

    for s in exceptional:
        print("发生异常:", s.getpeername())
        inputs.remove(s)
        if s in outputs:
            outputs.remove(s)
        s.close()
        del message_queues[s]

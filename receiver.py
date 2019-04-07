import sys
from socket import *
from packet import *
import time

def sendPacket(packet, server_name, server_port):
    print('sending ack: ' + str(packet.getSeqNum()))
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.sendto(Packet.getUDPdata(packet), (server_name, server_port))

if __name__ == '__main__':
    if len(sys.argv) != 5:
        exit('Error! Please provide 4 arguments')
    else:
        emu_host_addr = sys.argv[1]
        emu_udp_receive_acks = int(sys.argv[2])
        receiver_udp_port = int(sys.argv[3])
        file_name = sys.argv[4]

    file = open(file_name, 'w')
    arrival_file = open('arrival.log', 'w')

    recv_socket = socket(AF_INET, SOCK_DGRAM)
    recv_socket.bind(('', receiver_udp_port))
    expected_seq_num = 0
    packet_zero = False

    while True:
        data, address = recv_socket.recvfrom(4096)
        unpacked_data = Packet.parseUDPdata(data)
        data_seq_num = unpacked_data.getSeqNum()

        print('expecting ' + str(expected_seq_num%32) + ' ' + 'received ' + str(data_seq_num))
        arrival_file.write(str(data_seq_num) + '\n')

        # got expected seq_num
        if data_seq_num == expected_seq_num % 32:
            packet_zero = True
            ack_packet = Packet.createACK(expected_seq_num % 32)
            expected_seq_num += 1
            if unpacked_data.getType() == 1:
                file.write(unpacked_data.getData())

        # still waiting for first packet
        elif packet_zero is False:
            continue

        # did not receive expected seq_num
        elif data_seq_num != expected_seq_num % 32:
            ack_packet = Packet.createACK(expected_seq_num % 32 - 1)
        # received EOT
        if unpacked_data.getType() == 2:
            ack_packet = Packet.createEOT(expected_seq_num % 32)

        sendPacket(ack_packet, emu_host_addr, emu_udp_receive_acks)
    file.close()

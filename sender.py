import sys
import time
from socket import *
from packet import *

def read_in_chunks(file_object):
    while True:
        data = file_object.read(500)
        if not data:
            break
        yield data

def sendPacket(packet, server_name, server_port):
    print('sending: ' + str(packet.getSeqNum()))
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.sendto(Packet.getUDPdata(packet), (server_name, server_port))

def get_acks_receive(sender_udp_receive_ack):
    ackSocket = socket(AF_INET, SOCK_DGRAM)
    ackSocket.bind(('', sender_udp_receive_ack))
    ackSocket.settimeout(0.1)

    try:
        data, address = ackSocket.recvfrom(4096)
        unpacked_data = Packet.parseUDPdata(data)
        received_seq_ack = unpacked_data.getSeqNum()
        ackSocket.close()
        return received_seq_ack

    except timeout:
        ackSocket.close()
        return -1

def get_eot_receive(sender_udp_receive_ack):
    ackSocket = socket(AF_INET, SOCK_DGRAM)
    ackSocket.bind(('', sender_udp_receive_ack))

    data, address = ackSocket.recvfrom(4096)
    unpacked_data = Packet.parseUDPdata(data)
    received_eot = unpacked_data.getType()
    ackSocket.close()
    return received_eot

if __name__ == '__main__':
    if len(sys.argv) != 5:
        exit('Error! Please provide 4 arguments')
    else:
        emu_host_addr = sys.argv[1]
        emu_udp_from_sender = int(sys.argv[2])
        sender_udp_receive_ack = int(sys.argv[3])
        file_name = sys.argv[4]

        file = open(file_name, 'r')
        seq_file = open('seqnum.log', 'w')
        ack_file = open('ack.log', 'w')

        data_pieces = []
        for data_piece in read_in_chunks(file):
            data_pieces.append(data_piece)

        buffer_stack = []
        buffer_size = 10
        next_seq_num = 0
        all_sent = False
        base = 0
        received_ack = None

        while not all_sent or buffer_stack:
            if (next_seq_num % 32 < base + buffer_size) and not all_sent:
		        # only send new packets if last received_ack is 31
                if next_seq_num % 32 != 0 or (next_seq_num % 32 == 0 and (received_ack is None or received_ack == 31)):
                    new_packet = Packet.createPacket(next_seq_num%32, data_pieces[next_seq_num])
                    sendPacket(new_packet, emu_host_addr, emu_udp_from_sender)
                    seq_file.write(str(new_packet.getSeqNum()) + '\n')
                    next_seq_num += 1
                    buffer_stack.append(new_packet)

		    # all packets sent
            if next_seq_num >= len(data_pieces) or (not data_pieces[next_seq_num]):
                all_sent = True

            # get acks
            received_ack = get_acks_receive(sender_udp_receive_ack)
            print('received ack: ' + str(received_ack))
            ack_file.write(str(received_ack) + '\n')

	        # timeout
            if received_ack == -1:
                # resend everything in buffer
                for i in buffer_stack:
                    sendPacket(i, emu_host_addr, emu_udp_from_sender)
                    seq_file.write(str(i.getSeqNum()) + '\n')

            # reset base to be 0 once we receive ack for 31
            elif received_ack == 31:
                base = 0

            # adjust base to be equal to ack and remove packets from buffer
            else:
                while received_ack > base and len(buffer_stack) > 0:
                    buffer_stack.pop(0)
                    base += 1
            print('base: ' + str(base))
            if all_sent is True:
                break

    	# all packets sent; send EOT
    	eot_packet = Packet.createEOT(next_seq_num)
    	sendPacket(eot_packet, emu_host_addr, emu_udp_from_sender)
        seq_file.write(str(eot_packet.getSeqNum()))

    	# wait for EOT from receiver
    	while True:
            received_type = get_eot_receive(sender_udp_receive_ack)
            if received_type == 2:
                file.close()
                seq_file.close()
                ack_file.close()
            break

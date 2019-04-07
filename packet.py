import struct

class Packet():
    def __init__(self, type, seq_num, str_data):
        if len(str_data) > 500:
            print("data too large (max 500 chars)")
            exit()
        self.type = type
        self.seqnum = seq_num % 32
        self.data = str_data

    @staticmethod
    def createACK(seq_num):
        return Packet(0, seq_num, '')

    @staticmethod
    def createPacket(seq_num, data):
        return Packet(1, seq_num, data)

    @staticmethod
    def createEOT(seq_num):
        return Packet(2, seq_num, '')

    def getType(self):
        return self.type

    def getSeqNum(self):
        return self.seqnum

    def getLength(self):
        return len(self.data)

    def getData(self):
        return self.data

    def getUDPdata(self):
        packed_struct = struct.pack('!iii' + str(len(self.data)) + 's', self.type, self.seqnum, len(self.data), self.data)
        return packed_struct

    @staticmethod
    def parseUDPdata(udp_data):
       data_len = len(udp_data) - 12
       type_num, seq_num, data_length, str_data = struct.unpack('!iii' + str(data_len) + 's', udp_data)
       str_data = str_data[0:data_length]
       return Packet(type_num, seq_num, str_data)

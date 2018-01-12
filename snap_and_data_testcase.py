import os
import re
import string

class Units:
    unit = ["Byte","KB","MB","GB","TB","PB","EB"]
    unit2 = {"m":"MB","k":"KB","g":"GB"}
    pows = {"EB" : pow(1024,6),
        "PB" : pow(1024,5),
        "TB" : pow(1024,4),
        "GB" : pow(1024,3),
        "MB" : pow(1024,2),
        "KB" : pow(1024,1),
        "Byte" : pow(1024,0)}

    def __init__(self, size):
        m = re.match('([0-9.]+)([a-zA-z]+)',size)
        val = m.group(1)
        unit = m.group(2)
        self.byte_size = float(val) * Units.pows[unit]

    def __getattr__(self, attr):
        if attr in map(string.lower, Units.unit2.keys()): 
            attr = Units.unit2[attr.lower()]
        if attr not in Units.unit: return None
        return self.__convert(self.byte_size, attr) 

    def __convert(self, byte_size, attr):
        size = self.__convert_size(byte_size, attr)
        if float("%.2f" % size).is_integer(): return '%d%s' % (size, attr) 
        return "%.2f%s" % (size, attr)

    def __convert_size(self, byte_size, attr):
        d = Units.pows[attr]
        size = byte_size / d
        return size

    def __str__(self):
        for u in Units.unit:
            size = self.__convert_size(self.byte_size, u)
            if size < 1024: return getattr(self, u)


def run(cmd):
    return os.popen(cmd).read()

def generate_data(letter, blocksize):
    m = re.match('([0-9.]+)([a-zA-Z]+)', Units(blocksize).Byte)
    size = int(m.group(1))
    in_data = "%s" % letter * size 
    with open("%s" % letter,"w+") as f:
        f.write(in_data)

def write_data(letter, offset, dev, blocksize):
    """
    :param offset: int type , offset is seek from blocksize
    :param offset: /dev/rbd0, or /dev/sdb
    :param blocksize: dd bs=1M
    """
    dev = "/dev/" + dev
    cmd = "dd if=./%s of=%s seek=%s bs=%s count=1" % (letter, dev, offset, blocksize)
    run(cmd)

if __name__ == "__main__":
    for i in ["A","B","C","D"]:
        write_data(i, 1, "rbd2", "1m")



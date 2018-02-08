import re
import sys
import logging
from .utils import run

_logger = logging.getLogger(__name__)



class Sds:
    engine_path = "/opt/sandstone/bin/sds "
    om_path     = "/opt/sdsom/" 

    def __init__(self):
        pass

    def bcache_quote(self):
        cmd = "cat /sys/fs/bcache/$(/opt/sandstone/sbin/sdscache_ctl -q \
        /dev/sdb2 | grep cset.uuid | awk '{print $2}')/cache0/priority_stats"
        return run(cmd)

    def osd_df(self, a):
        cmd = self.engine_path + "osd df | sort -nk 6"
        print a 
        return run(cmd)
    
    def osd_tree(self):
        cmd = self.engine_path + "osd tree"
        return run(cmd)

    def osd_pool_create(self, poolname, pg_num=512):
        cmd = self.engine_path + poolname + pg_num
        return run(cmd)

    def flashcache_stat(self):
        cmd = "/opt/sandstone/sbin/sdscache_stat -d /dev/mapper/"
        return run(cmd)




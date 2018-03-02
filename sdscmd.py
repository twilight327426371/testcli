import re
import sys
import logging

from .utils import run
from .decorator import options, make_opt, CmdError

_logger = logging.getLogger(__name__)


class Sds:
    engine_path, om_path  = ["/opt/sandstone/bin/sds ", "/opt/sdsom/"]
    orders = "up|down".split("|")

    def check_order(order):
        if order not in Sds.orders: raise CmdError('Only support order "up" or "down"')

    def error_suggest():
        return ["Available parameters:",
                "up     sort by $use from larger to small",
                "down   sort by $use from small to larger"]

    def bcache_quote(self):
        cmd = "cat /sys/fs/bcache/$(/opt/sandstone/sbin/sdscache_ctl -q \
        /dev/sdb2 | grep cset.uuid | awk '{print $2}')/cache0/priority_stats"
        return run(cmd)
    
    @options(make_opt("order", nokey=True, check=check_order, suggest=error_suggest))
    def osd_df(self, order):
        cmd = self.engine_path + "osd df | sort -nk 6"
        print order
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




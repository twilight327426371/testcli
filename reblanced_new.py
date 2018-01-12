# -*- coding: utf-8 -*-
import subprocess
from copy import deepcopy
import os
import re
import json
import logging
import logging.config
import pickle
import time
import sys
from colors import red,green
from datetime import datetime

logging.config.fileConfig("logger.conf")
logger = logging.getLogger("example01") 




def createDaemon(fn):
    def _createDaemon(*arg,**kwargs):
        # fork����        
        try:
            if os.fork() > 0: os._exit(0)
        except OSError, error:
            logging.error(red('fork #1 failed: %d (%s)' % (error.errno, error.strerror)))
            os._exit(1)    
        try:
            pid = os.fork()
            if pid > 0:
                logging.info('Daemon PID %d' % pid)
                os._exit(0)
        except OSError, error:
            logging.error(red('fork #2 failed: %d (%s)' % (error.errno, error.strerror)))
            os._exit(1)
        # �ض����׼IO
        sys.stdout.flush()
        sys.stderr.flush()
        si = file("/dev/null", 'r')
        so = file("/dev/null", 'a+')
        se = file("/dev/null", 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
        fn(*arg,**kwargs)
    return _createDaemon


def run_cmd(cmd):
    args = cmd.split(' ')
    run = subprocess.Popen(args,
                           close_fds=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    if 'test.sh' not in args:
        logging.info(args)
    stdout,stderr = run.communicate(input=None)
    #if stderr:
        #print "err: ",stderr
    return stdout

def operations(fn):
    def _operations(*args,**kwargs):
        for i in range(1,int(kwargs['exec_times'])+1):
            logging.info(green("exec %s function, %d times!"%(fn.__name__,i)))
            fn(*args,**kwargs)
    return _operations

class BlancePg(object):
    head = '/opt/sandstone/bin/sds '
    new_head = '/root/osdmaptool '
    def __init__(self):
        #self.osd_tree=BlancePg.head + 'osd tree -f json'
        #self.pg_stat=BlancePg.head + "pg stat --format json"
        #self.osd_crush_reweight=BlancePg.head + "osd crush reweight %s %s"
        self.osd_crush_reweight=BlancePg.new_head + "osd reweight %s %s"
        self.df=BlancePg.head + 'df -f json'
        self.osdmap = BlancePg.new_head + "osdmap --dump_osdmap"

    @property
    def osd2pg(self):
        out = run_cmd('sh t.sh')
        poolid=self.poolid
        def parse_pg_maps(out,poolid):
            osdinfo=[]
            default=0
            for i in out.split('\n'):
                if i.startswith('pool'):
                    pool=re.split('\s+',re.split(':',i)[1])
                elif i.startswith('osd'):        
                    osdinfo.append(re.split('\s+',i))
                else:
                    pass
            #pool :  0   1   | SUM 
            #--------------------------------
            #osd.0   18  86  | 104
            #get osd2poolid pg numbers
            if str(poolid)=='-1':
                return osdinfo,-1
            for idx,value in enumerate(pool):
                if str(poolid)==value:
                    default=idx
            return osdinfo,default
        s_resource,idx = parse_pg_maps(out,poolid)
        logging.info(str(s_resource))
        logging.info(str(idx))
        resource = [ (i[0],int(i[idx])) for i in s_resource if int(i[idx])]
        logging.info(resource)
        dict_osd2pg = dict(resource)
        return dict_osd2pg

    @property
    def pgaverage(self):
        default=self.osd2pg
        logging.info(default)
        total = sum([i for i in default.values()])
        pg_average = total/len(default.keys())
        return pg_average

    
    #call method self.osd2weight
    @property
    def osd2weight(self):
        out = run_cmd(self.osdmap)
        osd_dump = json.loads(out)
        import collections
        dict_osd2weight = collections.OrderedDict()
        for i in osd_dump[9]:
            dict_osd2weight[i["osd"]]= i["weight"]
        return dict_osd2weight


    #call method self.osd2weight
   # @property
   # def osd2weight(self):
   #     out = run_cmd(self.osd_tree)
   #     dict_osd2weight={}
   #     for node in json.loads(out)['nodes']:
   #         if node['id'] in range(0,300):
   #             dict_osd2weight[node['name']]=node['crush_weight']
   #     return dict_osd2weight

    def complete_exit(self,m,n):
        max, min=m,n
        #use float to get float percent.
        if float(max-min)/float(self.pgaverage) < 0.04:
            import sys
            logging.info("max osd / min osd  is %f "%(float(max-min)/float(self.pgaverage)))
            logging.info(green("reblanse osd  successfully, less then 4% !"))
            sys.exit(0)

    #return max_pg_num,min_pg_num 
    @property    
    def pg_max_min(self):
        o2u=self.osd2pg
        logging.info(o2u)
        max = o2u[o2u.keys()[0]]
        max_osd = o2u.keys()[0]
        min = o2u[o2u.keys()[0]]
        min_osd = o2u.keys()[0]
        other_same_max = []
        other_same_min = []
        #max and min compare use float
        for osd,pg in o2u.iteritems():
            if pg > max:
                max_osd = osd
                max = pg 
            elif pg < min:
                min_osd = osd
                min = pg
            else:
                pass
        #other same max and min compare use int
        for osd,pg in o2u.iteritems():
            if max == pg and osd <> max_osd:
                other_same_max.append(osd)
            elif pg == min and osd <> min_osd:
                other_same_min.append(osd)
            else:
                pass
        logging.info("max osd pg : %s %d"%(max_osd,max))
        logging.info("min osd pg : %s %d"%(min_osd,min))
        if other_same_max:
            logging.info(green("other same max osd: %s %d"%(str(other_same_max),max)))
        if other_same_min:
            logging.info(green("other same min osd: %s %d"%(str(other_same_min),min)))
        self.complete_exit(max,min)
        return max,min,max_osd,min_osd,other_same_max,other_same_min

    def check_active_clean(self):
        time.sleep(5)
        out = run_cmd(self.pg_stat)
        d_info = json.loads(out)
        logging.info(str(d_info))
        try:
            out = [ i['num'] for i in d_info['num_pg_by_state'] if i['name']=='active+clean' ]
        except KeyError:
            out =[0]
        if out[0] == d_info['num_pgs']:
            return True
        else:
            return False

    @property
    def now_hour(self):
        now=datetime.now()
        return now.hour

    
    def check_time_exit(self,start,end):
        start = int(start)
        end = int(end)
        if start not in range(0,24) or end not in range(0,24):
            raise TimeFormatError('the start %d and end %d is not in 00,01,02...23!'%(start,end))
        if start > end:
            timerange=range(start,23+1)+range(0,end+1)
            while True:
                if self.now_hour not in timerange:
                    logging.info(red("%d is not in reblance time %s , need to wait 60s"
                        %(self.now_hour,str(timerange))))
                    time.sleep(60)
                else:
                    break
        if start < end:
            timerange=range(start,end+1)
            while True:
                if self.now_hour not in timerange:
                    logging.info(red("%d is not in reblance time %s , need to wait 60s"
                        %(self.now_hour,str(timerange))))
                    time.sleep(60)
                else:
                    break

    def reweight_osd_pg(self,s_num):
        o2weight=self.osd2weight
        logging.info(o2weight)
        max,min,max_osd,min_osd,other_same_max,other_same_min = self.pg_max_min
        s_num = float(s_num)
        logging.info("reweight %f"%s_num)
        #max_osd
        run_cmd(self.osd_crush_reweight%(max_osd, o2weight[max_osd]-s_num))
        o2weight[max_osd] =  o2weight[max_osd]-s_num
        #other_same_max
        for other_osd in other_same_max:
            run_cmd(self.osd_crush_reweight%(other_osd, o2weight[other_osd]-s_num))
            o2weight[other_osd] =  o2weight[other_osd]-s_num
        #other_same_min
        for other_osd in other_same_min:
            run_cmd(self.osd_crush_reweight%(other_osd, o2weight[other_osd]+s_num))
            o2weight[other_osd] =  o2weight[other_osd]+s_num
        #min_osd
        run_cmd(self.osd_crush_reweight%(min_osd, o2weight[min_osd]+s_num))
        o2weight[min_osd] =  o2weight[min_osd]+s_num

    @property
    def pool2id(self):
        out=run_cmd(self.df)
        pool_name2pool_id={}
        for n2i in json.loads(out)["pools"]:
            pool_name2pool_id[n2i['name']]=n2i['id']
        logging.info(str(pool_name2pool_id))
        return pool_name2pool_id
    @createDaemon
    @operations
    def reblance_osd_through_pg(self,pool,start,end,exec_times):
        self.poolid=self.pool2id[pool]
        logging.info("pool id : %s"%self.poolid)
        aver=self.pgaverage
        o2p=self.osd2pg
        max,min,max_osd,min_osd,other_same_max,other_same_min=self.pg_max_min
        logging.info('averger: %d'%aver)
        for i in range(3):
            self.check_time_exit(start,end)
            #use float to get float percent.
            if float(o2p[max_osd])/float(aver)-1 > 0.2:
                self.reweight_osd_pg(0.1)
            elif 0.2 > float(o2p[max_osd])/float(aver)-1 > 0.1:
                self.reweight_osd_pg(0.05)
            elif 0.1 > float(o2p[max_osd])/float(aver)-1 > 0.06:
                self.reweight_osd_pg(0.04)
            else:
                self.reweight_osd_pg(0.02)
           # while True:
           #     time.sleep(1)
           #     result = self.check_active_clean()
           #     if result:
           #         logging.info('first reweight , status is not active + clean , please wait !')
           #         break
           #     else:
           #         continue
            logging.info(green("first period reweight , times %d successfully"%(i+1)))
        logging.info("new osd weight info: "+str(self.osd2weight))
        for i in range(3):
            self.check_time_exit(start,end)
            self.reweight_osd_pg(0.01)
           # while True:
           #     result = self.check_active_clean()
           #     if result:
           #         logging.info('second reweight , status is not active + clean , please wait !')
           #         break
           #     else:
           #         continue
            logging.info(green("second period reweight 0.01 times %d"%(i+1)))
        for i in range(3):
            self.check_time_exit(start,end)
            self.reweight_osd_pg(0.004)
           # while True:
           #     result = self.check_active_clean()
           #     if result:
           #         logging.info('third reweight , status is not active + clean , please wait !')
           #         break
           #     else:
           #         continue
            logging.info(green("third period reweight 0.004 times %d"%(i+1)))
        logging.info("osd weight info: "+str(self.osd2weight))
        logging.info("osd to pg info: "+str(self.osd2pg))
        time.sleep(0.5)
        myosd2weight = open('/tmp/osd2weight','w')
        pickle.dump(self.osd2weight,myosd2weight)

def get_paras():
    from optparse import OptionParser
    opt=OptionParser()
    opt.add_option( '-p', '--pool_name',
                    dest='pool_name',
                    type=str,
                    help='the pool_name in the system!'
                    )
    opt.add_option( '-a', '--all_pool',
                    dest='all_pool',
                    action='store_true',
                    help='all pool but not contain sys pool!'
                    )
    opt.add_option( '-s', '--start_time',
                    dest='start_time',
                    default=1,
                    help='the start reblance time, default 1 !'
                    )
    opt.add_option( '-e', '--end_time',
                    dest='end_time',
                    default=5,
                    help='the end reblance time, default 5!'
                    )
    opt.add_option( '-n', '--exec_num',
                    dest='exec_num',
                    default=5,
                    help='exec reblance functions times,default 5!'
                    )
    (options,args) = opt.parse_args()
    logging.info(options)
    if options.pool_name=='sys':
        raise NotSupportError('not support %s reblance, or input poolname is error, please check'
                                %options.pool_name)
    elif options.pool_name and options.all_pool:
        opt.error("can't use -p and -a in same time")
    elif options.pool_name and options.start_time and options.end_time:
        return options
    elif options.all_pool:
        return "-1"    
    else:
        return options

if __name__ == "__main__":
    args=get_paras()
    blance=BlancePg()
    blance.reblance_osd_through_pg(args.pool_name,args.start_time,args.end_time,exec_times=args.exec_num)
    
    #if sys.argv[1]:
    #    osd2pg,average,pg_list,osd_list = get_average(out,sys.argv[1])
    #    reblance_osd_one_by_one(osd2pg,average,pg_list,osd_list,sys.argv[1])
    #else:
    #    osd2pg,average,pg_list,osd_list = get_average(out)
    #    reblance_osd_one_by_one(osd2pg,average,pg_list,osd_list)
    #get_max_min(osd2pg)
    #reblance_osd_all(osd2pg,average,pg_list)


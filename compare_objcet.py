
import os,sys,re
import glob
import pickle
import subprocess
import json
import time
from colors import red,blue

class NotExistFileError(Exception):
    def __init__(self):
        Exception.__init__(self,"Not Exist the plk file")

def cur_time_str():
    return time.strftime('%Y-%m-%d %H:%M:%S')

class C(object):
    def __init__(self):
        self.same,self.different={},{}

    def get_all_pg_objects(self):
        file = self.get_path('/root/*/pg_dict_dump_file.pkl')
        print file
        if not file:
            raise NotExistFileError()
        else:
            with open(file[0],'r') as f:
                pg_2_object=pickle.load(f)
            return pg_2_object

    def get_path(self,pg_or_file,object=None,parten="01"):
        if not object:
            return glob.glob(pg_or_file)
        return glob.glob("/root/*%s/*%s_%s*"%(parten,pg_or_file,object))

    def run_cmd(self,cmd):
        args = cmd.split(' ')
        run = subprocess.Popen(args,
                            close_fds=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
        stdout,stderr = run.communicate(input=None)
        if stderr:
            print "err: ",stderr
        return stdout

    def json_attr(self,file):
        cmd = "/opt/sandstone/bin/sds-dencoder \
        import %s type object_info_t decode dump_json"%file
        info=self.run_cmd(cmd)
        return json.loads(info)


    def compare_attr(self,pg,object,record):
        files=self.get_path(pg,object)
        print files
        if len(files)==2:
            first=self.json_attr(files[0])
            second=self.json_attr(files[1])
            with open(record,'a+') as f:
                if first["version"] <> second["version"] and \
                   first["prior_version"] <> second["prior_version"]:
                    f.write(red("{:*>30}_{:*<30} \n".format(pg,object)))
                    self.different["%s_%s"%(pg,object)] = { files[0] : [first["version"], first["prior_version"]], 
                                                            files[1] : [second["version"], second["prior_version"]]}
                else:
                    self.same["%s_%s"%(pg,object)] = {files[0] : [first["version"], first["prior_version"]],
                                                     files[1] : [second["version"], second["prior_version"]]}
                    f.write("{:*>30}_{:*<30} \n".format(pg,object))
                f.write("{0[0]}: {version} {prior_version} \n".format(files, **first))
                f.write("{0[1]}: {version} {prior_version} \n".format(files, **second))
        else:
            print  "not find the primary and follow!  %s_%s"%(pg,object)       
            
    def all(self):
        pg_2_object = self.get_all_pg_objects()
        record = "compare_%s" % cur_time_str()
        for pg, objects in pg_2_object.items():
            for o in objects:
                self.compare_attr(pg,o,record)
        with open(record,"a+") as r:
            r.write(blue("same is %d \n" % len(self.same.keys()) ) )
            r.write(red("different is %d \n" % len(self.different.keys()) ) )

if __name__ == "__main__":
    c=C() 
    c.all()




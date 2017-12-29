#!/tmp/tools/env/tops/bin/python
# -*- coding:utf-8 -*-
###usage: deviceName  mtu
import os
import sys
import re
import subprocess


if len(sys.argv) != 3:
    print "Input length is incorrect!"
    print "Usage:%s deviceName mtu" % sys.argv[0]
    sys.exit(1)

deviceName = sys.argv[1]
mtu_value = sys.argv[2]
path = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir,'Lib_testcase'))
sys.path.append(path)

#change mtu
change_mtu = subprocess.Popen(["ifconfig", "%s" %deviceName, "mtu", "%s" % mtu_value], stdout=subprocess.PIPE)

#check mtu
check_mtu = subprocess.Popen(["ip", "addr", "show"], stdout=subprocess.PIPE).stdout.readlines()
mtu_list = []
pattern_mtu = re.compile(r".*%s.*mtu\s*(\d*)" % deviceName)
for item in check_mtu:
    mtu_now = re.search(pattern=pattern_mtu, string=item)
    if mtu_now is not None:
        mtu_list.append(mtu_now.groups()[0])

if mtu_value not in mtu_list:
    print "MTU set failed! Please check! Need %s!" % mtu_value
    sys.exit(1)
print "MTU set successfully!"
sys.exit(0)
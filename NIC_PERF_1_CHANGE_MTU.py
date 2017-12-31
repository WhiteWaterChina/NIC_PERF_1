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
change_mtu = subprocess.Popen("ifconfig %s mtu %s" % (deviceName, mtu_value), shell=True,stdout=subprocess.PIPE)

#check mtu
check_mtu = subprocess.Popen("ip addr show|grep %s|grep mtu|awk '{match($0,/mtu\s*([0-9]*)/,a);print a[1]}'" % deviceName, shell=True,stdout=subprocess.PIPE).stdout.readlines()[0].strip()

if check_mtu != mtu_value:
    print "MTU set failed! Please check! Need %s!" % mtu_value
    sys.exit(1)
print "MTU set successfully!"
sys.exit(0)
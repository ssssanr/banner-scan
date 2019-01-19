#-*-coding=utf-8-*-
# __author__  = sanr
# __url__     = http://0x007.blog.51cto.com/
# __version__ = 2.0
import requests
import re
import sys
from threading import Thread,Lock
import Queue
import chardet
import netaddr
import socket
import struct
import optparse
import os
import time
 
 
lock = Lock()
 
q = Queue.Queue()
 
def ip2int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]
def int2ip(addr):
    return socket.inet_ntoa(struct.pack("!I", addr))
  
def int_dec(pagehtml):
    '''
    智能获取页面编码
    第一步查找charset
    第二步使用chardect智能匹配
    '''
    charset = None
    if pagehtml != '':
        # print 'use charset dect'
        enc = chardet.detect(pagehtml)
        # print 'enc= ', enc
        if enc['encoding'] and enc['confidence'] > 0.9:
            charset = enc['encoding']
 
        if charset == None:
            charset_re = re.compile("((^|;)\s*charset\s*=)([^\"']*)", re.M)
            charset=charset_re.search(pagehtml[:1000]) 
            charset=charset and charset.group(3) or None
 
        # test charset
        try:
            if charset:
                unicode('test',charset,errors='replace')
        except Exception,e:
            print 'Exception',e
            charset = None
    # print 'charset=', charset
    return charset
 
 
def http_banner():
 
    while True:
        try:
            if q.qsize() == 0:
                break;
            ip = q.get()
             
            url='http://%s:%s'%(ip,port)
            url=requests.get(url,timeout=2)
 
            body = url.content
             
            charset = None
            if body != '':
                charset = int_dec(body)
 
            if charset == None or charset == 'ascii':
                charset = 'ISO-8859-1'
 
            if charset and charset != 'ascii' and charset != 'unicode':
                try:
                    body = unicode(body,charset,errors='replace')
                except Exception, e:
                    body = ''
            #获取状态码
            Struts=url.status_code
            #获取webserver信息
            Server=url.headers['server'][0:13]
            #获取title
            if Struts==200 or Struts==403 or Struts==401:
                title=re.findall(r"<title>(.*)<\/title>",body)
                if len(title):
                    title = title[0].strip()
                else:
                    title = ''
                #输出加锁 防止第二行输入
                #申请锁
                lock.acquire()
                print ('%s\t%d\t%-10s\t%s'%(ip.lstrip('http://'),Struts,Server,title))
                #释放锁
                lock.release()
        except (requests.HTTPError,requests.RequestException,AttributeError,KeyError),e:
            pass
 
 
def main(ips,threads=10):
    if '-' in ips:
        start, end = ips.split('-')
        startlong = ip2int(start)
        endlong = ip2int(end)
        ips = netaddr.IPRange(start,end)
        for ip in list(ips):
            q.put(str(ip))
    elif '/'   in ips:
        ips = netaddr.IPNetwork(ips)
        for ip in ips:
            q.put(str(ip))
             
    ths = []
    for i in xrange(threads):
        th = Thread(target=http_banner,name='thread'+str(i))
        th.start()
        ths.append(th)
         
if __name__ == '__main__':
    parser = optparse.OptionParser('usage: %prog [options] target')
    parser.add_option('-p', '--port', dest='port', default='80',type='string', help='Port.default = 80')
    parser.add_option('-t', '--threads', dest='threads_num',default=10, type='int',help='Number of threads. default = 10')
    (options,args) = parser.parse_args()
    if len(args) < 1:
        parser.print_help()
        print 'usage: python %s 218.92.227.1-218.92.227.254'%os.path.basename(sys.argv[0])
        print 'usage: python %s 218.92.227.1/24 '%os.path.basename(sys.argv[0])
        print 'usage: python %s 218.92.227.1/24 -p 8080'%os.path.basename(sys.argv[0])
        print 'usage: python %s 218.92.227.1/24 -t 100 -p 8080'%os.path.basename(sys.argv[0])
 
        sys.exit(0)
    ips=args[0]
    port=options.port
    threads = options.threads_num
    main(ips,int(threads)) 

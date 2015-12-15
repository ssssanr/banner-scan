#-*-coding=utf-8-*-
import requests
import re
import sys
from threading import Thread,Lock
import logging
import Queue
import chardet
import traceback
import netaddr
import socket
import struct

logging.basicConfig(format='[%(threadName)s]-[%(levelname)s] >> %(message)s',level=logging.WARN)
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
			#print '[*] scaning ', url.lstrip('http://')
			if q.qsize() == 0:
				break;
			ip = q.get()
			
			url = 'http://%s' %ip
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
					# traceback.print_exc()
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
	elif '/'	in ips:
		ips = netaddr.IPNetwork(ips)
		for ip in ips:
			q.put(str(ip))
			
	ths = []
	for i in xrange(threads):
		th = Thread(target=http_banner,name='thread'+str(i))
		th.start()
		ths.append(th)
	
		
if __name__ == '__main__':
	if len(sys.argv) >= 2:
		ips = sys.argv[1]
	else:
		print 'usage: python %s ips [threads]' % sys.argv[0]
		sys.exit()
	threads = 10
	if len(sys.argv) == 3:
		threads = sys.argv[2]
	main(ips,int(threads))
	
	
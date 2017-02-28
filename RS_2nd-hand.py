# -*- coding:utf-8 -*-

import requests
from lxml import etree
import urllib2
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr,formataddr
import smtplib
import re
import urllib
import cookielib
import time
import os
import random
import sys
reload(sys)
sys.setdefaultencoding( "utf-8" )

def getTitleUrl(html):
    selector = etree.HTML(html)
    list = selector.xpath('//tbody[starts-with(@id,"normalthread")]')
    title_url = []
    for each in list:
        title = each.xpath('tr/th/a[@class="s xst"]/text()')[0]
        url = each.xpath('tr/th/a/@href')[1]
        url = 'http://rs.xidian.edu.cn/' + url
        title_url.append([title,url])
    return title_url

def check( list, keywords, logs ):
    checked = []
    for eachlist in list:
        for eachkeyword in keywords:
            if eachlist[0].find(eachkeyword) != -1 :
                flag = 0 # If flag = 0 finally, means log not exist
                for eachlog in logs:
                    if eachlog.find(eachlist[0]) != -1:
                        flag = 1
                        break
                if flag == 0:
                    checked.append(eachlist)
                    break
    return checked

def getRScomtent(url):
    html = urllib2.urlopen(url).read()
    selector=etree.HTML(html)

    timediv = selector.xpath('//div[@class="authi"]')[0]
    posttime = timediv.xpath('em[starts-with(@id,"authorposton")]/span/@title')[0]

    comtent = re.findall(r'pcb{margin-right:0}</style>(.*?)<tr><td class="plc plm">',html,re.DOTALL)[0].replace('"./data/attachment','"http://rs.xidian.edu.cn/data/attachment').replace('"static/image/common/none.gif" zoomfile=','')
    return posttime, comtent

def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr(( \
        Header(name, 'utf-8').encode(), \
        addr.encode('utf-8') if isinstance(addr, unicode) else addr))

def sendemail(comtent, email_addr):
    from_addr = 'zjchen@stu.xidian.edu.cn'
    password = 'Xidian1234'
    to_addr = email_addr
    smtp_server = 'stumail.xidian.edu.cn'

    msg = MIMEText(comtent,'html','utf-8')
    msg['From'] = _format_addr(u'二手交易<%s>' % from_addr)
    msg['To'] = _format_addr(u'RS<%s>' % to_addr)
    msg['Subject'] = Header(u'你关心的 才是头条', 'utf-8')

    server = smtplib.SMTP(smtp_server,25)
    server.set_debuglevel(1)
    server.login(from_addr,password)
    server.sendmail(from_addr,[to_addr],msg.as_string())
    server.quit()

if __name__ == "__main__":
    # 处理post请求的url
    posturl = 'http://rs.xidian.edu.cn/member.php?mod=logging&action=login&loginsubmit=yes&infloat=yes&lssubmit=yes&inajax=1'

    if os.path.exists('log.txt') != True:
        log = open('log.txt', 'w')
        log.close()

    if os.path.exists('setting.txt') != True:
        setting = open('setting.txt', 'w')
        setting.write('接收邮箱=\n')
        setting.write('关键字(另起一行):\n')
        setting.close()
        exit(0)

    #设置一个cookie处理器，它负责从服务器下载cookie到本地，并且在发送请求时带上本地的cookie
    cj = cookielib.LWPCookieJar()
    cookie_support = urllib2.HTTPCookieProcessor(cj)
    opener = urllib2.build_opener(cookie_support, urllib2.HTTPHandler)
    urllib2.install_opener(opener)

    #构造header，一般header至少要包含一下两项。
    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.11 Safari/537.36',
              'Referer' : 'http://rs.xidian.edu.cn/forum.php?mod=forumdisplay&fid=106'}

    # 构造postdata用于传输登陆
    postData = {
                'username':'Terumi',
                'cookietime':'2592000',
                'password':'8f31c1023b1eb0ca522c8019322d0271',
                'quickforward':'yes',
                'handlekey':'ls'
               }

    #需要给Post数据编码
    postData = urllib.urlencode(postData)

    #通过urllib2提供的request方法来向指定Url发送我们构造的数据，并完成登录过程
    request = urllib2.Request(posturl, postData, headers)
    response = urllib2.urlopen(request)

    while True:
        try:
            # 可以往下循环
            old_campus_link = urllib2.urlopen('http://rs.xidian.edu.cn/forum.php?mod=forumdisplay&fid=110&filter=typeid&typeid=68').read()
            new_campus_link = urllib2.urlopen('http://rs.xidian.edu.cn/forum.php?mod=forumdisplay&fid=110&filter=typeid&typeid=2').read()

            old_campus_list = getTitleUrl(old_campus_link)
            new_campus_list = getTitleUrl(new_campus_link)

            with open('setting.txt') as setting:
                email_addr = setting.readline().split("=")[1].replace("\n",'').decode('gbk')
                #print email_addr
                setting.readline()
                #keywords = [each.replace("\n",'').decode('gbk') for each in setting.readlines()]   #若自己手动新建txt文件，而非程序自动生成，则需要gbk解码——windows的锅
                #keywords = [each.replace("\n", '') for each in setting.readlines()]
                keywords = [each.strip('\n') for each in setting.readlines()]
                keywords = [each for each in keywords if each != '']
                #print keywords

            log = open('log.txt')
            logs = log.readlines()
            log.close()

            old_campus_checked = check(old_campus_list,keywords,logs)
            new_campus_checked = check(new_campus_list,keywords,logs)
            allchecked = old_campus_checked + new_campus_checked
            #print allchecked

            # 存储标题到log文本中
            if len(allchecked) != 0:
                log = open('log.txt','a')
                for each in allchecked:
                    log.write(each[0])
                    log.write('\n')
                log.close()

                allcomtent = []
                for each in allchecked:
                    posttime, comtent = getRScomtent(each[1])
                    finalcomtent = '<br />标题：' + each[0] +'<br />' + '发帖时间：' + posttime + '<br />' + '<br />' + comtent + '<br />'
                    allcomtent.append(finalcomtent)
                allcomtent = ''.join(allcomtent)
                # 发送到邮箱
                sendemail(allcomtent, email_addr)
            time.sleep(10 * 60 + random.randint(0, 300))  # 暂停片刻 再次扫描
        except:
            pass



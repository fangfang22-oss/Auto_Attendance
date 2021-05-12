# -*- coding: utf-8 -*-
import sys
import datetime
import json
import re
import time

import requests
import urllib3
from halo import Halo


class DaKa():
    def __init__(self):
        self.base_url = "https://wxxy.csu.edu.cn/ncov/wap/default/index"
        self.save_url = "https://wxxy.csu.edu.cn/ncov/wap/default/save"
        self.info = None
        self.sess = requests.Session()
        self.sess.cookies.update({'eai-sess': sys.argv[1]})

    def get_info(self, html=None):
        """Get hitcard info, which is the old info with updated new time."""
        if not html:
            urllib3.disable_warnings()
            res = self.sess.get(self.base_url, verify=False)
            html = res.content.decode()

        jsontext = re.findall(r'def = {[\s\S]*?};', html)[0]
        jsontext = eval(jsontext[jsontext.find("{"):jsontext.rfind(";")].replace(" ", ""))

        geo_text = jsontext['geo_api_info']
        geo_obj = json.loads(geo_text)['addressComponent']
        area = geo_obj['province'] + " " + geo_obj['city'] + " " + geo_obj['district']
        name = re.findall(r'realname: "([^\"]+)",', html)[0]
        number = re.findall(r"number: '([^\']+)',", html)[0]

        new_info = jsontext.copy()
        new_info['name'] = name
        new_info['number'] = number
        new_info['area'] = area
        new_info["date"] = self.get_date()
        new_info["created"] = round(time.time())
        new_info['city'] = geo_obj['city']
        new_info['address'] = json.loads(geo_text)['formattedAddress']
        self.info = new_info
        return new_info

    def get_date(self):
        today = datetime.date.today()
        return "%4d%02d%02d" % (today.year, today.month, today.day)

    def post(self):
        """Post the hitcard info"""
        res = self.sess.post(self.save_url, data=self.info)
        return json.loads(res.text)


if __name__ == "__main__":
    print("\n[Time] %s" % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("🚌 打卡任务启动")
    spinner = Halo(text='Loading', spinner='dots')
    spinner.start('正在新建打卡实例...')
    dk = DaKa()
    spinner.succeed('已新建打卡实例')

    spinner.start(text='正在获取个人信息...')
    dk.get_info()
    spinner.succeed('学号末尾为%s的%s同学, 你好~' % (dk.info['number'][-4:], dk.info['name'][0]))

    spinner.start(text='正在为您打卡打卡打卡')
    res = dk.post()
    if str(res['e']) == '0':
        spinner.stop_and_persist(symbol='🦄 '.encode('utf-8'), text='已为您打卡成功！')
    else:
        spinner.stop_and_persist(symbol='🦄 '.encode('utf-8'), text=res['m'])

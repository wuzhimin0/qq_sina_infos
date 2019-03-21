# -*- coding: utf-8 -*-
# 随机UserAgent和代理IP的所需库
import random
from scrapy.conf import settings
# 获取随机代理，自己写的
from proxypool.api import get_proxies

# UserAgent随机
class RandomUserAgentMiddleware(object):
    def __init__(self):
        # 35个UserAgent的列表
        self.user_agent_list = settings["USER_AGENT_LIST"]
    # 每次请求访问时，在headers中加入一个随机的UserAgent
    def process_request(self, request, spider):
        request.headers['USER_AGENT'] = random.choice(self.user_agent_list)

class PhotoMiddleware(object):
    def process_request(self, request, spider):
        # 获取网页的网址，传入到referer中
        # referer = request.url
        if spider.name == "qq_info":
            referer = "https://new.qq.com"
        else:
            referer = "https://news.sina.com.cn/"
        if referer:
            # 每次访问时在headers中加入referer
            request.headers['referer'] = referer
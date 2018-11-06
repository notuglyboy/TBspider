# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from scrapy_splash import SplashRequest
from selenium import webdriver
from selenium.webdriver.common.proxy import ProxyType
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from scrapy.http import HtmlResponse, TextResponse
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import redis
import random
import time
from multiprocessing import Queue

class TaobaoDownloaderMiddleware(object):
    replace_lazy_script = '''
        var img_array = document.getElementsByTagName('img');
        for(var img_item of img_array){
            var img_src = img_item.getAttribute('data-ks-lazyload');
            if(img_src != null){img_item.setAttribute('src', img_src);}
        }
    '''
    def __init__(self):
        self.test_content = open('.testsource', 'r')

    @classmethod
    def from_crawler(cls, crawler):
        if crawler.spider.name == 'taobao':
            s = cls()
            crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
            return s

    def process_request(self, request, spider):
        if spider.name in ('taobao', ):
            page_source = self.test_content.read()
            return HtmlResponse(url=request.url, body=page_source, request=request, status=200, encoding='utf-8')

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        if spider.name == 'taobao':
            print(exception)
            request.meta['exception'] = 'TimeOut'
            return request

    def spider_opened(self, spider):
        self.test_content.close()
        spider.logger.info('Spider opened: %s' % spider.name)


class ProxyDownloaderMiddleware(object):
    def process_request(self, request, spider):
        if spider.name == 'proxy':
            request.headers['Content-Type'] = 'text/html'
            request.headers['User-Agent'] = 'Mozilla/5.0(compatible;MSIE 9.0; Windows NT 6.1; Trident/5.0)'


    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        return s

    def process_exception(self, request, exception, spider):
        if spider.name == 'proxy':
            print(request.url)
            print(exception)
            request.meta['is_exception'] = 'True'
            return TextResponse(url=request.meta['proxy'], body='exception', encoding='utf8', request=request)


class LocalDataMiddleware(object):

    @classmethod
    def from_crawler(cls, crawler):
        if crawler.spider.name == 'LocalSpider':
            s = cls()
            return s

    def process_request(self, request, spider):
        if spider.name in ('LocalSpider',) and request.meta['splash']['args']['action'] == 'loop_goods':
            f = open(request.meta['splash']['args']['file'], 'r', encoding='utf8')
            page_source = f.read()
            return HtmlResponse(url=request.url, body=page_source, request=request, status=200, encoding='utf-8')


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


class windowd_pool:
    def __init__(self, browser):
        self.browser = browser
        self.handles = self.browser.window_handles
        self.windows_queue = Queue()
        for handle in self.handles:
            self.windows_queue.put(handle)

    def get_windows(self):
        return self.windows_queue.get()

    def release_windows(self, windows):
        self.windows_queue.put(windows)


class TaobaoDownloaderMiddleware(object):

    def __init__(self):
        self.chrome_options = Options()
        #self.chrome_options.add_argument('--headless')
        #self.chrome_options.add_argument('--disable-gpu')

        #self.chrome_options.add_argument("--proxy-server=http://171.221.239.11:808")
        self.browser = webdriver.Chrome(chrome_options=self.chrome_options)
        self.wait = WebDriverWait(self.browser, 5)
        self.conn = redis.StrictRedis(host='127.0.0.1', port=6379)
        self.proxy_list = list(self.conn.hgetall('proxyip').keys())
        self.action = ActionChains(self.browser)
        self.windows_poll = windowd_pool(self.browser)
        time.sleep(6)

    def get_random_proxy(self):
        list_len = len(self.proxy_list)
        list_index = random.randint(0, list_len-1)
        return self.proxy_list[list_index].decode('utf8')

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):

        if spider.name in ('taobao', ):
            windows_handle = self.windows_poll.get_windows()
            self.browser.switch_to.window(windows_handle)
            #self.action.key_down(Keys.CONTROL).send_keys('t').key_up(Keys.CONTROL).perform()
            self.browser.get(request.url)
            if request.meta.get('loop_category', None):
                cateitem = self.browser.find_element_by_xpath('/html/body/div[4]/div[1]/div[1]/div[1]/div/ul/li')
                self.action.move_to_element(cateitem)
                self.action.perform()
                time.sleep(2)
                self.wait.until(lambda x: x.find_elements_by_xpath('/html/body/div[4]/div[1]/div[1]/div[1]/div/div/div[1]/div[1]/div[1]/p/a[1]'))

            elif request.meta.get('loop_goods', None):
                self.wait.until(lambda x: x.find_elements_by_xpath('//*[@id="listsrp-itemlist"]'))
            else:
                try:
                    '''
                    proxy = webdriver.Proxy()
                    proxy.proxy_type = ProxyType.MANUAL
                    proxy_addr = self.get_random_proxy()
                    proxy.http_proxy = proxy_addr
                    print('get proxy is ' + proxy_addr)
                    proxy.add_to_capabilities(webdriver.DesiredCapabilities.CHROME)
                    self.browser.start_session(webdriver.DesiredCapabilities.CHROME)
                    '''

                    #self.wait.until(lambda x: x.find_elements_by_xpath('//*[@id="listsrp-itemlist"]'))
                except TimeoutError:
                    return request
            page_source = self.browser.page_source
            self.windows_poll.release_windows(windows_handle)
            return HtmlResponse(url=request.url, body=self.browser.page_source,
                                        request=request, status=200, encoding='utf-8')


    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        if spider.name == 'taobao':
            print(exception)
            request.meta['exception'] = 'TimeOut'
            return request

    def spider_opened(self, spider):
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

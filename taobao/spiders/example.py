# -*- coding: utf-8 -*-
import scrapy, json
import js2xml
from scrapy_splash import SplashRequest

from taobao.items import ProxyItem


class TaobaoSpider(scrapy.Spider):
    name = 'taobao'
    start_urls = ['https://www.taobao.com/']
    root_url = 'https://www.taobao.com/'
    def mergetitle(self, locator):
        t = locator.xpath('.//span').extract()[0]
        #for l in locator.xpath('.//span'):
        #    t = t + l.extract()[0]
        return t

    def start_requests(self):
        meta_dict = {}
        meta_dict['loop_category'] = 'True'
        yield scrapy.Request(self.root_url, meta=meta_dict)

    def parse_goods_list(self, response):
        pass

    def parse(self, response):
        f = open('category.json', 'wb+')

        categorys = response.xpath('/html/body/div[4]/div[1]/div[1]/div[1]/div/div/div[1]/div[1]/div[1]/p/a')
        print(len(categorys))
        categorys_dict = {}
        for category in categorys:
            if category.xpath('.//@href').extract()[0].startswith('https://s.taobao.com/list?'):
                category_key = category.xpath('.//text()').extract()[0]
                category_href = category.xpath('.//@href').extract()[0]
                categorys_dict[category_key] = category_href
                yield scrapy.Request(category_href, callback=self.parse_goods_list, meta={'loop_goods': 'True'})

        s = json.dumps(categorys_dict)
        f.write(s.encode('utf8'))
        f.close()

        '''
        f.write(response.body)
        f.close()
        goods_list = response.xpath('//*[@id="listsrp-itemlist"]/div/div/div[1]/div')
        for goods in goods_list:
            print(goods.xpath('.//div[3]/div[2]/a/text()').extract()[0])
        '''


class ProxySpider(scrapy.Spider):
    name = 'proxy'
    start_urls = [
        'http://www.xicidaili.com/nn',
        'http://www.xicidaili.com/wt',
        'http://www.xicidaili.com/nt',
        'http://www.xicidaili.com/wn',
    ]
    test_url = 'http://47.106.86.29:8000'

    def test_proxy(self, response):
        if not response.meta.get('is_exception', None):
            addr = ProxyItem()
            addr['addr'] = response.meta['proxy']
            yield addr

    def parse(self, response):
        iplist = response.xpath('//*[@id="ip_list"]/tr')
        for item in iplist[1:]:
            ip = item.xpath('.//td[2]/text()').extract()[0]
            port = item.xpath('.//td[3]/text()').extract()[0]
            proxy_addr = 'http://%s:%s' % (ip, port)
            yield scrapy.Request(self.test_url, meta={'proxy': proxy_addr}, callback=self.test_proxy, dont_filter=True)
            for i in range(6)[2:]:
                yield scrapy.Request("%s/%s" % (response.url, i))


class splashSpider(scrapy.Spider):
    name = 'splash'
    test_url = 'https://item.taobao.com/item.htm?spm=a219r.lmn002.14.27.2229585d6ahQfb&id=578083768146&ns=1&abbucket=6'

    start_urls = [
        'https://item.taobao.com/item.htm?spm=a219r.lmn002.14.27.2229585d6ahQfb&id=578083768146&ns=1&abbucket=6'
    ]
    script = """
             function main(splash, args)
                 splash:go(args.url)
                 splash:wait(5)
                 return splash:html()
             end
             """

    #def start_requests(self):
    #    yield SplashRequest(self.test_url, callback=self.parse, endpoint='execute', args ={'lua_source': self.script})

    def parse(self, response):
        des = response.xpath('//*[@id="description"]')
        print(des.extract()[0].encode('utf8'))
        f = open('goods.html', 'wb+')
        f.write(des.extract()[0].encode('utf8'))
        #print(response.body)
        f.close()

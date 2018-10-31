# -*- coding: utf-8 -*-
import json
import re
import scrapy
import js2xml
from scrapy_splash import SplashRequest

from taobao.items import ProxyItem, TaobaoItem


class TaobaoSpider(scrapy.Spider):
    name = 'taobao'
    start_urls = ['https://www.taobao.com/']
    root_url = 'https://www.taobao.com/'
    goods_url = 'https://item.taobao.com/item.htm?spm=a219r.lmn002.14.1.56843127n2RwMM&id=577564098267&ns=1&abbucket=6'
    goods_list_url = 'https://s.taobao.com/list?spm=a21bo.2017.201867-links-0.19.5a8f11d9cw80zP&q=%E5%8D%8A%E8%BA%AB%E8%A3%99&cat=16&seller_type=taobao&oetag=6745&source=qiangdiao'
    def start_requests(self):
        meta_dict = {}
        meta_dict['loop_category'] = 'True'
        #yield scrapy.Request(self.root_url, meta=meta_dict)
        #yield scrapy.Request(self.goods_url,  meta={'get_data': 'True'}, callback=self.parse_goods)
        yield scrapy.Request(self.goods_list_url, meta={'loop_goods': 'True'}, callback=self.parse_goods_list)

    def parse_goods(self, response):
        print('parse goods')
        goods_item = TaobaoItem()
        title = response.xpath('//*[@id="J_Title"]/h3/text()').extract()[0]
        goods_item['title'] = title
        property_dict = {}
        htm = response.body.decode('utf8')
        sku_s = re.search('skuMap.*?:', htm).group()
        sku_map_str = re.search('(?<=%s).*\}' % sku_s, htm).group()
        for property in response.xpath('//*[@id="J_isku"]/div[@class="tb-skin"]/dl[contains(@class,"J_Prop")]'):
            property_key = property.xpath('.//dt/text()').extract()[0]
            property_value_str = ""
            for property_value in property.xpath('.//dd/ul/li'):
                value = property_value.xpath('.//a/span/text()').extract()[0]
                sku_str = "%s:%s" % (property_key, value)
                sku_key = property_value.xpath('.//@data-value').extract()[0]
                property_value_str = '%s;%s' % (property_value_str, value)
                sku_map_str = sku_map_str.replace(sku_key, sku_str)
            property_dict[property_key] = property_value_str
        goods_item['property'] = property_dict
        goods_item['sku'] = sku_map_str.replace('\"', '\'')
        descript = response.xpath('//*[@id="description"]').extract()[0]
        goods_item['descript'] = descript.strip().replace('\"', '\'')
        yield goods_item

    def parse_goods_list(self, response):
        goods_url_list = response.xpath('//*[@id="listsrp-itemlist"]/div/div/div[1]/div')
        for goods in goods_url_list[0:2]:
            goods_url = goods.xpath('.//div[3]/div[2]/a/@href').extract()[0]
            yield scrapy.Request("http:%s" % goods_url, callback=self.parse_goods, meta={'get_data': 'True'})

    def parse(self, response):
        f = open('category.json', 'wb+')

        categorys = response.xpath('/html/body/div[4]/div[1]/div[1]/div[1]/div/div/div[1]/div[1]/div[1]/p/a')
        print(len(categorys))
        categorys_dict = {}
        for category in categorys[0:8]:
            if category.xpath('.//@href').extract()[0].startswith('https://s.taobao.com/list?'):
                category_key = category.xpath('.//text()').extract()[0]
                category_href = category.xpath('.//@href').extract()[0]
                categorys_dict[category_key] = category_href
                yield scrapy.Request(category_href, callback=self.parse_goods_list, meta={'loop_goods': 'True'})

        s = json.dumps(categorys_dict)
        f.write(s.encode('utf8'))
        f.close()


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
    root_url = 'https://www.taobao.com/'
    goods_url = 'https://item.taobao.com/item.htm?spm=2013.1.20141001.1.e5796eebicshgg&id=578175958491&scm=1007.12144.95220.42296_0&pvid=cc4e5abc-9aaa-43cf-bb08-db40454212af&utparam=%7B%22x_hestia_source%22%3A%2242296%22%2C%22x_object_type%22%3A%22item%22%2C%22x_mt%22%3A0%2C%22x_src%22%3A%2242296%22%2C%22x_pos%22%3A1%2C%22x_pvid%22%3A%22cc4e5abc-9aaa-43cf-bb08-db40454212af%22%2C%22x_object_id%22%3A578175958491%7D'
    goods_list_url = 'https://s.taobao.com/list?spm=a21bo.2017.201867-links-0.19.5a8f11d9cw80zP&q=%E5%8D%8A%E8%BA%AB%E8%A3%99&cat=16&seller_type=taobao&oetag=6745&source=qiangdiao'

    script = """
             function main(splash, args)
                 

                 splash:go(args.url)
                 if(args.action == 'get_data') then
                    local script = string.format(waitElement,'#J_DivItemDesc img')
                    local result, error = splash:wait_for_resume(script)
                 elseif(args.action == 'loop_goods') then
                    splash:wait(5)
                 elseif(args.action == 'loop_category') then
                    print('lopp category')
                 end
                 return splash:html()
             end
             """

    def start_requests(self):
        args_dict = {}
        args_dict['lua_source'] = self.script

        args_dict['action'] = 'get_data'
        yield SplashRequest(self.goods_url, callback=self.parse_goods, endpoint='execute', args=args_dict)

        #args_dict['action'] = 'loop_goods'
        #yield SplashRequest(self.goods_list_url, callback=self.parse_goods_list,endpoint='execute', args=args_dict)

    def parse_goods(self, response):
        print('parse goods')
        goods_item = TaobaoItem()
        title = response.xpath('//*[@id="J_Title"]/h3/text()').extract()[0]
        goods_item['title'] = title
        property_dict = {}
        htm = response.body.decode('utf8')
        sku_s = re.search('skuMap.*?:', htm).group()
        sku_map_str = re.search('(?<=%s).*\}' % sku_s, htm).group()
        for property in response.xpath('//*[@id="J_isku"]/div[@class="tb-skin"]/dl[contains(@class,"J_Prop")]'):
            property_key = property.xpath('.//dt/text()').extract()[0]
            property_value_str = ""
            for property_value in property.xpath('.//dd/ul/li'):
                value = property_value.xpath('.//a/span/text()').extract()[0]
                sku_str = "%s:%s" % (property_key, value)
                sku_key = property_value.xpath('.//@data-value').extract()[0]
                property_value_str = '%s;%s' % (property_value_str, value)
                sku_map_str = sku_map_str.replace(sku_key, sku_str)
            property_dict[property_key] = property_value_str
        goods_item['property'] = property_dict
        goods_item['sku'] = sku_map_str.replace('\"', '\'')
        descript = response.xpath('//*[@id="description"]').extract()[0]
        goods_item['descript'] = descript.strip().replace('\"', '\'')
        yield goods_item

    def parse_goods_list(self, response):
        print('parse_goods_list')
        goods_url_list = response.xpath('//*[@id="listsrp-itemlist"]/div/div/div[1]/div')
        for goods in goods_url_list[0:2]:
            goods_url = goods.xpath('.//div[3]/div[2]/a/@href').extract()[0]
            print(goods_url)
            yield SplashRequest("http:%s" % goods_url, callback=self.parse_goods, endpoint='execute',
                                args={'lua_source': self.script, 'action': 'get_data'})

    def parse(self, response):
        f = open('category.json', 'wb+')

        categorys = response.xpath('/html/body/div[4]/div[1]/div[1]/div[1]/div/div/div[1]/div[1]/div[1]/p/a')
        print(len(categorys))
        categorys_dict = {}
        for category in categorys[0:8]:
            if category.xpath('.//@href').extract()[0].startswith('https://s.taobao.com/list?'):
                category_key = category.xpath('.//text()').extract()[0]
                category_href = category.xpath('.//@href').extract()[0]
                categorys_dict[category_key] = category_href
                yield SplashRequest(category_href, callback=self.parse_goods_list, endpoint='execute',
                                    args={'lua_source': self.script, 'action': 'loop_goods'})

        s = json.dumps(categorys_dict)
        f.write(s.encode('utf8'))
        f.close()

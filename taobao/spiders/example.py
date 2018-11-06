# -*- coding: utf-8 -*-
import json
import re
import os
import scrapy
import js2xml
from scrapy_splash import SplashRequest
import abc
from taobao.items import ProxyItem, TaobaoItem


class TaobaoSpider(scrapy.Spider):
    name = 'taobao1'
    start_urls = ['https://www.taobao.com/']
    root_url = 'https://www.taobao.com/'
    goods_url = 'https://item.taobao.com/item.htm?spm=a219r.lmn002.14.1.56843127n2RwMM&id=577564098267&ns=1&abbucket=6'
    goods_list_url = 'https://s.taobao.com/list?spm=a21bo.2017.201867-links-0.19.5a8f11d9cw80zP&q=%E5%8D%8A%E8%BA%AB%E8%A3%99&cat=16&seller_type=taobao&oetag=6745&source=qiangdiao'
    def start_requests(self):
        meta_dict = {}
        meta_dict['loop_category'] = 'True'
        #yield scrapy.Request(self.root_url, meta=meta_dict)
        #yield scrapy.Request(self.goods_url,  meta={'get_data': 'True'}, callback=self.parse_goods)
        yield scrapy.Request(self.goods_list_url, meta={'loop_goods': 'True'}, callback=self.parse_goods)

    def parse_goods(self, response):
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

        url_list = []
        for img_url_item in response.xpath('//*[@id="J_UlThumb"]/li'):
            url = img_url_item.xpath('.//div/a/img/@src').extract()[0]
            print(url)
            url_list.append(url.replace('50x50', '400x400'))

        goods_item['img_url'] = str(url_list)
        goods_item['property'] = property_dict
        # goods_item['sku'] = sku_map_str.replace('\"', '\'')
        goods_item['sku'] = json.loads(sku_map_str)
        descript = response.xpath('//*[@id="description"]').extract()[0]
        goods_item['descript'] = descript.strip().replace('\"', '\'')
        yield goods_item

    def parse_goods_list(self, response):
        goods_url_list = response.xpath('//*[@id="listsrp-itemlist"]/div/div/div[1]/div')
        for goods in goods_url_list[0:10]:
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

    goods_url = 'https://item.taobao.com/item.htm?spm=a219r.lm895.14.601.71834edcwa9SzE&id=574058285482&ns=1&abbucket=6'
    goods_list_url = 'https://s.taobao.com/list?spm=a21bo.2017.201867-links-0.56.300611d904Hd6n&q=%E7%89%9B%E4%BB%94%E8%A3%A4&cat=50344007&style=grid&seller_type=taobao'

    script = """
             function main(splash, args)
                 local replace_lazy_src = [[
                    var img_array = document.getElementsByTagName('img');
                    for(var img_item of img_array){
                        var img_src = img_item.getAttribute('data-ks-lazyload');
                        if(img_src != null){img_item.setAttribute('src', img_src);}
                    }
                 ]]

                 local waitElement = [[
                     function main(splash) {
                    function waitElement(func, selector, timeout){
                        _interval = 20;
                        _timeout = timeout || 0;
                        var _times = (_timeout/_interval) || -1;
                        _self = document.querySelector(selector);
                        _iIntervalID = 0;
                        if(_self){func&& func.call(this);}
                        else{
                            _iIntervalID = setInterval(function(){
                                if(!_times){clearInterval(_iIntervalID);func&& func.call(_self);}
                                _times <= 0 || _times--;
                                _self = document.querySelector(selector);
                                if(_self){func&& func.call(_self);clearInterval(_iIntervalID);}
                            }, _interval);
                        }
                        return _self;
                     };
                     waitElement(function(){
                        splash.set('result', 'asd');
                        splash.resume();
                     }, '%s',30000)
                    }
                 ]]

                 splash:go(args.url)
                 if(args.action == 'get_data') then
                    local script = string.format(waitElement,'#J_DivItemDesc img')
                    local result, error = splash:wait_for_resume(script)
                    splash:runjs(replace_lazy_src)
                    splash:wait(4)
                 elseif(args.action == 'loop_goods') then
                    local script = string.format(waitElement,'#listsrp-itemlist')
                    local result, error = splash:wait_for_resume(script)
                    --splash:wait(5)
                 elseif(args.action == 'loop_category') then
                    print('lopp category')
                 end
                 return splash:html()
             end
             """

    def start_requests(self):
        args_dict = {}
        args_dict['lua_source'] = self.script
        #args_dict['action'] = 'get_data'
        #yield SplashRequest(self.goods_url, callback=self.parse_goods, endpoint='execute', args=args_dict)
        args_dict['action'] = 'loop_goods'
        yield SplashRequest(self.goods_list_url, callback=self.parse_goods_list, endpoint='execute', args=args_dict)

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

        url_list = []
        for img_url_item in response.xpath('//*[@id="J_UlThumb"]/li'):
            url = img_url_item.xpath('.//div/a/img/@src').extract()[0]
            print(url)
            url_list.append(url.replace('50x50', '400x400'))

        goods_item['img_url'] = str(url_list)
        goods_item['property'] = property_dict
        #goods_item['sku'] = sku_map_str.replace('\"', '\'')
        goods_item['sku'] = json.loads(sku_map_str)
        descript = response.xpath('//*[@id="description"]').extract()[0]
        goods_item['descript'] = descript.strip().replace('\"', '\'')
        yield goods_item

    def parse_goods_list(self, response):
        print('parse_goods_list')
        goods_url_list = response.xpath('//*[@id="listsrp-itemlist"]/div/div/div[1]/div')
        for goods in goods_url_list[0:10]:
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


class splashSpider(scrapy.Spider):
    name = 'LocalSpider'
    root_url = 'https://www.baidu.com/'
    goods_url = 'http://item.taobao.com/item.htm?id=578375508416&ns=1&abbucket=6'
    script = """
                 function main(splash, args)
                     local replace_lazy_src = [[
                        var img_array = document.getElementsByTagName('img');
                        for(var img_item of img_array){
                            var img_src = img_item.getAttribute('data-ks-lazyload');
                            if(img_src != null){img_item.setAttribute('src', img_src);}
                        }
                     ]]

                     local waitElement = [[
                         function main(splash) {
                        function waitElement(func, selector, timeout){
                            _interval = 20;
                            _timeout = timeout || 0;
                            var _times = (_timeout/_interval) || -1;
                            _self = document.querySelector(selector);
                            _iIntervalID = 0;
                            if(_self){func&& func.call(this);}
                            else{
                                _iIntervalID = setInterval(function(){
                                    if(!_times){clearInterval(_iIntervalID);func&& func.call(_self);}
                                    _times <= 0 || _times--;
                                    _self = document.querySelector(selector);
                                    if(_self){func&& func.call(_self);clearInterval(_iIntervalID);}
                                }, _interval);
                            }
                            return _self;
                         };
                         waitElement(function(){
                            splash.set('result', 'asd');
                            splash.resume();
                         }, '%s',30000)
                        }
                     ]]

                     splash:go(args.url)
                     if(args.action == 'get_data') then
                        local script = string.format(waitElement,'#J_DivItemDesc img')
                        local result, error = splash:wait_for_resume(script)
                        splash:runjs(replace_lazy_src)
                        splash:wait(4)
                     elseif(args.action == 'loop_goods') then
                        local script = string.format(waitElement,'#listsrp-itemlist')
                        local result, error = splash:wait_for_resume(script)
                        --splash:wait(5)
                     elseif(args.action == 'loop_category') then
                        print('lopp category')
                     end
                     return splash:html()
                 end
            """

    def start_requests(self):
        args_dict = {}
        args_dict['lua_source'] = self.script
        file_name = ''
        category = ''
        root_dir = 'E:\project\myhtml\ShopData'
        for cate_dir in os.listdir(root_dir):
            cate_root = r'%s\%s' % (root_dir, cate_dir)
            for cate in os.listdir(cate_root):
                cate_name = r'%s\%s' % (cate_root, cate)
                for cate_goods in os.listdir(cate_name):
                    file_name = '%s\%s' % (cate_name, cate_goods)
                    category = '%s:%s' % (cate, cate_goods)
                    print(file_name)
        args_dict['category'] = category
        args_dict['file'] = file_name
        args_dict['action'] = 'loop_goods'
        yield SplashRequest(self.root_url, callback=self.parse_goods_list, endpoint='execute', args=args_dict)

    def parse_goods(self, response):
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

        url_list = []
        for img_url_item in response.xpath('//*[@id="J_UlThumb"]/li'):
            url = img_url_item.xpath('.//div/a/img/@src').extract()[0]
            print(url)
            url_list.append(url.replace('50x50', '400x400'))

        goods_item['img_url'] = str(url_list)
        goods_item['property'] = property_dict
        goods_item['sku'] = json.loads(sku_map_str)
        descript = response.xpath('//*[@id="description"]').extract()[0]
        goods_item['descript'] = descript.strip().replace('\"', '\'')
        yield goods_item

    def parse_goods_list(self, response):
        goods_url_list = response.xpath('//*[@id="listsrp-itemlist"]/div/div/div[1]/div')
        for goods in goods_url_list[0:2]:
            goods_url = goods.xpath('.//div[3]/div[2]/a/@href').extract()[0]
            yield SplashRequest("http:%s" % goods_url, callback=self.parse_goods, endpoint='execute',
                                args={'lua_source': self.script, 'action': 'get_data'})

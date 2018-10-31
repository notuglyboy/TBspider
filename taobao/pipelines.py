# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
#import redis
import json

from taobao.spiders.example import ProxySpider


class TaobaoPipeline(object):
    def __init__(self):
        self.goods = open('goods.json', 'w', encoding='utf8')

    def process_item(self, item, spider):
        line = json.dumps(dict(item), ensure_ascii=False) + '\n'
        self.goods.writelines(line)
        return item

    def spider_closed(self, spider):
        self.goods.close()


class ProxyPipeline(object):

    def __init__(self):
        self.conn = None

    def open_spider(self, spider):
        #self.conn = redis.StrictRedis(host='127.0.0.1', port=6379)
        pass

    def process_item(self, item, spider):
        pass
        #if isinstance(spider, ProxySpider):
        #    self.conn.hset('proxyip', item['addr'], 1)
        #    return item
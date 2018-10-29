# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import redis

class TaobaoPipeline(object):

    def process_item(self, item, spider):
        return item


class ProxyPipeline(object):

    def __init__(self):
        self.conn = None

    def open_spider(self, spider):
        self.conn = redis.StrictRedis(host='127.0.0.1', port=6379)

    def process_item(self, item, spider):
        self.conn.hset('proxyip', item['addr'], 1)
        return item
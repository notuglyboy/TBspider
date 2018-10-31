# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class TaobaoItem(scrapy.Item):
    sku = scrapy.Field()
    title = scrapy.Field()
    property = scrapy.Field()
    descript = scrapy.Field()


class ProxyItem(scrapy.Item):
    addr = scrapy.Field()

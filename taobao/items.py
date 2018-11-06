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
    category = scrapy.Field()
    descript = scrapy.Field()
    img_url = scrapy.Field()


class ProxyItem(scrapy.Item):
    addr = scrapy.Field()

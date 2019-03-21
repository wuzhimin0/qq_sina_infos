# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Field

class QQCommonItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # 文章类型
    article_type = Field()
    thumbnail = Field()
    title = Field()
    times = Field()
    # 文章分类
    classify = Field()
    # 来源
    source = Field()
    # 文章主内容
    content = Field()
    detail_img = Field()

class QQSubjectItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # 文章类型
    article_type = Field()
    thumbnail = Field()
    title = Field()
    times = Field()
    # 文章分类
    classify = Field()
    # 来源
    source = Field()
    # 文章主内容
    content = Field()
    detail_img = Field()
    # 专题的标题
    subject_title = Field()
    # 专题文章的分类
    subject_class = Field()

class SinaInfosItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = Field()
    thumbnail = Field()
    times = Field()
    # 文章分类
    classify = Field()
    # 来源
    source = Field()
    # 文章主内容
    content = Field()
    detail_img = Field()

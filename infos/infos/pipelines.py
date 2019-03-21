# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import re,pymysql
from scrapy import Request
from scrapy.conf import settings
from scrapy.exceptions import DropItem
from infos.items import QQCommonItem
from infos.items import QQSubjectItem
from infos.items import QQVideoItem
from infos.items import SinaInfosItem
from scrapy.pipelines.images import ImagesPipeline

class InfosPipeline(object):
    def __init__(self):
        self.book_set = set()
        host = settings["MYSQL_HOST"]
        user = settings["MYSQL_USER"]
        passwd = settings["MYSQL_PASSWD"]
        dbname = settings["MYSQL_DBNAME"]
        self.db = pymysql.connect(host, user, passwd, dbname, charset="utf8")
        self.cursor = self.db.cursor()
    def process_item(self, item, spider):
        name = item['title']
        if name in self.book_set:
            raise DropItem("Duplicate book found:%s" % item)
        self.book_set.add(name)
        # 存入数据库时，不同的item类型用不同的语句，存入同一个数据库
        thumbnail = "".join(item["thumbnail"])
        detail_img = "".join(item["detail_img"])
        if isinstance(item,QQCommonItem):
            sql = "insert into info(article_type,thumbnail,title,times,classify,source,content,detail_img) value ('%s', '%s', '%s', '%s', '%s', '%s','%s','%s')" % (item["article_type"], thumbnail, item["title"], item["times"], item["classify"], item["source"],item["content"],detail_img)
        elif isinstance(item,QQSubjectItem):
            sql = "insert into info(article_type,thumbnail,title,times,classify,source,content,detail_img,subject_title,subject_class) value ('%s', '%s', '%s', '%s', '%s', '%s','%s','%s','%s','%s')" % (item["article_type"], thumbnail, item["title"], item["times"], item["classify"],item["source"], item["content"], detail_img,item["subject_title"],item["subject_class"])
        elif isinstance(item,SinaInfosItem):
            sql = "insert into info(thumbnail,title,times,classify,source,content,detail_img) value ('%s', '%s', '%s', '%s', '%s','%s','%s')" % (thumbnail, item["title"], item["times"], item["classify"],item["source"], item["content"], detail_img)
        else:
            sql = ""
            print("error")
        try:
            print("1111111111111111111",sql)
            self.cursor.execute(sql)
            self.db.commit()
        except Exception as error:
            # 打印错误
            print(error)
        return item

    def close_spider(self,spider):
        self.cursor.close()
        self.db.close()

# 下载详情图
class DetailImagePipeline(ImagesPipeline):
    # 写存储图片的函数
    def get_media_requests(self, item, info):
        for image_url in item['detail_img']:
            if image_url[:2] == "//":
                image_url = "http:" + image_url
            elif image_url[:4] == "http":
                image_url = image_url
            yield Request(url=image_url, meta={"name":item["title"],"classify":item["classify"]})

    # 重写图片存放的目录名及文件名的函数
    def file_path(self, request, response=None, info=None):
        classify = request.meta["classify"]
        name = request.meta["name"]
        # \ /: * ?"<>| 目录中不能有这几个字符
        name = re.sub(r'[?\\*|"<>:/]',"",name)
        image_guids = request.url.split("/")[-1]
        if "jpg" not in image_guids and "png" not in image_guids and "jpeg" not in image_guids:
            image_guid = request.url.split("/")[-2] + ".jpg"
        else:
            image_guid = image_guids
        filename = u'{0}/{1}/{2}'.format(classify,name, image_guid)
        return filename

    # 将图片的地址从网址变成本地的路径
    def item_completed(self, results, item, info):
        imgs = []
        image_paths = [x['path'] for ok, x in results if ok]
        if not image_paths:
            raise DropItem('Item contains no images')
        for img in image_paths:
            if item["title"] in img:
                imgs.append(img)
        item["detail_img"] = imgs
        return item

# 下载缩略图
class ThunmbnailImagePipeline(ImagesPipeline):
    # 写存储图片的函数
    def get_media_requests(self, item, info):
        image_url = item["thumbnail"]
        if image_url:
            if image_url[:2] == "//":
                image_url = "http:" + image_url
            elif image_url[:4] == "http":
                image_url = image_url
            yield Request(url=image_url, meta={"name": item["title"], "classify": item["classify"]})

    # 重写图片存放的目录名及文件名的函数
    def file_path(self, request, response=None, info=None):
        classify = request.meta["classify"]
        name = request.meta["name"]
        name = re.sub(r'[?\\*|"<>:/]',"",name)
        image_guid = request.url.split("/")[-1]
        filename = u'{0}/{1}/{2}/{3}'.format(classify,name,"缩略图" ,image_guid)
        return filename

    # 将图片的地址从网址变成本地的路径
    def item_completed(self, results, item, info):
        image_paths = [x['path'] for ok, x in results if ok]
        if not image_paths:
            raise DropItem('Item contains no images')
        item["thumbnail"] = image_paths
        return item

# 下载缩略图
class ThunmbnailImagePipeline1(ImagesPipeline):
    headers = {
        "User-Agent":"Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36",
        "Referer":"https://new.qq.com/zt/template/?id=FIN2019032000191600",
    }
    # 写存储图片的函数
    def get_media_requests(self, item, info):
        for img_url in item["thumbnail"]:
            if img_url[:2] == "//":
                img_url = "http:" + img_url
            elif img_url[:4] == "http":
                img_url = img_url
            yield Request(url=img_url, meta={"name": item["title"], "classify": item["classify"]},headers=self.headers)

    # 重写图片存放的目录名及文件名的函数
    def file_path(self, request, response=None, info=None):
        classify = request.meta["classify"]
        name = request.meta["name"]
        name = re.sub(r'[?\\*|"<>:/]',"",name)
        image_guids = request.url.split("/")[-1]
        if "jpg" not in image_guids and "png" not in image_guids and "jpeg" not in image_guids:
            image_guid = request.url.split("/")[-2] + ".jpg"
        else:
            image_guid = image_guids
        filename = u'{0}/{1}/{2}/{3}'.format(classify,name,"缩略图" ,image_guid)
        return filename

    # 将图片的地址从网址变成本地的路径
    def item_completed(self, results, item, info):
        image_paths = [x['path'] for ok, x in results if ok]
        if not image_paths:
            raise DropItem('Item contains no images')
        item["thumbnail"] = image_paths
        return item
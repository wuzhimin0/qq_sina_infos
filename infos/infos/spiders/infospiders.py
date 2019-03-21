# -*- coding: utf-8 -*-
from scrapy.spiders import CrawlSpider
from scrapy.http import Request
from infos.items import QQCommonItem
from infos.items import QQSubjectItem
from infos.items import QQVideoItem
from infos.items import SinaInfosItem
import json,re,sys,io

# 其实print()函数的局限就是Python默认编码的局限，因为系统是win7的，python的默认编码不是'utf-8',改一下python的默认编码成'utf-8'就行了
sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='gb18030') #改变标准输出的默认编码

class InfoSpider(CrawlSpider):
    custom_settings = {
        'ITEM_PIPELINES':{
        'infos.pipelines.InfosPipeline': 300,
        'infos.pipelines.DetailImagePipeline': 200,
        'infos.pipelines.ThunmbnailImagePipeline1': 210,
        }
    }
    name = 'qq_info'
    allowed_domains = []
    start_urls = [r'https://mat1.gtimg.com/pingjs/ext2020/configF2017/5a9cf828.js']

    # 获得各个分类的cid和名字
    def parse(self, response):
        nav_datas = response.text
        re_nav = re.compile(r'"nav":(.*?),"nav2"')
        nav_data = re_nav.findall(nav_datas)
        nav_json = json.loads(nav_data[0])
        for nav in nav_json:
            for n_data in nav_json[nav]:
                try:
                    if int(n_data["ids"]) or n_data["ids"] == "0":
                        print(n_data)
                except:
                    ext = n_data["ids"]
                    classify = n_data["name"]
                    # 热点精选
                    popul_url = [r"https://pacaio.match.qq.com/irs/rcd?cid=135&token=6e92c215fb08afa901ac31eca115a34f&ext={}&page={}".format(ext, str(i)) for i in range(1)]#11
                    for popul in popul_url:
                        yield Request(url=popul, callback=self.main_parse,meta={"classify": classify},dont_filter=True)
                    # 主新闻
                    main_url = [r"https://pacaio.match.qq.com/irs/rcd?cid=146&token=49cbb2154853ef1a74ff4e53723372ce&ext={}&page={}".format(ext, str(i)) for i in range(1)]  # 1000
                    for main in main_url:
                        yield Request(url=main, callback=self.main_parse,meta={"classify": classify}, dont_filter=True)

    # 根据获得的cid对文章进行区分，不同类型的文章不同的处理方式
    def main_parse(self,response):
        news_data = response.text
        classify = response.meta["classify"]
        result = json.loads(news_data).get("data")
        if result:
            for r in result:
                item = QQCommonItem()
                item["classify"] = classify
                article_type = int(r["article_type"])
                item["thumbnail"] = r["multi_imgs"]
                item["source"] = r["source"]
                item["times"] = r["update_time"]
                item["article_type"] = article_type
                item["title"] = r["title"]
                article_url = r["vurl"]
                if article_type == 0:
                    pass
                    # dont_filter=True解决301重定向的问题
                    yield Request(url=article_url, callback=self.details_parse, meta={"data": item},dont_filter=True)
                elif article_type == 11:
                    app_id = r["app_id"]
                    subject_url = r"https://openapi.inews.qq.com/getQQNewsSpecialListItems?refer=mobileqqcom&srcfrom=newsapp&id={}".format(app_id)
                    yield Request(url=subject_url, callback=self.subject_parse,meta={"data":classify,"title":r["title"]},dont_filter=True)
                else:
                    pass


    # 普通文章内容
    def details_parse(self,response):
        item = response.meta["data"]
        content = response.xpath('//div[@class="content-article"]/p/text()').extract()
        item["content"] = "".join(content)
        item["detail_img"] = response.xpath('//div[@class="content-article"]/p/img/@src').extract()
        yield item

    # 专题页的文章列表
    def subject_parse(self,response):
        classify = response.meta["data"]
        title = response.meta["title"]
        subject_data = response.text
        subject_json = json.loads(subject_data)
        for subj in subject_json["idlist"]:
            subject_class = subj["section"]
            for s in subj["newslist"]:
                item = QQSubjectItem()
                item["classify"] = classify
                item["article_type"] = 11
                item["subject_title"] = title
                item["title"] = s["title"]
                item["source"] = s["source"]
                item["thumbnail"] = s["thumbnails"]
                item["subject_class"] = subject_class
                article_id = s["id"]
                article_url = r"https://openapi.inews.qq.com/getQQNewsNormalContent?id={}&chlid=news_rss&refer=mobilewwwqqcom&ext_data=all&srcfrom=newsapp".format(article_id)
                yield Request(url=article_url,callback=self.subject_article,meta={"data":item},dont_filter=True)

    # 专题页的文章
    def subject_article(self,response):
        item = response.meta["data"]
        article_data = response.text
        article_json = json.loads(article_data)
        content = ""
        detail_img = []
        item["times"] = article_json["pubtime"]
        for cont in article_json["content"]:
            if int(cont["type"]) == 1:
                content += cont["value"]
            elif int(cont["type"]) == 2:
                detail_img.append(cont["value"])
        item["content"] = content
        item["detail_img"] = detail_img
        yield item

class SinaInfoSpider(CrawlSpider):
    custom_settings = {
        'ITEM_PIPELINES':{
        'infos.pipelines.InfosPipeline': 300,
        'infos.pipelines.DetailImagePipeline': 200,
        'infos.pipelines.ThunmbnailImagePipeline': 210,
    }
    }
    name = 'sina_info'
    allowed_domains = ['sina.com.cn']
    start_urls = []

    def start_requests(self):
        # 国内新闻
        china_url = ["https://feed.sina.com.cn/api/roll/get?pageid=121&lid=1356&num=20&page={}".format(str(i)) for i in range(1)]#0-9283可以从0开始
        for ch_url in china_url:
            yield Request(url=ch_url,callback=self.info_parse,meta={"data":"国内新闻"})
        # 国际新闻
        word_url = ["https://interface.sina.cn/news/get_news_by_channel_new_v2018.d.html?cat_1=51923&show_num=27&level=1,2&page={}".format(str(i)) for i in range(1,2)]#不可以从0开始 #1-37
        for w_url in word_url:
            yield Request(url=w_url,callback=self.info_parse,meta={"data":"国际新闻"})
        # 辟谣
        piyao_url = "http://piyao.sina.cn/api/list/group?len=50"
        yield Request(url=piyao_url,callback=self.piyao_parse)
        # 文化
        cul_url = ["http://feed.mix.sina.com.cn/api/roll/get?pageid=411&lid=2595&num=22&page={}".format(str(i))for i in range(1)]#0-57
        for c_url in cul_url:
            yield Request(url=c_url,callback=self.info_parse,meta={"data":"文化"})

        # 中国军情、国际军情、东海局势、南海局势；静态的数据
        mil_url = ["http://mil.news.sina.com.cn/roll/index.d.html?cid=57918&page=1","http://mil.news.sina.com.cn/roll/index.d.html?cid=57919&page=1","http://mil.news.sina.com.cn/roll/index.d.html?cid=234399&page=1","http://mil.news.sina.com.cn/roll/index.d.html?cid=234400&page=1"]
        for m_url in mil_url:
            yield Request(url=m_url,callback=self.mil_parse)
        # 军事深度ajax加载的数据1-100
        mil_depth_url = ["https://interface.sina.cn/news/get_news_by_channel_new_v2018.d.json?cat_1=57920&level=1,2&page={}&show_num=10".format(str(i)) for i in range(1,2)]
        for mil_dp_url in mil_depth_url:
            yield Request(url=mil_dp_url,callback=self.mil_ajax_parse,meta={"data":"军事深度"})
        # 大国博弈1-100
        mil_dg_url = ["http://interface.sina.cn/news/get_news_by_channel_new_v2018.d.json?cat_1=70035&level=1,2&page={}&show_num=10".format(str(i)) for i in range(1,2)]
        for mil_d_url in mil_dg_url:
            yield Request(url=mil_d_url,callback=self.mil_ajax_parse,meta={"data":"大国博弈"})
        # 军史回眸1-100
        mil_holmes_url = ["http://interface.sina.cn/news/get_news_by_channel_new_v2018.d.json?cat_1=57921&level=1,2&page={}&show_num=10".format(str(i)) for i in range(1,2)]
        for mil_h_url in mil_holmes_url:
            yield Request(url=mil_h_url,callback=self.mil_ajax_parse,meta={"data":"军史回眸"})
        # 航空新闻1-1025
        mil_air_url = ["http://api.roll.news.sina.com.cn/zt_list?channel=sky&show_num=22&tag=1&page={}".format(str(i))for i in range(1,2)]
        for mil_a_url in mil_air_url:
            yield Request(url=mil_a_url,callback=self.mil_ajax_parse,meta={"data":"航空新闻"})
        # 出鞘1-32
        mil_chu_url = ["http://platform.sina.com.cn/slide/album?app_key=3656193992&format=json&active_size=198_132&size=img&ch_id=8&sid=62085&page={}&num=16".format(str(i)) for i in range(1,2)]
        for mil_c_url in mil_chu_url:
            yield Request(url=mil_c_url,callback=self.chu_parse,meta={"data":"出鞘"})

    # 国内新闻、国际新闻、文化的列表页
    def info_parse(self, response):
        classify = response.meta["data"]
        china_infos = response.text
        china_info = json.loads(china_infos).get("result").get("data")
        if china_info:
            for c_info in china_info:
                item = SinaInfosItem()
                item["classify"] = classify
                item["title"] = c_info["title"]
                item["source"] = c_info["media_name"]
                thumbnails = c_info.get("img")
                if type(thumbnails) is dict:
                    thumbnail = thumbnails["u"]
                else:
                    thumbnail = thumbnails
                item["thumbnail"] = thumbnail
                article_url = c_info["url"]
                yield Request(url=article_url,callback=self.info_detail,meta={"data":item},dont_filter=True)

    # 国内新闻、国际新闻、文化的文章页
    def info_detail(self,response):
        item = response.meta["data"]
        item["times"] = response.xpath('//span[@class="date"]/text()').extract()[0]
        content = response.xpath('//div[@id="article"]/p//text()').extract()
        item["content"] = "".join(content)
        item["detail_img"] = response.xpath('//div[@id="article"]//img/@src').extract()
        yield item

    # 辟谣的列表页
    def piyao_parse(self,response):
        piyao_infos = response.text
        piyao_info = json.loads(piyao_infos).get("result").get("data")
        i = 0
        if piyao_info:
            for p in piyao_info:
                for p_info in piyao_info[p]:
                    item = SinaInfosItem()
                    item["classify"] = "辟谣"
                    item["title"] = p_info["title"]
                    item["thumbnail"] = p_info["img"]
                    item["source"] = p_info.get("media_name")
                    article_url = p_info["url"]
                    yield Request(url=article_url,callback=self.piyao_detail,meta={"data":item},dont_filter=True)
                    i += 1
                    if i == 50:
                        ptime = p_info["ptime"]
                        next_url = "http://piyao.sina.cn/api/list/group?len=50&ptime={}".format(ptime)
                        yield Request(url=next_url,callback=self.piyao_parse,dont_filter=True)

    # 辟谣的文章页
    def piyao_detail(self,response):
        item = response.meta["data"]
        content = response.xpath('//div[@class="paragraph"]/div/text()').extract()
        item["content"] = "".join(content)
        item["detail_img"] = response.xpath('//div[@class="paragraph"]/div/img/@src').extract()
        item["times"] = response.xpath('//span[@class="article_date"]/text()').extract()[0]
        yield item

    # 中国军情、国际军情、东海局势、南海局势的列表页
    def mil_parse(self,response):
        data = response.xpath('//ul[@class="linkNews"]/li')
        if data:
            for d in data:
                item = SinaInfosItem()
                item["classify"] = response.xpath('//div[@class="hd"]/h3/text()').extract()[0]
                item["title"] = d.xpath('a/text()').extract()[0]
                item["thumbnail"] = []
                article_url = d.xpath('a/@href').extract()[0]
                yield Request(url=article_url,callback=self.mil_detail,meta={"data":item})
                next_url = response.xpath('//span[@class="pagebox_next"]/a/@href').extract()
                if next_url:
                    # yield Request(url=next_url[0],callback=self.mil_parse,dont_filter=True)
                    pass

    # 军事深度、大国博弈、军史回眸、航空的列表页
    def mil_ajax_parse(self, response):
        classify = response.meta["data"]
        datas = response.text
        data = json.loads(datas).get("result").get("data")
        if data:
            for d in data:
                item = SinaInfosItem()
                item["title"] = d["title"]
                item["classify"] = classify
                item["thumbnail"] = d["img"]
                item["source"] = d["media_name"]
                article_url = d["url"]
                if classify == "航空新闻":
                    yield Request(url=article_url, callback=self.air_detail, meta={"data": item})
                else:
                    yield Request(url=article_url, callback=self.mil_detail, meta={"data": item})

    # 中国军情、国际军情、东海局势、南海局势；军事深度、大国博弈、军史回眸的文章页
    def mil_detail(self,response):
        item = response.meta["data"]
        content = response.xpath('//div[@id="article"]/p/text()').extract()
        item["content"] = "".join(content)
        source = response.xpath('//div[@class="date-source"]/a/text()').extract()
        if not source:
            source = response.xpath('//div[@class="date-source"]/span[@class="source"]/text()').extract()
        item["source"] = source[0]
        item["detail_img"] = response.xpath('//div[@id="article"]/div/img/@src').extract()
        item["times"] = response.xpath('//div[@class="date-source"]/span[@class="date"]/text()').extract()[0]
        yield item

    # 航空的文章页
    def air_detail(self,response):
        item = response.meta["data"]
        content = response.xpath('//div[@id="artibody"]/p/text()').extract()[:-5]
        item["content"] = "".join(content)
        item["times"] = response.xpath('//span[@class="titer"]/text()').extract()[0]
        item["detail_img"] = response.xpath('//div[@id="artibody"]/div[@class="img_wrapper"]/img/@src').extract()
        yield item

    # 出鞘的列表页
    def chu_parse(self,response):
        datas = response.text
        data = json.loads(datas).get("data")
        if data:
            for d in data:
                item = SinaInfosItem()
                item["title"] = d["name"]
                item["classify"] = "出鞘"
                item["thumbnail"] = d["img_url"]
                item["times"] = d["createtime"]
                article_url = d["url"]
                yield Request(url=article_url,callback=self.chu_detail,meta={"data":item})

    # 出鞘的文章页
    def chu_detail(self,response):
        item = response.meta["data"]
        content = []
        contents = response.xpath('//div[@id="eData"]/dl')
        for c in contents:
            cont = c.xpath('dd/text()').extract()[4:-1]
            content.append("".join(cont))
        item["content"] = content
        item["detail_img"] = response.xpath('//div[@id="eData"]/dl/dd[1]/text()').extract()
        item["source"] = ""
        yield item
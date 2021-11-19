import math
import functools
from lxml import html
import requests
import time
import json
import random
import sys
from concurrent.futures import ProcessPoolExecutor
from Core.exception import SKException
from bs4 import BeautifulSoup
from Config.settings import config
from Logger.logger import logger
from Core.login import SpiderSession, QrLogin
from Message.message import sendMessage
from Core.timer import Timer
from Core.util import parse_json


class Waiter():
    def __init__(self,
                 skuids=config.settings("Spider", "sku_id"),
                 area=config.settings("Spider", "area"),
                 eid=config.settings("Spider", "eid"),
                 fp=config.settings("Spider", "fp"),
                 count=config.settings("Spider", "amount"),
                 payment_pwd=config.settings(
                     "Account", "payment_pwd"),
                 retry=config.settings("Spider", "retry"),
                 work_count=config.settings(
                     'Spider', 'work_count'),
                 random_time=config.settings(
                     'Spider', 'random_time'),
                 timeout=float(config.raw(
                     "Spider", "timeout")),
                 date=config.settings('Spider', 'buy_time').__str__()
                 ):

        self.skuids = skuids
        self.area = area
        self.eid = eid
        self.fp = fp
        self.count = count
        self.payment_pwd = payment_pwd
        self.retry = retry
        self.work_count = work_count
        self.random_time = random_time
        self.timeout = timeout
        self.buyTime = date

        self.spider_session = SpiderSession()
        self.spider_session.load_cookies_from_local()
        self.session = self.spider_session.get_session()
        self.qrlogin = QrLogin(self.spider_session)
        self.user_agent = self.spider_session.user_agent
        self.item_cat = {}
        self.item_vender_ids = {}  # 记录商家id
        self.headers = {'User-Agent': self.user_agent}
        self.timers = Timer(self.buyTime)

    def login_by_qrcode(self):
        """
        二维码登陆
        :return:
        """
        if self.qrlogin.is_login:
            logger.info('登录成功')
            return

        self.qrlogin.login_by_qrcode()

        if self.qrlogin.is_login:
            self.nick_name = self.getUsername()
            self.spider_session.save_cookies_to_local(self.nick_name)
        else:
            raise SKException("二维码登录失败！")

    def check_login(func):
        """
        用户登陆态校验装饰器。若用户未登陆，则调用扫码登陆
        """

        @functools.wraps(func)
        def new_func(self, *args, **kwargs):
            if not self.qrlogin.is_login:
                logger.info("{0} 需登陆后调用，开始扫码登陆".format(func.__name__))
                self.login_by_qrcode()
            return func(self, *args, **kwargs)

        return new_func

    @check_login
    def waitForSell(self):
        self._waitForSell()

    @check_login
    def waitTimeForSell(self):
        self._waitTimeForSell()

    def get_tag_value(self, tag, key='', index=0):
        if key:
            value = tag[index].get(key)
        else:
            value = tag[index].text
        return value.strip(' \t\r\n')

    def response_status(self, resp):
        if resp.status_code != requests.codes.OK:
            print('Status: %u, Url: %s' % (resp.status_code, resp.url))
            return False
        return True

    def getUsername(self):
        userName_Url = 'https://passport.jd.com/new/helloService.ashx?callback=jQuery339448&_=' + str(
            int(time.time() * 1000))
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "Referer": "https://order.jd.com/center/list.action",
            "Connection": "keep-alive"
        }
        resp = self.session.get(url=userName_Url, allow_redirects=True)
        resultText = resp.text
        resultText = resultText.replace('jQuery339448(', '')
        resultText = resultText.replace(')', '')
        usernameJson = json.loads(resultText)
        logger.info('登录账号名称' + usernameJson['nick'])
        return usernameJson['nick']

    def get_sku_title(self):
        """获取商品名称"""
        url = 'https://item.jd.com/{}.html'.format(self.skuids)
        resp = self.session.get(url).content
        x_data = html.etree.HTML(resp)
        sku_title = x_data.xpath('/html/head/title/text()')
        try:
            result = sku_title[0]
            return result
        except:
            return self.get_sku_title()

    @check_login
    def waitAndBuy_by_proc_pool(self):
        """
        多进程进行抢购
        work_count：进程数量
        """
        work_count = self.work_count
        with ProcessPoolExecutor(work_count) as pool:
            for i in range(work_count):
                pool.submit(self.buy)

    def check_item_stock(self):
        """
        检查是否有货
        """
        stockurl = 'http://c0.3.cn/stock?skuId=' + self.skuids + \
                   '&cat=652,829,854&area=' + self.area + \
                   '&extraParam={%22originid%22:%221%22}'
        response = self.session.get(stockurl)
        resp = self.session.get(stockurl)
        jsparser = json.loads(resp.text)
        # 33 有货 34 无货
        if jsparser['StockState'] == 33 and jsparser['StockStateName'] == '现货':
            print('库存状态：', jsparser['StockStateName'])
            return True
        else:
            print('库存状态：{}(无现货)'.format(jsparser['StockStateName']))
            return False

    def _get_item_detail_page(self, sku_id):
        """访问商品详情页
        :param sku_id: 商品id
        :return: 响应
        """
        url = 'https://item.jd.com/{}.html'.format(sku_id)
        page = requests.get(url=url, headers=self.headers)
        return page

    def _waitForSell(self):
        area_id = self.area
        sku_id = self.skuids
        logger.info("正在等待商品上架：{}".format(
            self.get_sku_title()[:80] + " ......"))
        while True:
            if self.get_single_item_stock(sku_id, area_id):
                logger.info("商品上架: {}".format(
                    self.get_sku_title()[:80] + " ......"))
                # self.waitAndBuy_by_proc_pool()
                self.buy()
            else:
                logger.info("等待商品上架: {}".format(
                    self.get_sku_title()[:80] + " ......"))
                time.sleep(self.timeout + random.randint(1, self.random_time))

    def _waitTimeForSell(self):
        self.initCart()
        logger.info("正在等待商品上架：{}".format(
            self.get_sku_title()[:80] + " ......"))
        self.timers.start()
        self.fastBuy()

    def get_single_item_stock(self, sku_id, area_id):
        """获取单个商品库存状态
        :param sku_id: 商品id
        :param num: 商品数量
        :param area: 地区id
        :return: 商品是否有货 True/False
        """
        url = 'https://cd.jd.com/stocks'
        # https://cd.jd.com/stocks?callback=jQuery3528455&type=getstocks&skuIds=100011513445&area=21_1827_4101_40925&_=1625970219360
        payload = {
            'callback': 'jQuery{}'.format(random.randint(1000000, 9999999)),
            'type': 'getstocks',
            'skuIds': sku_id,
            'area': area_id,
            '_': str(int(time.time() * 1000)),
        }
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://item.jd.com/{}.html'.format(sku_id),
        }

        resp_text = ''
        try:
            resp_text = requests.get(
                url=url, params=payload, headers=headers, timeout=self.timeout).text
            resp_json = parse_json(resp_text)
            stock_info = resp_json.get(sku_id)
            sku_state = stock_info.get('skuState')  # 商品是否上架
            # 商品库存状态：33 -- 现货  0,34 -- 无货  36 -- 采购中  40 -- 可配货
            stock_state = stock_info.get('StockState')
            if sku_state == 1 and stock_state in (33, 40):
                logger.info("有货: " + stock_info.get('StockStateName'))
                return True
            # else:
            #     logger.info(stock_info.get('StockStateName'))
            #     return False
        except requests.exceptions.Timeout:
            logger.error('查询 %s 库存信息超时(%ss)', sku_id, self.timeout)
            return False
        except requests.exceptions.RequestException as request_exception:
            logger.error('查询 %s 库存信息发生网络请求异常:\n%s', sku_id, request_exception)
            return False
        except Exception as e:
            logger.error('查询 %s 库存信息发生异常:\nresp: %s\nexception: %s',
                         sku_id, resp_text, e)
            return False

    def cancel_select_all_cart_item(self):
        '''
        取消勾选购物车中的所有商品
        '''
        url = "https://cart.jd.com/cancelAllItem.action"
        data = {
            't': 0,
            'outSkus': '',
            'random': random.random()
        }
        resp = self.session.post(url, data=data)
        if resp.status_code != requests.codes.OK:
            print('Status: %u, Url: %s' % (resp.status_code, resp.url))
            return False
        return True

    '''
    勾选购物车中的所有商品
    '''

    def select_all_cart_item(self):
        url = "https://cart.jd.com/selectAllItem.action"
        data = {
            't': 0,
            'outSkus': '',
            'random': random.random()
        }
        resp = self.session.post(url, data=data)
        if resp.status_code != requests.codes.OK:
            print('Status: %u, Url: %s' % (resp.status_code, resp.url))
            return False
        return True

    '''
    删除购物车选中商品
    '''

    def remove_item(self):
        url = "https://cart.jd.com/batchRemoveSkusFromCart.action"
        data = {
            't': 0,
            'null': '',
            'outSkus': '',
            'random': random.random(),
            'locationId': '19-1607-4773-0'
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.37",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://cart.jd.com/cart.action",
            "Host": "cart.jd.com",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Encoding": "zh-CN,zh;q=0.9,ja;q=0.8",
            "Origin": "https://cart.jd.com",
            "Connection": "keep-alive"
        }
        resp = self.session.post(url, data=data, headers=headers)
        logger.info('清空购物车')
        if resp.status_code != requests.codes.OK:
            print('Status: %u, Url: %s' % (resp.status_code, resp.url))
            return False
        return True

    '''
    购物车详情
    '''

    def cart_detail(self):
        url = 'https://cart.jd.com/cart.action'
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "Referer": "https://order.jd.com/center/list.action",
            "Host": "cart.jd.com",
            "Connection": "keep-alive"
        }
        resp = self.session.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")

        cart_detail = dict()
        for item in soup.find_all(class_='item-item'):
            try:
                sku_id = item['skuid']  # 商品id
            except Exception as e:
                logger.info('购物车中有套装商品，跳过')
                continue
            try:
                # 例如：['increment', '8888', '100001071956', '1', '13', '0', '50067652554']
                # ['increment', '8888', '100002404322', '2', '1', '0']
                item_attr_list = item.find(class_='increment')['id'].split('_')
                p_type = item_attr_list[4]
                promo_id = target_id = item_attr_list[-1] if len(
                    item_attr_list) == 7 else 0

                cart_detail[sku_id] = {
                    # 商品名称
                    'name': self.get_tag_value(item.select('div.p-name a')),
                    'verder_id': item['venderid'],  # 商家id
                    'count': int(item['num']),  # 数量
                    # 单价
                    'unit_price': self.get_tag_value(item.select('div.p-price strong'))[1:],
                    # 总价
                    'total_price': self.get_tag_value(item.select('div.p-sum strong'))[1:],
                    'is_selected': 'item-selected' in item['class'],  # 商品是否被勾选
                    'p_type': p_type,
                    'target_id': target_id,
                    'promo_id': promo_id
                }
            except Exception as e:
                logger.error("商品%s在购物车中的信息无法解析，报错信息: %s，该商品自动忽略", sku_id, e)

        logger.info('购物车信息：%s', cart_detail)
        return cart_detail

    '''
    修改购物车商品的数量
    '''

    def change_item_num_in_cart(self, sku_id, vender_id, num, p_type, target_id, promo_id):
        url = "https://cart.jd.com/changeNum.action"
        data = {
            't': 0,
            'venderId': vender_id,
            'pid': sku_id,
            'pcount': num,
            'ptype': p_type,
            'targetId': target_id,
            'promoID': promo_id,
            'outSkus': '',
            'random': random.random(),
            # 'locationId'
        }
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "Referer": "https://cart.jd.com/cart",
            "Connection": "keep-alive"
        }
        resp = self.session.post(url, data=data)
        return json.loads(resp.text)['sortedWebCartResult']['achieveSevenState'] == 2

    '''
    添加商品到购物车
    '''

    def add_item_to_cart(self, sku_id):
        url = 'https://cart.jd.com/gate.action'
        payload = {
            'pid': sku_id,
            'pcount': self.count,
            'ptype': 1,
        }
        resp = self.session.get(url=url, params=payload)
        if 'https://cart.jd.com/cart.action' in resp.url:  # 套装商品加入购物车后直接跳转到购物车页面
            result = True
        else:  # 普通商品成功加入购物车后会跳转到提示 "商品已成功加入购物车！" 页面
            soup = BeautifulSoup(resp.text, "html.parser")
            # [<h3 class="ftx-02">商品已成功加入购物车！</h3>]
            result = bool(soup.select('h3.ftx-02'))

        if result:
            logger.info('%s  已成功加入购物车', sku_id)
        else:
            logger.error('%s 添加到购物车失败', sku_id)

    def get_checkout_page_detail(self):
        """获取订单结算页面信息

        该方法会返回订单结算页面的详细信息：商品名称、价格、数量、库存状态等。

        :return: 结算信息 dict
        """
        url = 'http://trade.jd.com/shopping/order/getOrderInfo.action'
        # url = 'https://cart.jd.com/gotoOrder.action'
        payload = {
            'rid': str(int(time.time() * 1000)),
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "Referer": "https://cart.jd.com/cart.action",
            "Connection": "keep-alive",
            'Host': 'trade.jd.com',
        }
        try:
            # print(url)
            resp = self.session.get(url=url, params=payload, headers=headers)
            if "刷新太频繁了" in resp.text:
                logger.error("刷新太频繁了 url: {}".format(url))
                return ''

            if not self.response_status(resp):
                logger.error('获取订单结算页信息失败')
                return ''

            soup = BeautifulSoup(resp.text, "html.parser")
            # print(soup.title)
            risk_control = self.get_tag_value(
                soup.select('input#riskControl'), 'value')

            order_detail = {
                # remove '寄送至： ' from the begin
                'address': soup.find('span', id='sendAddr').text[5:],
                # remove '收件人:' from the begin
                'receiver': soup.find('span', id='sendMobile').text[4:],
                # remove '￥' from the begin
                'total_price': soup.find('span', id='sumPayPriceId').text[1:],
                'items': []
            }

            logger.info("下单信息：%s", order_detail)
            return order_detail
        except Exception as e:
            logger.error('该商品频繁刷新被京东风控！！！（仅限该商品，请勿重复多次下单，易被风控）')
        return ''

    def submit_order(self, risk_control):
        """提交订单

        重要：
        1.该方法只适用于普通商品的提交订单（即可以加入购物车，然后结算提交订单的商品）
        2.提交订单时，会对购物车中勾选✓的商品进行结算（如果勾选了多个商品，将会提交成一个订单）

        :return: True/False 订单提交结果
        """
        url = 'https://trade.jd.com/shopping/order/submitOrder.action'
        # js function of submit order is included in https://trade.jd.com/shopping/misc/js/order.js?r=2018070403091

        # overseaPurchaseCookies:
        # vendorRemarks: []
        # submitOrderParam.sopNotPutInvoice: false
        # submitOrderParam.trackID: TestTrackId
        # submitOrderParam.ignorePriceChange: 0
        # submitOrderParam.btSupport: 0
        # riskControl:
        # submitOrderParam.isBestCoupon: 1
        # submitOrderParam.jxj: 1
        # submitOrderParam.trackId:

        data = {
            'overseaPurchaseCookies': '',
            'vendorRemarks': '[]',
            'submitOrderParam.sopNotPutInvoice': 'false',
            'submitOrderParam.trackID': 'TestTrackId',
            'submitOrderParam.ignorePriceChange': '0',
            'submitOrderParam.btSupport': '0',
            'riskControl': risk_control,
            'submitOrderParam.isBestCoupon': 1,
            'submitOrderParam.jxj': 1,
            # Todo: need to get trackId
            'submitOrderParam.trackId': '9643cbd55bbbe103eef18a213e069eb0',
            # 'submitOrderParam.eid': eid,
            # 'submitOrderParam.fp': fp,
            'submitOrderParam.needCheck': 1,
        }

        def encrypt_payment_pwd(payment_pwd):
            return ''.join(['u3' + x for x in payment_pwd])

        if len(self.payment_pwd) > 0:
            data['submitOrderParam.payPassword'] = encrypt_payment_pwd(
                self.payment_pwd)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "Referer": "http://trade.jd.com/shopping/order/getOrderInfo.action",
            "Connection": "keep-alive",
            'Host': 'trade.jd.com',
        }

        try:
            resp = self.session.post(url=url, data=data, headers=headers)
            if "刷新太频繁了" in resp.text:
                logger.error("刷新太频繁了 url: {}".format(url))
                return False
            resp_json = json.loads(resp.text)

            # 返回信息示例：
            # 下单失败
            # {'overSea': False, 'orderXml': None, 'cartXml': None, 'noStockSkuIds': '', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': False, 'resultCode': 60123, 'orderId': 0, 'submitSkuNum': 0, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': None, 'msgUuid': None, 'message': '请输入支付密码！'}
            # {'overSea': False, 'cartXml': None, 'noStockSkuIds': '', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'orderXml': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': False, 'resultCode': 60017, 'orderId': 0, 'submitSkuNum': 0, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': None, 'msgUuid': None, 'message': '您多次提交过快，请稍后再试'}
            # {'overSea': False, 'orderXml': None, 'cartXml': None, 'noStockSkuIds': '', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': False, 'resultCode': 60077, 'orderId': 0, 'submitSkuNum': 0, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': None, 'msgUuid': None, 'message': '获取用户订单信息失败'}
            # {"cartXml":null,"noStockSkuIds":"xxx","reqInfo":null,"hasJxj":false,"addedServiceList":null,"overSea":false,"orderXml":null,"sign":null,"pin":"xxx","needCheckCode":false,"success":false,"resultCode":600157,"orderId":0,"submitSkuNum":0,"deductMoneyFlag":0,"goJumpOrderCenter":false,"payInfo":null,"scaleSkuInfoListVO":null,"purchaseSkuInfoListVO":null,"noSupportHomeServiceSkuList":null,"msgMobile":null,"addressVO":{"pin":"xxx","areaName":"","provinceId":xx,"cityId":xx,"countyId":xx,"townId":xx,"paymentId":0,"selected":false,"addressDetail":"xx","mobile":"xx","idCard":"","phone":null,"email":null,"selfPickMobile":null,"selfPickPhone":null,"provinceName":null,"cityName":null,"countyName":null,"townName":null,"giftSenderConsigneeName":null,"giftSenderConsigneeMobile":null,"gcLat":0.0,"gcLng":0.0,"coord_type":0,"longitude":0.0,"latitude":0.0,"selfPickOptimize":0,"consigneeId":0,"selectedAddressType":0,"siteType":0,"helpMessage":null,"tipInfo":null,"cabinetAvailable":true,"limitKeyword":0,"specialRemark":null,"siteProvinceId":0,"siteCityId":0,"siteCountyId":0,"siteTownId":0,"skuSupported":false,"addressSupported":0,"isCod":0,"consigneeName":null,"pickVOname":null,"shipmentType":0,"retTag":0,"tagSource":0,"userDefinedTag":null,"newProvinceId":0,"newCityId":0,"newCountyId":0,"newTownId":0,"newProvinceName":null,"newCityName":null,"newCountyName":null,"newTownName":null,"checkLevel":0,"optimizePickID":0,"pickType":0,"dataSign":0,"overseas":0,"areaCode":null,"nameCode":null,"appSelfPickAddress":0,"associatePickId":0,"associateAddressId":0,"appId":null,"encryptText":null,"certNum":null,"used":false,"oldAddress":false,"mapping":false,"addressType":0,"fullAddress":"xxxx","postCode":null,"addressDefault":false,"addressName":null,"selfPickAddressShuntFlag":0,"pickId":0,"pickName":null,"pickVOselected":false,"mapUrl":null,"branchId":0,"canSelected":false,"address":null,"name":"xxx","message":null,"id":0},"msgUuid":null,"message":"xxxxxx商品无货"}
            # {'orderXml': None, 'overSea': False, 'noStockSkuIds': 'xxx', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'cartXml': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': False, 'resultCode': 600158, 'orderId': 0, 'submitSkuNum': 0, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': {'oldAddress': False, 'mapping': False, 'pin': 'xxx', 'areaName': '', 'provinceId': xx, 'cityId': xx, 'countyId': xx, 'townId': xx, 'paymentId': 0, 'selected': False, 'addressDetail': 'xxxx', 'mobile': 'xxxx', 'idCard': '', 'phone': None, 'email': None, 'selfPickMobile': None, 'selfPickPhone': None, 'provinceName': None, 'cityName': None, 'countyName': None, 'townName': None, 'giftSenderConsigneeName': None, 'giftSenderConsigneeMobile': None, 'gcLat': 0.0, 'gcLng': 0.0, 'coord_type': 0, 'longitude': 0.0, 'latitude': 0.0, 'selfPickOptimize': 0, 'consigneeId': 0, 'selectedAddressType': 0, 'newCityName': None, 'newCountyName': None, 'newTownName': None, 'checkLevel': 0, 'optimizePickID': 0, 'pickType': 0, 'dataSign': 0, 'overseas': 0, 'areaCode': None, 'nameCode': None, 'appSelfPickAddress': 0, 'associatePickId': 0, 'associateAddressId': 0, 'appId': None, 'encryptText': None, 'certNum': None, 'addressType': 0, 'fullAddress': 'xxxx', 'postCode': None, 'addressDefault': False, 'addressName': None, 'selfPickAddressShuntFlag': 0, 'pickId': 0, 'pickName': None, 'pickVOselected': False, 'mapUrl': None, 'branchId': 0, 'canSelected': False, 'siteType': 0, 'helpMessage': None, 'tipInfo': None, 'cabinetAvailable': True, 'limitKeyword': 0, 'specialRemark': None, 'siteProvinceId': 0, 'siteCityId': 0, 'siteCountyId': 0, 'siteTownId': 0, 'skuSupported': False, 'addressSupported': 0, 'isCod': 0, 'consigneeName': None, 'pickVOname': None, 'shipmentType': 0, 'retTag': 0, 'tagSource': 0, 'userDefinedTag': None, 'newProvinceId': 0, 'newCityId': 0, 'newCountyId': 0, 'newTownId': 0, 'newProvinceName': None, 'used': False, 'address': None, 'name': 'xx', 'message': None, 'id': 0}, 'msgUuid': None, 'message': 'xxxxxx商品无货'}
            # 下单成功
            # {'overSea': False, 'orderXml': None, 'cartXml': None, 'noStockSkuIds': '', 'reqInfo': None, 'hasJxj': False, 'addedServiceList': None, 'sign': None, 'pin': 'xxx', 'needCheckCode': False, 'success': True, 'resultCode': 0, 'orderId': 8740xxxxx, 'submitSkuNum': 1, 'deductMoneyFlag': 0, 'goJumpOrderCenter': False, 'payInfo': None, 'scaleSkuInfoListVO': None, 'purchaseSkuInfoListVO': None, 'noSupportHomeServiceSkuList': None, 'msgMobile': None, 'addressVO': None, 'msgUuid': None, 'message': None}

            if resp_json.get('success'):
                logger.info('订单提交成功! 订单号：%s', resp_json.get('orderId'))
                sendMessage('订单提交成功! 订单号：{}'.format(resp_json.get('orderId')))
                sys.exit(1)
                return True
            else:
                message, result_code = resp_json.get(
                    'message'), resp_json.get('resultCode')
                if result_code == 0:
                    # self._save_invoice()
                    message = message + '<<<<<<<<<<京东返回的限制信息<<<<<<<-------该商品被京东限制购买'
                elif result_code == 60077:
                    message = message + '(可能是购物车为空 或 未勾选购物车中商品)'
                elif result_code == 60123:
                    message = message + '(需要在payment_pwd参数配置支付密码)'
                logger.info('订单提交失败, 错误码：%s, 返回信息：%s', result_code, message)
                logger.info(resp_json)
                return False
        except Exception as e:
            logger.error(e)
            return False

    '''
    购买环节
    测试三次
    '''

    def buyMask(self, sku_id):
        retry = self.retry
        for count in range(retry):
            logger.info('第[%s/%s]次尝试提交订单', count, 3)
            self.cancel_select_all_cart_item()
            cart = self.cart_detail()
            if sku_id in cart:
                logger.info('%s 已在购物车中，调整数量为 %s', sku_id, 1)
                cart_item = cart.get(sku_id)
                self.change_item_num_in_cart(
                    sku_id=sku_id,
                    vender_id=cart_item.get('vender_id'),
                    num=self.skuids,
                    p_type=cart_item.get('p_type'),
                    target_id=cart_item.get('target_id'),
                    promo_id=cart_item.get('promo_id')
                )
            else:
                self.add_item_to_cart(sku_id)
            risk_control = self.get_checkout_page_detail()
            if risk_control == '刷新太频繁了':
                return False
            if len(risk_control) > 0:
                if self.submit_order(risk_control):
                    return True
            logger.info('休息%ss', 3)
            time.sleep(3)
        else:
            logger.info('执行结束，提交订单失败！')
            return False

    '''
    查询库存
    '''

    '''
    update by rlacat
    解决skuid长度过长（超过99个）导致无法查询问题
    '''

    def check_stock(self):
        st_tmp = []
        len_arg = 70
        # print("skustr:",skuidStr)
        # print("skuids:",len(skuids))
        skuid_nums = len(self.skuids)
        skuid_batchs = math.ceil(skuid_nums / len_arg)
        # print("skuid_batchs:",skuid_batchs)
        if (skuid_batchs > 1):
            for i in range(0, skuid_batchs):
                if (len_arg * (i + 1) <= len(self.skuids)):
                    # print("取个数：",len_arg*i,"至",len_arg*(i+1))
                    skuidStr = ','.join(
                        self.skuids[len_arg * i:len_arg * (i + 1)])
                    st_tmp += self.check_stock_tmp(skuidStr,
                                                   self.skuids[len_arg * i:len_arg * (i + 1)])
                else:
                    # print("取个数：",len_arg*i,"至",len_arg*(i+1))
                    skuidStr = ','.join(
                        self.skuids[len_arg * i:skuid_nums])  # skuid配置的最后一段
                    # print(skuidStr)
                    st_tmp += self.check_stock_tmp(skuidStr,
                                                   self.skuids[len_arg * i:skuid_nums])
        else:
            # <=1的情况
            skuidStr = ','.join(self.skuids)
            st_tmp = self.check_stock_tmp(skuidStr, self.skuids)
        return st_tmp

    def check_stock_tmp(self, skuidString, skuids_a):
        callback = 'jQuery' + str(random.randint(1000000, 9999999))
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "Referer": "https://cart.jd.com/cart.action",
            "Connection": "keep-alive",
        }
        url = 'https://c0.3.cn/stocks'
        payload = {
            'type': 'getstocks',
            'skuIds': skuidString,
            'area': self.area,
            'callback': callback,
            '_': int(time.time() * 1000),
        }
        resp = self.session.get(url=url, params=payload, headers=headers)
        resptext = resp.text.replace(callback + '(', '').replace(')', '')
        respjson = json.loads(resptext)
        inStockSkuid = []
        nohasSkuid = []
        # print(resptext,respjson)
        for i in skuids_a:
            # print("当前处理：",i)
            if (respjson[i]['StockStateName'] != '无货'):
                inStockSkuid.append(i)
            else:
                nohasSkuid.append(i)
        # print(nohasSkuid)
        logger.info('[%s]无货', ','.join(nohasSkuid))
        return inStockSkuid

    @check_login
    def buy(self):
        sku_id = self.skuids
        retry = self.retry
        for count in range(retry):
            logger.info('第[%s/%s]次尝试提交订单', count, retry)
            self.cancel_select_all_cart_item()
            cart = self.cart_detail()
            if sku_id in cart:
                logger.info('%s 已在购物车中，调整数量为 %s', sku_id, self.count)
                cart_item = cart.get(sku_id)
                self.change_item_num_in_cart(
                    sku_id=sku_id,
                    vender_id=cart_item.get('vender_id'),
                    num=self.skuids,
                    p_type=cart_item.get('p_type'),
                    target_id=cart_item.get('target_id'),
                    promo_id=cart_item.get('promo_id')
                )
            else:
                self.add_item_to_cart(sku_id)
            risk_control = self.get_checkout_page_detail()
            if risk_control == '刷新太频繁了':
                return False
            if len(risk_control) > 0:
                if self.submit_order(risk_control):
                    return True
            logger.info('休息%ss', 3)
            time.sleep(3)
        else:
            logger.info('执行结束，提交订单失败！')
            return False

    @check_login
    def initCart(self):
        sku_id = self.skuids
        self.cancel_select_all_cart_item()
        cart = self.cart_detail()
        if sku_id in cart:
            logger.info('%s 已在购物车中，调整数量为 %s', sku_id, self.count)
            cart_item = cart.get(sku_id)
            self.change_item_num_in_cart(
                sku_id=sku_id,
                vender_id=cart_item.get('vender_id'),
                num=self.count,
                p_type=cart_item.get('p_type'),
                target_id=cart_item.get('target_id'),
                promo_id=cart_item.get('promo_id')
            )
        else:
            self.add_item_to_cart(sku_id)
        logger.info('购物车初始化结束，程序开始后请勿更改购物车')

    @check_login
    def fastBuy(self):
        retry = self.retry
        for count in range(retry):
            logger.info('第[%s/%s]次尝试提交订单', count, retry)
            risk_control = self.get_checkout_page_detail()
            if risk_control == -1:
                continue
            if risk_control == '刷新太频繁了':
                return False
            if len(risk_control) > 0:
                if self.submit_order(risk_control):
                    return True
            logger.info('休息%ss', 5)
            time.sleep(5)
        else:
            logger.info('执行结束，提交订单失败！')
            return False

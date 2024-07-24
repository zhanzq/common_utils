# encoding=utf-8
# created @2024/4/28
# created by zhanzq
#

import re
import json
import time
import requests
from urllib.parse import quote
from common_utils.text_io.txt import load_from_json, save_to_json
from common_utils.const.web import USER_AGENT, COOKIE_XUANWU_DEV, COOKIE_XUANWU_TEST


class XuanWu:
    def __init__(self, domain_intent_to_id_path=None, slot_info_dct_path=None):
        if not domain_intent_to_id_path:
            domain_intent_to_id_path = "/Users/zhanzq/Documents/work_haier/data/domain_intent_to_id.json"
        if not slot_info_dct_path:
            slot_info_dct_path = "/Users/zhanzq/Documents/work_haier/data/slot_info.json"
        self.domain_intent_to_id_path = domain_intent_to_id_path
        self.slot_info_dct_path = slot_info_dct_path
        self.domain_intent_to_id = None
        self.slot_info_dct = None
        self.load_resource()

    def load_resource(self):
        self.get_domain_intent_to_id()
        self.get_slot_info_dct()

    def get_slot_info_dct(self):
        if not self.slot_info_dct:
            self.slot_info_dct = load_from_json(self.slot_info_dct_path)

        return self.slot_info_dct

    @staticmethod
    def _remove_slot_info(intent_info, slots_to_remove):
        slots = intent_info["nlpIntentSlots"]
        if type(slots_to_remove) is str:
            slots_to_remove = [slots_to_remove]

        remove_slot_ids = []
        new_slot_info = []
        for slot in slots:
            slot_code = slot.get("slotCode")
            if slot_code in slots_to_remove:
                remove_slot_ids.append(slot.get("id"))
            else:
                new_slot_info.append(slot)

        intent_info["nlpIntentSlots"] = new_slot_info
        intent_info["delNlpIntentSlotIds"] = ",".join(remove_slot_ids)

        return intent_info

    def remove_slot_from_xuanwu(self, domain, intent, slots_to_remove):
        """
        从玄武中删除意图中的一个或多个槽位
        :param domain: 领域code
        :param intent: 意图code
        :param slots_to_remove: 待删除的槽位名列表或字符串，如"temp", ["temp", "device"]
        :return:
        """
        # 获取intent所有信息
        intent_id = self.domain_intent_to_id.get(domain).get(intent).get("id")
        intent_info = self._get_detail_intent_info(intent_id)

        url = "https://aidev.haiersmarthomes.com/xuanwu-admin/jwt/intentSlot/saveDetail"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Content-Type": "application/json;charset=UTF-8",
            "Cookie": COOKIE_XUANWU_DEV,
            "User-Agent": USER_AGENT
        }
        method = "POST"
        data = self._remove_slot_info(intent_info=intent_info, slots_to_remove=slots_to_remove)
        payload = json.dumps(data)

        response = requests.request(method, url, headers=headers, data=payload)
        obj_resp = json.loads(response.text)

        return obj_resp

    def add_slot_into_xuanwu(self, domain, intent, slot_info_lst):
        """
        玄武中新增槽位信息
        :param domain:
        :param intent:
        :param slot_info_lst:
        :return:
        """
        intent_id = self.domain_intent_to_id.get(domain).get(intent).get("id")
        add_slot_lst = []
        for slot_info in slot_info_lst:
            slot_info.update({"intent_id": intent_id})
            # 构造槽位信息数据
            slot_item = self._construct_slot(slot_info=slot_info)
            add_slot_lst.append(slot_item)

        # 获取intent所有信息
        intent_info = self._get_detail_intent_info(intent_id)
        # 构造完整的待上传slot数据
        post_data = construct_auto_upload_slot_post_data(intent_info, new_slot_items=add_slot_lst)

        # 自动上传slot数据
        return self._auto_upload_slot(post_data)

    @staticmethod
    def _construct_slot(slot_info):
        data_type = slot_info.get("data_type", "String")
        slot_code = slot_info.get("slot_code")
        slot_name = slot_info.get("slot_name")
        dict_code = slot_info.get("dict_code")
        intent_id = slot_info.get("intent_id")
        must = slot_info.get("must", "N")
        single = slot_info.get("single", "N")
        slot_item = {
            'dataType': data_type,
            'dictCode': dict_code,
            'dnitId': intent_id,
            'slotCode': slot_code,
            'slotName': slot_name,
            "must": must,
            "single": single
        }

        return slot_item

    @staticmethod
    def add_intent_into_xuanwu(domain, intent, intent_name):
        """
        玄武中新增意图
        :param domain: 领域code
        :param intent: 意图code
        :param intent_name: 意图名称
        :return:
        """
        url = "https://aidev.haiersmarthomes.com/xuanwu-admin/jwt/domainIntent/add"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8",
            "Cookie": COOKIE_XUANWU_DEV,
            "User-Agent": USER_AGENT
        }
        method = "POST"
        data = {
            "domainCode": domain,
            "intentCode": intent,
            "intentName": intent_name,
            "commandCheckFlag": "N",
            "statusQueryFlag": "N",
            "functionQueryFlag": "N",
            "functionStatusQueryFlag": "N",
            "extend": "{}"
        }

        response = requests.request(url=url, method=method, headers=headers, data=json.dumps(data))
        obj_resp = json.loads(response.text)

        return obj_resp

    def auto_deploy(self, domain, env):
        """
        自动部署，使更新生效
        :param domain: 更新的领域
        :param env: 待部署的环境
        :return:
        """
        comment = "fb"
        if env == "sim":
            comment = f"同步{domain}"
        deploy_res = self._auto_deploy_template(env, comment=comment)
        curr_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(f"部署到{env}, comment: {comment}, time: {curr_time}")
        print(deploy_res)

        return deploy_res

    def domain_sync_to_sim(self, domains_to_sync):
        """
        领域同步
        :param domains_to_sync: 待同步到仿真的领域列表, 多个领域以‘,’分隔，如"Dev.oven,Steamer,BlockTemplate"
        :return:
        """
        if type(domains_to_sync) is str:
            if "," in domains_to_sync:
                domains_to_sync = domains_to_sync.split(",")
            else:
                domains_to_sync = [domains_to_sync]
        sync_res = self._domain_sync_to_sim(domains=domains_to_sync)
        curr_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(f"同步到仿真（模板数据: 验收 --> 仿真）, time: {curr_time}")
        print(sync_res)

        return

    def export_additional_data_from_dev(self,):
        """
        从开发环境导出新增数据（sql文件）
        :return:
        """
        url = "https://aidev.haiersmarthomes.com/xuanwu-admin/ver/dataRelease/exportUat"

        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cookie": COOKIE_XUANWU_DEV,
            "User-Agent": USER_AGENT,
            "X-Requested-With": "XMLHttpRequest"
        }
        method = "POST"
        payload = ""

        response = requests.request(method, url, headers=headers, data=payload)
        obj_resp = json.loads(response.text)
        data_file = obj_resp.get("data")
        if data_file:
            output_path = self._download_data_file_from_xuanwu(data_file)
            print(f"store file {data_file} into {output_path}")
            return obj_resp, output_path
        else:
            return obj_resp, None

    @staticmethod
    def import_additional_data_into_test(data_path):
        """
        导入新增数据到验收环境，数据包括模板和字典
        :param data_path: 新增数据文件
        :return:
        """
        url = 'https://aitest.haiersmarthomes.com/xuanwu-admin/ver/dataRelease/import'

        headers = {
            "Cookie": COOKIE_XUANWU_TEST,
            "User-Agent": USER_AGENT,
            "X-Requested-With": "XMLHttpRequest"
        }

        file_name = data_path.split("/")[-1]
        reader = open(data_path, "rb")
        files = {
            'file': (file_name, reader, 'application/octet-stream')
        }
        try:
            response = requests.post(url, headers=headers, files=files)
            print("import data into test finished!")
            print(response.text)
        except Exception as e:
            print(e)

        reader.close()
        return

    def get_domain_intent_to_id(self):
        # 加载domain_intent_to_id映射表
        if not self.domain_intent_to_id:
            self.domain_intent_to_id = load_from_json(self.domain_intent_to_id_path)

        return self.domain_intent_to_id

    def get_intent_info(self, domain, intent, verbose=True):
        """
        获取intent所有信息
        :param domain: 意图所属的领域代码
        :param intent: 意图代码
        :param verbose: 是否打印详细的日志信息，默认打印
        :return: slot_info, tpl_info
        """
        intent_id = self.domain_intent_to_id.get(domain).get(intent).get("id")
        if not intent_id:
            return None, None

        intent_info = self._get_detail_intent_info(intent_id)
        slot_info = parse_slot_info(intent_info, verbose=verbose)
        tpl_info = parse_template_lst(intent_info)

        return slot_info, tpl_info

    @staticmethod
    def template_exist(tpl_info, template):
        for tpl_item in tpl_info:
            if tpl_item["tpl"] == template:
                return True

        return False

    def edit_template(self, domain, intent, old_template, new_template):
        """
        插入模板
        :param domain: 意图所属的领域代码
        :param intent: 意图代码
        :param old_template: 修改前的模板
        :param new_template: 修改后的模板
        :return:
        """

        intent_id = self.domain_intent_to_id.get(domain).get(intent).get("id")

        if not intent_id:
            return "意图未找到"
        if not old_template or not new_template:
            return "新/旧模板为空值"

        found = False
        intent_info = self._get_detail_intent_info(intent_id)
        template_lst = intent_info["nlpTemlpateSlotVOS"]
        for tpl_item in template_lst:
            tpl_content = tpl_item.get("tplContent")
            if tpl_content == old_template:
                tpl_item["tplContent"] = new_template
                found = True
                break

        if not found:
            return "未找到旧的模板"

        # 自动上传tpl数据
        res = self._auto_upload_tpl(intent_info)

        return res

    def insert_template(self, domain, intent, template, slot_value_dct=None, overwrite=False):
        """
        插入模板
        :param domain: 意图所属的领域代码
        :param intent: 意图代码
        :param template: 待插入的模式列表，以'\n'分隔
        :param slot_value_dct: 模板对应的槽位默认值, 默认所有槽位无值
        :param overwrite: 是否覆盖已有模板，默认为False，即不覆盖
        :return:
        """

        intent_id = self.domain_intent_to_id.get(domain).get(intent).get("id")

        if not intent_id:
            return None, None
        if not template:
            return

        intent_info = self._get_detail_intent_info(intent_id)
        slot_info_dct = parse_slot_info(intent_info, verbose=False)
        # construct slot items
        slot_items = []
        if slot_value_dct:
            slot_items = self.construct_nlp_template_slot_items(slot_info_dct, slot_value_dct)
        tpl_info = parse_template_lst(intent_info)

        if not overwrite and self.template_exist(tpl_info, template):
            print(f"template '{template}' exists in XuanWu")
            return

        for tpl in template.split("\n"):
            # 获取intent所有信息
            intent_info = self._get_detail_intent_info(intent_id)
            tpl_item = self._construct_tpl(intent_id=intent_id, tpl_content=tpl, slot_items=slot_items)
            # old_tpl_num = len(intent_info['nlpTemlpateSlotVOS'])

            # 构造完整的待上传tpl数据
            post_data = construct_auto_upload_template_post_data(intent_info, tpl_item)
            # new_tpl_num = len(post_data['nlpTemlpateSlotVOS'])

            # 自动上传tpl数据
            self._auto_upload_tpl(post_data)

        return

    def update_domain_info(self, domain_to_update):
        """
        更新领域信息
        :param domain_to_update: 待更新的领域名称
        :return:
        """
        if not domain_to_update:
            return

        domain_intent_to_id = load_from_json(self.domain_intent_to_id_path)
        intent_to_id = self._get_intent_to_id_by_domain(domain=domain_to_update)
        if not intent_to_id:
            return
        domain_intent_to_id[domain_to_update] = intent_to_id
        save_to_json(json_obj=domain_intent_to_id, json_path=self.domain_intent_to_id_path)
        self.domain_intent_to_id = domain_intent_to_id

        return

    def _auto_deploy_template(self, env="dev", comment="fb"):
        comment = quote(comment)
        version = self._get_template_deploy_version(env=env)
        # print(f"deploy: env={env}, version= {version}")
        url = {
            "dev": "https://aidev.haiersmarthomes.com/xuanwu-admin/ver/deployTask/add",
            "test": "https://aitest.haiersmarthomes.com/xuanwu-admin/ver/deployTask/add",
            "sim": "https://aisim.haiersmarthomes.com/xuanwu-admin/ver/deployTask/add"
        }[env]

        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Cookie": COOKIE_XUANWU_DEV,
            "User-Agent": USER_AGENT,
            "X-Requested-With": "XMLHttpRequest"
        }
        method = "POST"
        payload = f"version={version}&remark={comment}"
        response = requests.request(method, url, headers=headers, data=payload)
        obj_resp = json.loads(response.text)

        return obj_resp

    @staticmethod
    def _auto_upload_tpl(post_data):
        url = "https://aidev.haiersmarthomes.com/xuanwu-admin/jwt/intentSlot/saveDetail"

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Content-Type": "application/json;charset=UTF-8",
            "Cookie": COOKIE_XUANWU_DEV,
            "User-Agent": USER_AGENT
        }
        payload = json.dumps(post_data)
        method = "POST"
        response = requests.request(method, url, headers=headers, data=payload)
        obj_resp = json.loads(response.text)

        return obj_resp

    @staticmethod
    def _auto_upload_slot(post_data):
        url = "https://aidev.haiersmarthomes.com/xuanwu-admin/jwt/intentSlot/saveDetail"

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Content-Type": "application/json;charset=UTF-8",
            "Cookie": COOKIE_XUANWU_DEV,
            "User-Agent": USER_AGENT
        }
        payload = json.dumps(post_data)
        method = "POST"

        response = requests.request(method, url, headers=headers, data=payload)
        obj_resp = json.loads(response.text)

        return obj_resp

    @staticmethod
    def _construct_nlp_template_slot_item(slot_info, slot_value):
        slot_item = {
            "isselect": False,
            "id": "",
            "itstId": slot_info.get("id"),
            "params": {
                "slotName": slot_info.get("slot_name"),
                "dictCode": slot_info.get("dict_code"),
                "slotCode": slot_info.get("slot_code")
            },
            "dictCode": slot_info.get("dict_code"),
            "slotCode": slot_info.get("slot_code"),
            "slotName": slot_info.get("slot_name"),
            "slotValue": slot_value
        }

        return slot_item

    def construct_nlp_template_slot_items(self, slot_info_dct, value_dct):
        slot_items = []
        for slot_code, slot_value in value_dct.items():
            if slot_code not in slot_info_dct:
                continue
            else:
                slot_items.append(self._construct_nlp_template_slot_item(slot_info_dct[slot_code], slot_value))

        return slot_items

    @staticmethod
    def _construct_tpl(intent_id, tpl_content, slot_items=None):
        if not slot_items:
            slot_items = []
        tpl_item = {
            'dnitId': intent_id,
            'entitySource': '',
            'id': '',
            'nlpTemplateSlots': slot_items,
            'status': '',
            'tplContent': tpl_content,
            'tplType': 'COMMON'
        }

        return tpl_item

    @staticmethod
    def _construct_slot(slot_info):
        data_type = slot_info.get("data_type", "String")
        slot_code = slot_info.get("slot_code")
        slot_name = slot_info.get("slot_name")
        dict_code = slot_info.get("dict_code")
        intent_id = slot_info.get("intent_id")
        must = slot_info.get("must", "N")
        single = slot_info.get("single", "N")
        slot_item = {
            'dataType': data_type,
            'dictCode': dict_code,
            'dnitId': intent_id,
            'slotCode': slot_code,
            'slotName': slot_name,
            "must": must,
            "single": single
        }

        return slot_item

    @staticmethod
    def _domain_sync_to_sim(domains):
        """
        领域同步
        :param domains: 待同步的领域列表
        :return:
        """
        domains = ",".join(domains)
        domains = quote(domains)
        url = "https://aitest.haiersmarthomes.com/xuanwu-admin/nlp/domain/domainSync"

        headers = {
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Cookie": COOKIE_XUANWU_DEV,
            "user-agent": USER_AGENT,
            "x-requested-with": "XMLHttpRequest"
        }
        method = "POST"
        payload = f"ids={domains}&env=k8ssim"

        response = requests.request(method, url, headers=headers, data=payload)

        obj_resp = json.loads(response.text)

        return obj_resp

    @staticmethod
    def _download_data_file_from_xuanwu(data_file):
        """
        从玄武平台下载数据文件
        :param data_file: 待下载的文件名称
        :return:
        """
        url = f"https://aidev.haiersmarthomes.com/xuanwu-admin/common/download?fileName={data_file}"

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;"
                      "q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cookie": COOKIE_XUANWU_DEV,
            "User-Agent": USER_AGENT
        }
        method = "GET"
        payload = ""

        response = requests.request(method, url, headers=headers, data=payload)

        output_path = f"/Users/zhanzq/Downloads/{data_file}"
        with open(output_path, "wb") as writer:
            writer.write(response.content)

        return output_path

    def _get_detail_intent_info(self, intent_id):
        url = f"https://aidev.haiersmarthomes.com/xuanwu-admin/jwt/intentSlot/detail?id={intent_id}"

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cookie": COOKIE_XUANWU_DEV,
            "User-Agent": USER_AGENT
        }
        method = "GET"
        payload = ""

        response = requests.request(method, url, headers=headers, data=payload)
        obj_resp = json.loads(response.text)
        intent_info = obj_resp["data"]
        intent_info = self._preprocess_detail_intent_info(intent_info)

        return intent_info

    @staticmethod
    def _get_intent_to_id_by_domain(domain):
        base_url = "https://aidev.haiersmarthomes.com/xuanwu-admin/jwt/workbench/intentList?"
        url = base_url + f"domainCode={domain}&pageNum=1&pageSize=1000"

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cookie": COOKIE_XUANWU_DEV,
            "User-Agent": USER_AGENT
        }
        method = "GET"
        payload = ""

        response = requests.request(method, url, headers=headers, data=payload)
        intent_info = json.loads(response.text)
        intent_to_id = parse_xuanwu_intent_info(intent_info)

        return intent_to_id

    @staticmethod
    def _get_template_deploy_version(env="dev"):
        url = {
            "dev": "https://aidev.haiersmarthomes.com/xuanwu-admin/ver/deployTask/add",
            "test": "https://aitest.haiersmarthomes.com/xuanwu-admin/ver/deployTask/add",
            "sim": "https://aisim.haiersmarthomes.com/xuanwu-admin/ver/deployTask/add"
        }[env]

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;"
                      "q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cookie": COOKIE_XUANWU_DEV,
            "User-Agent": USER_AGENT,
        }
        method = "GET"
        payload = ""

        response = requests.request(method, url, headers=headers, data=payload)

        version = re.findall(pattern="required value=\"([\d\.]+)\"", string=response.text)[0]

        return version

    def _preprocess_detail_intent_info(self, intent_info):
        obj = self._preprocess_desc_info(intent_info)
        obj = self._preprocess_intent_slots(obj)
        obj = self._preprocess_nlg_lst(obj)
        obj = self._preprocess_nlp_template(obj)

        return obj

    @staticmethod
    def _preprocess_desc_info(obj):
        obj["descInfo"] = '模板泛化'

        return obj

    @staticmethod
    def _preprocess_intent_slots(obj):
        intent_slots = obj["nlpIntentSlots"]
        for item in intent_slots:
            key_lst = list(item.keys())
            for key in key_lst:
                if key in ['searchValue', 'createBy', 'createTime', 'updateBy', 'updateTime', 'remark', 'response',
                           'slotIndex', 'preSlots', 'entitySource']:
                    item.pop(key)
                elif item[key] is None and key in ["action"]:
                    item[key] = ""
                if key == "params" and "dictType" in item[key]:
                    item[key].pop("dictType")

            item["redtips"] = False

        obj["nlpIntentSlots"] = intent_slots

        return obj

    @staticmethod
    def _preprocess_nlp_template(obj):
        tpl_items = obj["nlpTemlpateSlotVOS"]
        for tpl_item in tpl_items:
            keys = list(tpl_item.keys())
            for key in keys:
                if key in ["tplCode", "tplName"]:
                    tpl_item.pop(key)
                elif tpl_item[key] == "0" and key in ["status"]:
                    tpl_item[key] = ""
        obj["nlpTemlpateSlotVOS"] = tpl_items

        return obj

    @staticmethod
    def _preprocess_nlg_lst(obj):
        nlg_items = obj["nlpNlgIntentEnumList"]
        for nlg_item in nlg_items:
            keys = list(nlg_item.keys())
            for key in keys:
                if key in ['searchValue', 'createBy', 'createTime', 'updateBy', 'updateTime', 'remark', 'description',
                           'status', 'serviceType']:
                    nlg_item.pop(key)
                elif nlg_item[key] is None and key in ["action"]:
                    nlg_item[key] = ""

            nlg_item["tableRowKey"] = "nlgIntentId0"

        obj["nlpNlgIntentEnumList"] = nlg_items

        return obj


def parse_template_lst(intent_info):
    lst = []
    idx = 0
    for item in intent_info["nlpTemlpateSlotVOS"]:
        idx += 1
        out_item = {
            "idx": idx,
            "id": item["id"],
            "tpl": item["tplContent"]
        }
        lst.append(out_item)

    return lst


def construct_auto_upload_template_post_data(old_intent_info, new_tpl_item):
    # 构造待上传的完整数据
    old_intent_info["nlpTemlpateSlotVOS"].insert(0, new_tpl_item)

    return old_intent_info


def construct_auto_upload_slot_post_data(old_intent_info, new_slot_items):
    # 构造待上传的完整数据
    for item in new_slot_items:
        old_intent_info["nlpIntentSlots"].insert(0, item)

    return old_intent_info


def parse_slot_info(intent_info, verbose=True):
    detail_info = intent_info["nlpIntentSlots"]

    slot_info = {}
    for item in detail_info:
        slot_code = item["slotCode"]
        slot = {
            "id": item["id"],
            "slot_code": item["slotCode"],
            "slot_name": item["slotName"],
            "dict_code": item["dictCode"],
            "must": item["must"],
            "default_value": item["defaultValue"],
            "dict_name": item["params"].get("dictName"),
            "dict_type": item.get("dataType")
        }
        slot_info[slot_code] = slot

    if verbose:
        print(json.dumps(slot_info, indent=4, ensure_ascii=False))

    return slot_info


def parse_xuanwu_intent_info(intent_info):
    intent_lst = intent_info["rows"]
    out = {}
    for intent in intent_lst:
        code = intent["intentCode"]
        item = {
            "name": intent["intentName"],
            "id": intent["id"],
            "intent": code
        }
        out[code] = item

    return out


from common_utils.text_io.excel import load_json_list_from_xlsx


def main():
    xuanwu = XuanWu()
    xuanwu.get_intent_info(domain="Steamer", intent="increaseTemperature")
    data_path = "/Users/zhanzq/Documents/work_haier/data/玄武数据.xlsx"

    sheet_name = "slot_info"
    json_lst = load_json_list_from_xlsx(xlsx_path=data_path, sheet_names=[sheet_name])[sheet_name]

    category_lst = ["设备绑定", "留言板", "新闻", "菜谱", "日程闹钟", "闲聊", "找手机", "音乐电台", "股票查询", "限行",
                    "翻译", "天气"]

    life_skill_lst = []

    for item in json_lst:
        category_name = item.get("category_name")
        status = item.get("status")
        if category_name not in category_lst or status == "停用":
            continue
        else:
            domain = item.get("domain_code")
            intent = item.get("intent_code")
            slot_info, tpl_info = xuanwu.get_intent_info(domain=domain, intent=intent)
            item["slot_info"] = slot_info
            item["tpl_info"] = tpl_info
            life_skill_lst.append(item)


if __name__ == "__main__":
    main()


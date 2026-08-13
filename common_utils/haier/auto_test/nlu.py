# !/usr/bin/env python
# encoding=utf-8
# author: zhanzq
# email : zhanzhiqiang09@126.com 
# date  : 2023/3/18
#

import json
import requests
from common_utils.haier.auto_test.parse_log import LogParser
from common_utils.text_io.txt import load_from_json


class NLU:
    def __init__(self, simulation_device_path=None):
        """
        :param simulation_device_path: 模拟设备信息存储文件路径
        :return:
        """
        self.simulation_device_path = simulation_device_path
        self.simulation_devices = self.load_simulation_devices()
        self._session = requests.Session()
        self._session.trust_env = False

    def load_simulation_devices(self, simulation_device_path=None):
        """
        加载模拟的设备信息
        :param simulation_device_path: 模拟设备信息存储文件路径
        :return:
        """
        if simulation_device_path:
            self.simulation_device_path = simulation_device_path
        if self.simulation_device_path is None:
            self.simulation_device_path = "/Users/zhanzq/Documents/haier_data/simulation_devices.json"

        devices = load_from_json(json_path=self.simulation_device_path)
        lst = [f"{it['id']}|{it['nickname']}|{it['type']}|{it['floor']}|{it['room']}|{it['state']}" for it in devices]
        sim_devices = "#".join(lst)

        return sim_devices

    def get_nlu_service_response(self, query, env="local", device="X20"):
        """
        在特定环境中获取nlu的执行结果
        :param query: 输入语句
        :param env: 测试环境，local:开发, test:验收, sim:仿真, service:生产, 默认为本地开发环境
        :param device: 主控设备，即语音入口
        :return: dict, dm service处理结果
        """
        url = {
            "local": "http://desktop:11450/v2/nlu",  # 本地开发环境
            "test": "https://aitest.haiersmarthomes.com/nlu-service/v2/nlu",  # 验收环境
            "sim": "https://aisim.haiersmarthomes.com/nlu-service/v2/nlu",  # 仿真环境, not work
            "service": "https://aiservice.haier.net/nlu-service/v2/nlu"  # 生产环境, not work
        }[env]

        payload = json.dumps({
            "channel": device,
            "nickNameTable": {
                "deviceNickName": {
                    "gateway": "(智能网关五百三十一f|智能网关531f)"
                },
                "roomNickName": {
                    "roomPtn": "(洗漱间|卧室|客厅|全屋|厨房|阳台)"
                }
            },
            "otherParams": {
                "simulation": True,
                "neednlp": "yes",
                "rewakeStat": "",
                "multiDialog": "no",
                "specialNlp2": "yes",
                "screenState": "",
                "nlpmodel": "x20",
                "nlpType": "X20",
                "addQuestion": False,
                "needcontent": True,
                "isQuitMultContinueDialog": "no",
                "runStatus": "",
                "isMultiContinueDialog": "no",
                "userId": "3452436347",
                "agcKey": False,
                "forwardPass": False,
            },
            "originQuery": query,
            "query": query
        })
        headers = {
            'Content-Type': 'application/json',
            "auth": "access_nlp_12345678",
        }

        response = self._session.request("POST", url, headers=headers, data=payload)

        return json.loads(response.text)

    @staticmethod
    def parse_nlu_response(json_resp):
        nlu_info = {
            "query": None,
            "sn": None,
            "category": None,
            "domain": None,
            "intent": None,
            "slots": None
        }

        if "semantics" in json_resp and len(json_resp["semantics"]) > 0:
            semantics = json_resp["semantics"][0]
            nlu_info["query"] = semantics.get("text", None)
            nlu_info["sn"] = semantics.get("id", None)
            child_semantics = semantics.get("childSemantics", [])
            for it in child_semantics:
                domain = it.get("domain", None)
                intent = it.get("intent", None)
                slots = {slot["name"]: slot["value"] for slot in it.get("slots", [])}
                if domain != "NotSupport":
                    nlu_info["domain"] = domain
                    nlu_info["intent"] = intent
                    nlu_info["slots"] = slots
                    break

        return nlu_info

    def get_dm_service_response(self, query, env="service", device="X20", master_device_id="test_zzq", simulation=True, llm=True):
        """
        在特定环境中获取dm的执行结果
        :param query: 输入语句
        :param env: 测试环境，test:验收, sim:仿真, service:生产, 默认为生产环境
        :param device: 主控设备，即语音入口
        :param master_device_id: 主控设备id，默认为"test_zzq"
        :param simulation: 是否模拟设备信息，默认为True，表示具有各种设备
        :param llm: 是否使用llm模型，默认为True
        :return: dict, dm service处理结果
        """
        url = {
            "test": "https://aitest.haiersmarthomes.com/dialog-system/v2/dialog",
            "sim": "https://aisim.haiersmarthomes.com/dialog-system/v2/dialog",
            "service": "https://aiservice.haier.net/dialog-system/v2/dialog"
        }[env]
        payload = {
            "deviceType": device,
            "userInput": query,
            "otherParams": {
                "simulation": simulation,
                "familyId": "test_zzq",
                "dotId": "test_zzq",
            },
            "userId": "test_zzq",
            "masterDeviceId": master_device_id
        }
        if not simulation:
            payload["otherParams"]["simulationDevices"] = self.simulation_devices

        if llm:
            payload["otherParams"]["llm2"] = True
        payload = json.dumps(payload)
        headers = {
            'Content-Type': 'application/json',
            "auth": "access_nlp_12345678",
        }

        response = self._session.request("POST", url, headers=headers, data=payload)

        json_resp = json.loads(response.text)

        return json_resp

    def parse_dm_response(self, json_resp):
        """
        解析dm服务返回的结果
        :param json_resp: dict, dm服务返回结果
        :return: dict, keys包括sn, nlpVersion, query, domain, intent, slots, response
        """
        dm_info = {
            "query": json_resp.get("userQuery"),  # not None
            "sn": json_resp.get("sn"),  # not None
            "nlpVersion": json_resp.get("nlpVersion"), # not None
            "isDialog": json_resp.get("isDialog"), # not None
            "forwardPass": json_resp.get("forwardPass"),
            "errorCode": json_resp.get("errorCode"),
            "errorInfo": json_resp.get("errorInfo"),
            "category": json_resp.get("category", None),
            "domain": None,
            "intent": None,
            "slots": None,
            "response": json_resp.get("response")
        }
        # 如果errorCode和errorInfo为null, 则删掉这两个字段
        if not dm_info["errorCode"]:
            dm_info.pop("errorCode")
        if not dm_info["errorInfo"]:
            dm_info.pop("errorInfo")

        # 如果isDialog和forwardPass为False，则删掉这两个字段
        if not dm_info["isDialog"]:
            dm_info.pop("isDialog")
        if not dm_info["forwardPass"]:
            dm_info.pop("forwardPass")

        if "results" in json_resp and len(json_resp["results"]) > 0:
            params = json_resp["results"][0].get("params", {})
            dm_info.update(self._parse_dm_response_params(params))

        return dm_info

    def get_tpl_service_response(self, query):
        """
           在特定环境中获取template引擎的执行结果,目前只支持**开发环境**, <==> env = "dev", 且使用时需开启sico VPN
           :param query: 输入语句
           :return: dict, template处理结果
           """
        url = "http://10.205.241.186:11370/nlp-template-release/template/query"

        payload = json.dumps({
            "sn": "scene_test",
            "query": "",
            "originQuery": query,
            "nickNameTable": {
                "deviceNickName": {
                    "scenes": "(空调613A开关机状态开机|DEE2播放随机音乐)",
                    "airconditioner": "(挂式空调|空调22|空调2|空调3)"
                }
            }
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = self._session.request("POST", url, headers=headers, data=payload, timeout=2)

        json_resp = json.loads(response.text)

        return json_resp

    @staticmethod
    def parse_tpl_response(json_resp):
        return LogParser.get_semantics_info(json_resp)

    @staticmethod
    def _parse_dm_response_params(params):
        """
        解析dm服务返回的params字段
        :param params: dict, dm服务返回的params字段
        :return: dict, keys包括domain, intent, slots
        """
        out_item = {
            "domain": None,
            "intent": None,
            "slots": {}
        }
        # 删除为空的字段
        params = {k: v for k, v in params.items() if v}
        # 删除无用的字段
        params.pop("errorCode", None)
        params.pop("errorInfo", None)
        params.pop("internalDomain", None)
        params.pop("cloudDomain", None)

        out_item["domain"] = params.pop("domain", None)
        out_item["intent"] = params.pop("action", None)

        if params:
            out_item["slots"].update(params)
        else:
            out_item.pop("slots", None)

        return out_item


def main():
    query = "帮我煮果茶10分钟"

    parser = NLU()
    # do dm
    dm_resp = parser.get_dm_service_response(query, env="test")
    dm_info = parser.parse_dm_response(dm_resp)
    print(f"dm_info: \n{dm_info}\n")

    # do nlu
    nlu_resp = parser.get_nlu_service_response(query, env="test")
    nlu_info = parser.parse_nlu_response(nlu_resp)
    print(f"nlu_info: \n{nlu_info}\n")

    # do tpl
    tpl_resp = parser.get_tpl_service_response(query)
    tpl_info = parser.parse_tpl_response(tpl_resp)
    print(f"tpl_info: \n{tpl_info}\n")
    return


if __name__ == "__main__":
    main()

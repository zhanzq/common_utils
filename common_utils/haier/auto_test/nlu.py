# !/usr/bin/env python
# encoding=utf-8
# author: zhanzq
# email : zhanzhiqiang09@126.com 
# date  : 2023/3/18
#

import json
import requests


def get_nlu_service_response(query, env="local"):
    """
    在特定环境中获取nlu的执行结果
    :param query: 输入语句
    :param env: 测试环境，local:开发, test:验收, sim:仿真, service:生产, 默认为本地开发环境
    :return: dict, dm service处理结果
    """
    url = {
        "local": "http://desktop:11450/v2/nlu",  # 本地开发环境
        "test": "https://aitest.haiersmarthomes.com/nlu-service/v2/nlu",  # 验收环境
        "sim": "https://aisim.haiersmarthomes.com/nlu-service/v2/nlu",  # 仿真环境, not work
        "service": "https://aiservice.haier.net/nlu-service/v2/nlu"  # 生产环境, not work
    }[env]

    payload = json.dumps({
        "channel": "X20",
        "nickNameTable": {
            "deviceNickName": {
                "gateway": "(智能网关五百三十一f|智能网关531f)"
            },
            "roomNickName": {
                "roomPtn": "(洗漱间|卧室|客厅|全屋|厨房|阳台)"
            }
        },
        "originQuery": query,
        "query": query
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return json.loads(response.text)


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


def get_dm_service_response(query, env="service"):
    """
    在特定环境中获取dm的执行结果
    :param query: 输入语句
    :param env: 测试环境，test:验收, sim:仿真, service:生产, 默认为生产环境
    :return: dict, dm service处理结果
    """
    url = {
        "test": "https://aitest.haiersmarthomes.com/dialog-system/v2/dialog",
        "sim": "https://aisim.haiersmarthomes.com/dialog-system/v2/dialog",
        "service": "https://aiservice.haier.net/dialog-system/v2/dialog"
    }[env]
    payload = json.dumps({
        "deviceType": "X20",
        "applyChannel": "X20",
        "dotId": "BOX0000412313123",
        "masterDeviceId": "C8631420033333123123",
        "clientId": "C8631420033333123123",
        "token": "cb94786ec5414d068d78612c9aa6a061",
        "familyId": "279193340561000000",
        "otherParams": {
            "neednlp": "yes",
            "rewakeStat": "",
            "multiDialog": "no",
            "specialNlp2": "yes",
            "nlpmodel": "X20",
            "nlpType": "X20",
            "addQuestion": False,
            "needcontent": True,
            "isQuitMultContinueDialog": "no",
            "screenState1": "zhinengchuanda_photo",
            "runStatus": "",
            "isMultiContinueDialog": "no",
            "deviceActionCategory2": "Regex",
            "agcKey": False,
            "simulation": True,
            "forwardPass": False
        },
        "userInput": query,
        "userId": "10052057871212211121"
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    json_resp = json.loads(response.text)

    return json_resp


def parse_dm_response(json_resp):
    """
    解析dm服务返回的结果
    :param json_resp: dict, dm服务返回结果
    :return: dict, keys包括sn, query, domain, intent, slots, response
    """
    dm_info = {
        "query": json_resp.get("userQuery"),  # not None
        "sn": json_resp.get("sn"),  # not None
        "category": json_resp.get("category", None),
        "domain": None,
        "intent": None,
        "slots": None,
        "response": json_resp.get("response")
    }
    if "results" in json_resp and len(json_resp["results"]) > 0:
        params = json_resp["results"][0].get("params", {})
        dm_info.update(_parse_dm_response_params(params))

    return dm_info


def _parse_dm_response_params(params):
    out_item = {
        "domain": None,
        "intent": None,
        "slots": None
    }
    if params:
        params.pop("errorCode", None)
        params.pop("errorInfo", None)
        params.pop("internalDomain", None)
        out_item["domain"] = params.pop("domain", None)
        out_item["intent"] = params.pop("action", None)
        out_item["slots"] = params

    return out_item


def main():
    query = "打开三楼的电暖桌"

    # do nlu
    nlu_resp = get_nlu_service_response(query, env="test")
    nlu_info = parse_nlu_response(nlu_resp)
    print(f"nlu_info: \n{nlu_info}\n")

    dm_resp = get_dm_service_response(query, env="test")
    dm_info = parse_dm_response(dm_resp)
    print(f"dm_info: \n{dm_info}\n")
    return


if __name__ == "__main__":
    main()

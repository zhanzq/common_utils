# !/usr/bin/env python
# encoding=utf-8
# author: zhanzq
# email : zhanzhiqiang09@126.com 
# date  : 2023/3/18
#


import time
import json
import requests
from common_utils.utils import format_string


# 解析日志信息
def _parse_log_id(log_id_ret):
    """
    解析日志id信息，输出映射字典；key为服务名，value为对应的日志id
    :param log_id_ret: 完整的日志信息
    :return: dict()
    """
    log_id_map = {}
    data = log_id_ret.get("data", {})
    lst = data.get("list", [])
    for item in lst:
        service = item.get("path", None)
        log_id = item.get("logId", None)
        if service and log_id:
            log_id_map[service] = log_id

    return log_id_map


def get_log_id(sn, env="test"):
    """
    获取日志id信息
    :param sn: 请求的sn号
    :param env: 请求的执行环境, default="test"
    :return: dict()
    """
    # date: 服务日志写入时间, 格式为"%Y%m%d",如"2023-03-08"
    date = f"{sn[1:5]}-{sn[5:7]}-{sn[7:9]}"
    if env == "test":
        url_base = "https://aitest.haiersmarthomes.com:11001/bomp-logdata-adapter/datalog/getlogList"
    elif env == "sim":
        url_base = "https://aisim.haiersmarthomes.com/bomp-logdata-adapter/datalog/getlogList"
    else:
        url_base = "https://aiservice.haier.net/bomp-logdata-adapter/datalog/getlogList"

    url = url_base + f"?startDate={date}+00:00&accept={sn}&pageNum=1&pageSize=30"
    payload = {}
    headers = {}

    for _ in range(10):
        try:
            response = requests.request("GET", url, headers=headers, data=payload)
            log_id_ret = json.loads(response.text)
            log_id_map = _parse_log_id(log_id_ret)
            return log_id_map
        except TypeError:
            time.sleep(5)

    return {}


def get_service_info(sn, log_id_map, service_name, env="test"):
    """
    获取具体服务的结果信息
    :param sn: 请求的sn号
    :param log_id_map: 各服务的id信息字典
    :param service_name: 服务名称，如"NluTemplate:nlu"
    :param env: 请求的执行环境, default="test"
    """

    # date: 服务日志写入时间, 格式为"%Y%m%d",如"20230308"
    date = sn[1:9]
    log_id = log_id_map.get(service_name)
    if env == "test":
        url_base = "https://aitest.haiersmarthomes.com:11001/bomp-logdata-adapter/datalog/getHbaseChainLogDetail"
    elif env == "sim":
        url_base = "https://aisim.haiersmarthomes.com/bomp-logdata-adapter/datalog/getHbaseChainLogDetail"
    else:
        url_base = "https://aiservice.haier.net/bomp-logdata-adapter/datalog/getHbaseChainLogDetail"

    url = url_base + f"?id={log_id}&date={date}&sn={sn}"
    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)

    service_info = json.loads(response.text)
    return service_info


def _parse_tpl_match_semantics(child_semantics):
    """
    获取匹配成功的模板信息
    :param child_semantics: 模板匹配的语义信息
    """
    domain = child_semantics["domain"]
    intent = child_semantics["intent"]
    intent_score = child_semantics["intentScore"]
    slots = {it["name"]: it["value"] for it in child_semantics["slots"]}
    tpl_id, tpl = child_semantics["source"].split(":")

    simple_semantics = {"domain": domain, "intent": intent, "intent_score": intent_score, "slots": slots,
                        "tpl_id": tpl_id, "tpl": tpl}

    return simple_semantics


def rm_block_semantics(semantics):
    """
    过滤nlu_info中的Block类语义信息，如
    :param semantics: 待过滤的语义信息
    :return:
    """
    filtered = []
    for semantic in semantics:
        if "block" not in semantic.get("domain", "").lower():
            filtered.append(semantic)

    return filtered


def rm_internal_command(semantics):
    """
    过滤nlu_info中的InternalCommand类语义信息
    :param semantics: 待过滤的语义信息
    :return:
    """
    filtered = []
    for semantic in semantics:
        if "domain" in semantic and semantic["domain"] != "InternalCommand":
            filtered.append(semantic)

    return filtered


def rm_extract_domain(nlu_info):
    """
    过滤nlu_info中的Extract类的领域信息，如"ExtractNer", "ExtractExecutorType"
    :param nlu_info: 待过滤的nlu信息
    :return:
    """
    filtered = []
    for it in nlu_info:
        if "domain" in it and it["domain"] and not it["domain"].startswith("Extract"):
            filtered.append(it)

    return filtered


def get_tpl_match_result(sn, env="test"):
    """
    获取模板匹配NluTemplate:nlu结果
    :param sn: 请求的sn号
    :param env: 请求的执行环境, default="test"
    """
    print(format_string(f"template match result: env={env}, sn={sn}"))
    log_id_map = get_log_id(sn, env)

    service_name = "NluTemplate:nlu"
    service_info = get_service_info(sn, log_id_map, service_name, env)
    data = service_info.get("data", {})
    # req = json.loads(data["reqBody"]) if "reqBody" in data else None
    # param = data.get("reqParam", None)
    resp = json.loads(data["response"]) if "response" in data else None
    semantics = resp.get("semantics", [])
    simple_semantics = None
    if semantics:
        child_semantics = semantics[0]["childSemantics"]
        simple_semantics = [_parse_tpl_match_semantics(it) for it in child_semantics]

    simple_semantics = rm_block_semantics(simple_semantics)
    simple_semantics = rm_extract_domain(simple_semantics)
    simple_semantics = rm_internal_command(simple_semantics)
    if simple_semantics:
        simple_semantics = json.dumps(simple_semantics, indent=4, ensure_ascii=False)
    print(simple_semantics)

    return simple_semantics


def parse_nlu_info_from_log(child_semantics):
    """
    获取nlu结果
    :param child_semantics: nlu的语义信息，格式如下：
    {
        "intentScore":0.0,
        "slots":[
            {"name":"action","start":0,"end":0,"type":"String","value":"decrease","normValue":"decrease"},
            {"name":"device","start":2,"end":5,"type":"String","value":"电暖桌","normValue":"电暖桌"},
            {"name":"type","start":0,"end":0,"type":"String","value":"温度","normValue":"温度"},
            {"name":"unite","start":0,"end":0,"type":"String","value":"0","normValue":"0"}
        ],
        "systemSlotEmpty":true,
        "hasDeviceNickname":false,
        "domain":"ElectricHeatingTable",
        "channel":"nlu_unlu",
        "intent":"decreaseWarmGear"
    }
    """
    slots = child_semantics.get("slots", [])
    slots = {it["name"]: it.get("value", None) for it in slots}
    nlu_info = {
        "domain": child_semantics.get("domain", None),
        "intent": child_semantics.get("intent", None),
        "slots": slots,
        "intent_score": child_semantics.get("intentScore", 0),
    }

    return nlu_info


def get_log_trace_info_from_log(sn, env="test"):
    """
    获取dialog-system:LogTrace服务的结果
    :param sn: 请求的sn号
    :param env: 请求的执行环境, default="test"
    """
    print(format_string(f"log trace info: env={env}, sn={sn}"))
    log_id_map = get_log_id(sn, env)
    service_name = "dialog-system:LogTrace"

    service_info = get_service_info(sn, log_id_map, service_name, env)
    data = service_info.get("data", {})
    # req = json.loads(data["reqBody"]) if "reqBody" in data else None
    # param = data.get("reqParam", None)
    resp = json.loads(data["response"]) if "response" in data else None

    log_trace_info = json.dumps(resp, ensure_ascii=False, indent=4)
    log_trace_info = log_trace_info.replace("\\r", "\r")
    log_trace_info = log_trace_info.replace("\\n", "\n")
    log_trace_info = log_trace_info.replace("\\t", "\t")
    print(log_trace_info)

    return log_trace_info


def get_do_nlu_info_from_log(sn, env="test"):
    """
    获取dialog-system:doNlu服务的结果
    :param sn: 请求的sn号
    :param env: 请求的执行环境, default="test"
    """
    print(format_string(f"do_nlu info: env={env}, sn={sn}"))
    log_id_map = get_log_id(sn, env)
    service_name = "dialog-system:doNlu"

    service_info = get_service_info(sn, log_id_map, service_name, env)
    data = service_info.get("data", {})
    # req = json.loads(data["reqBody"]) if "reqBody" in data else None
    # param = data.get("reqParam", None)
    resp = json.loads(data["response"]) if "response" in data else None
    semantics = resp.get("semantics", [])
    nlu_info = None
    if semantics:
        child_semantics = semantics[0]["childSemantics"]
        nlu_info = [parse_nlu_info_from_log(it) for it in child_semantics]

    # filter unimportant semantics
    nlu_info = rm_extract_domain(nlu_info)
    nlu_info = rm_internal_command(nlu_info)
    if nlu_info:
        nlu_info = json.dumps(nlu_info, indent=4, ensure_ascii=False)
    print(nlu_info)

    return nlu_info


def main():
    env = "test"
    sn = "t20230425170334806661466624"
    get_do_nlu_info_from_log(sn, env)

    get_tpl_match_result(sn, env)

    get_log_trace_info_from_log(sn, env)
    return


if __name__ == "__main__":
    main()

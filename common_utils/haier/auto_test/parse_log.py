# !/usr/bin/env python
# encoding=utf-8
# author: zhanzq
# email : zhanzhiqiang09@126.com 
# date  : 2023/3/18
#


import hashlib
import time
import json
import requests

from common_utils.const.web import USER_AGENT
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


def get_sign(url, timestamp):
    """
    生产环境的日志系统计算签名signature
    :param url:
    :param timestamp:
    :return:
    """
    n = url.split("?")[0]
    e = "b407eb2f-7ee5-44b2-afc8-780e82764185"
    input_string = n + str(timestamp) + e
    sign = hashlib.sha256(input_string.encode()).hexdigest()

    return sign


def get_log_id(sn, env="test"):
    """
    获取日志id信息
    :param sn: 请求的sn号
    :param env: 请求的执行环境, default="test"
    :return: dict()
    """
    # date: 服务日志写入时间, 格式为"%Y%m%d",如"2023-03-08"
    date_start = 0
    while sn[date_start] != '2':
        date_start += 1
    date = f"{sn[date_start:date_start+4]}-{sn[date_start+4:date_start+6]}-{sn[date_start+6:date_start+8]}"

    if env == "test":
        url_base = "https://aitest.haiersmarthomes.com:11001/bomp-logdata-adapter/datalog/getlogList"
    elif env == "sim":
        url_base = "https://aisim.haiersmarthomes.com/bomp-logdata-adapter/datalog/getlogList"
    elif env == "service":
        url_base = "https://aiservice.haier.net/bomp-logdata-adapter/datalog/getlogList"

    url = url_base + f"?startDate={date}+00:00&accept={sn}&pageNum=1&pageSize=30"
    payload = {}
    timestamp = time.time_ns()//10**6
    sign = get_sign(url=url, timestamp=str(timestamp))
    headers = {
        "sign": sign,
        "timestamp": str(timestamp),
        "user-agent": USER_AGENT
    }

    for _ in range(3):
        try:
            response = requests.request("GET", url, headers=headers, data=payload)
            log_id_ret = json.loads(response.text)
            log_id_map = _parse_log_id(log_id_ret)
            return log_id_map
        except TypeError:
            time.sleep(1)

    return {}


def parse_nlu_receiver_info_from_log(resp_nlu_receiver):
    # multi_media_semantics = resp_nlu_receiver.get("multiMediaResult").get("semantics")[0]
    model_nlu_semantics = resp_nlu_receiver.get("modelNluResult").get("semantics")[0]
    # ccg_semantics = resp_nlu_receiver.get("ccgNluResult").get("semantics")[0]
    tpl_nlu_semantics = resp_nlu_receiver.get("templateNluResult").get("semantics")[0]
    nlu_receiver_info = {
        # "multi_media": [parse_nlu_info_from_log(it) for it in multi_media_semantics.get("childSemantics", [])],
        "model_nlu": [parse_nlu_info_from_log(it) for it in model_nlu_semantics.get("childSemantics", [])],
        # "ccg": [parse_nlu_info_from_log(it) for it in ccg_semantics.get("childSemantics", [])],
        "tpl_nlu": [parse_nlu_info_from_log(it) for it in tpl_nlu_semantics.get("childSemantics", [])],
    }

    return nlu_receiver_info


def _parse_service_info(service_info):
    data = service_info.get("data", {})
    req = json.loads(data["reqBody"]) if "reqBody" in data else {}
    param = req.get("args0", req)
    if "query" in param:
        query = param["query"]
    else:
        query = param.get("userInput", None)

    resp = json.loads(data["response"]) if "response" in data else None
    resp = resp.get("resp", resp)

    return query, resp


def get_query_by_sn(sn, env="test", verbose=False):
    """
        获取dialog-system:NluReceiver服务的结果
        :param sn: 请求的sn号
        :param env: 请求的执行环境, default="test"
        :param verbose: 是否打印详细信息, 默认不打印
        """
    log_id_map = get_log_id(sn, env)
    if not log_id_map:
        return None
    service_name = "dialog-system:NluReceiver"
    service_info = get_service_info(sn, log_id_map, service_name, env)
    query, _ = _parse_service_info(service_info)
    if verbose:
        print_info = {
            "env": env,
            "sn": sn,
            "query": query
        }
        print_info = json.dumps(print_info, indent=4, ensure_ascii=False)
        print(print_info)

    return query


def get_nlu_receiver_info_from_log(sn, env="test", verbose=False):
    """
        获取dialog-system:NluReceiver服务的结果
        :param sn: 请求的sn号
        :param env: 请求的执行环境, default="test"
        :param verbose: 是否打印详细信息, 默认不打印
        """
    log_id_map = get_log_id(sn, env)
    if not log_id_map:
        return None
    service_name = "dialog-system:NluReceiver"
    service_info = get_service_info(sn, log_id_map, service_name, env)
    query, resp = _parse_service_info(service_info)
    print(format_string(f"nlu receiver info: env={env}, query={query}"))

    nlu_receiver_info = parse_nlu_receiver_info_from_log(resp_nlu_receiver=resp)

    # filter unimportant semantics
    for key in nlu_receiver_info:
        nlu_receiver_info[key] = rm_extract_domain(nlu_receiver_info[key])
        nlu_receiver_info[key] = rm_internal_command(nlu_receiver_info[key])
        nlu_receiver_info[key] = rm_block_semantics(nlu_receiver_info[key])

    if nlu_receiver_info:
        print_info = json.dumps(nlu_receiver_info, indent=4, ensure_ascii=False)

        if verbose:
            print(print_info)

    return nlu_receiver_info


def get_service_info(sn, log_id_map, service_name, env="test"):
    """
    获取具体服务的结果信息
    :param sn: 请求的sn号
    :param log_id_map: 各服务的id信息字典
    :param service_name: 服务名称，如"NluTemplate:nlu"
    :param env: 请求的执行环境, default="test"
    """

    # date: 服务日志写入时间, 格式为"%Y%m%d",如"20230308"
    date_start = 0
    while sn[date_start] != '2':
        date_start += 1
    date = f"{sn[date_start:date_start+8]}"

    log_id = log_id_map.get(service_name)
    if env == "test":
        url_base = "https://aitest.haiersmarthomes.com:11001/bomp-logdata-adapter/datalog/getHbaseChainLogDetail"
    elif env == "sim":
        url_base = "https://aisim.haiersmarthomes.com/bomp-logdata-adapter/datalog/getHbaseChainLogDetail"
    elif env == "service":
        url_base = "https://aiservice.haier.net/bomp-logdata-adapter/datalog/getHbaseChainLogDetail"

    url = url_base + f"?id={log_id}&date={date}&sn={sn}"
    payload = {}
    timestamp = time.time_ns()//10**6
    sign = get_sign(url=url, timestamp=str(timestamp))

    headers = {
        "sign": sign,
        "timestamp": str(timestamp),
        "user-agent": USER_AGENT
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    service_info = json.loads(response.text)
    return service_info


def get_semantics(resp_obj, clean=True):
    """
    获取服务（如nlu, dm, template等）返回的结果中的semantics信息，并进行过滤
    :param resp_obj: 服务返回的json格式数据
    :param clean: 过滤不必要的类型，如Block类，Internal类等，默认为True
    :return:
    """
    if not resp_obj or "semantics" not in resp_obj or not resp_obj["semantics"]:
        return []

    semantics = []
    if clean:
        for item in resp_obj["semantics"]:
            if not item or "childSemantics" not in item or not item["childSemantics"]:
                continue

            child_semantics = item["childSemantics"]
            child_semantics = rm_block_semantics(child_semantics)
            child_semantics = rm_internal_command(child_semantics)
            child_semantics = rm_extract_domain(child_semantics)
            semantics.extend(child_semantics)

    return semantics


def get_semantics_info(resp_obj):
    semantics = get_semantics(resp_obj)
    channel = resp_obj["retChannel"]
    if channel == "nluTemplate":
        semantics_info = [_parse_tpl_match_semantic(it) for it in semantics]
    else:
        semantics_info = [parse_nlu_info_from_log(it) for it in semantics]

    return semantics_info


def _parse_tpl_match_semantic(child_semantic):
    """
    获取匹配成功的模板信息
    :param child_semantic: 模板匹配的语义信息
    """
    domain = child_semantic["domain"]
    intent = child_semantic["intent"]
    intent_score = child_semantic["intentScore"]
    slots = {it["name"]: it["value"] for it in child_semantic["slots"]}
    lst = child_semantic["source"].split(":")
    tpl_id = lst[0]
    tpl = ":".join(lst[1:])

    simple_semantics = {"domain": domain, "intent": intent, "intent_score": intent_score, "slots": slots,
                        "tpl_id": tpl_id, "tpl": tpl}

    return simple_semantics


def rm_block_semantics(semantics):
    """
    过滤nlu_info中的Block类语义信息，如**BlockTemplate**
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


def get_tpl_match_info_from_log(sn, env="test", verbose=False):
    """
    获取模板匹配NluTemplate:nlu结果
    :param sn: 请求的sn号
    :param env: 请求的执行环境, default="test"
    :param verbose: 是否打印详细日志信息，默认为不打印
    """
    log_id_map = get_log_id(sn, env)
    if not log_id_map:
        return None

    service_name = "NluTemplate:nlu"
    service_info = get_service_info(sn, log_id_map, service_name, env)
    query, resp = _parse_service_info(service_info)

    print(format_string(f"template match result: env={env}, query={query}"))
    semantics = resp.get("semantics", [])
    simple_semantics = None
    if semantics:
        child_semantics = semantics[0]["childSemantics"]
        simple_semantics = [_parse_tpl_match_semantic(it) for it in child_semantics]

    simple_semantics = rm_block_semantics(simple_semantics)
    simple_semantics = rm_extract_domain(simple_semantics)
    simple_semantics = rm_internal_command(simple_semantics)
    if simple_semantics:
        print_info = json.dumps(simple_semantics, indent=4, ensure_ascii=False)
        if verbose:
            print(print_info)

    return simple_semantics


def _block_check_by_domain(semantics, domain):
    """
    过滤nlu_info中的Block类语义信息，如**BlockTemplate**
    :param semantics: 待过滤的语义信息
    :param domain: 待检查的领域
    :return:
    """
    filtered = []
    for semantic in semantics:
        cur_domain = semantic.get("intent", "").lower()
        # 完全匹配检查
        if cur_domain == f"block{domain.lower()}":
            filtered.append(semantic)

    return filtered


def block_check(sn, domain_lst, env="test", verbose=False):
    """
    获取模板匹配NluTemplate:nlu结果
    :param sn: 请求的sn号
    :param domain_lst: 需要检查的领域
    :param env: 请求的执行环境, default="test"
    :param verbose: 是否打印详细日志信息，默认为不打印
    """
    log_id_map = get_log_id(sn, env)
    if not log_id_map:
        return None

    service_name = "NluTemplate:nlu"
    service_info = get_service_info(sn, log_id_map, service_name, env)
    query, resp = _parse_service_info(service_info)

    print(format_string(f"block check: domains: {domain_lst}, env={env}, query={query}"))
    semantics = resp.get("semantics", [])
    simple_semantics = []
    if semantics:
        child_semantics = semantics[0]["childSemantics"]
        simple_semantics = [_parse_tpl_match_semantic(it) for it in child_semantics]

    blocked_semantics = []
    for domain in domain_lst:
        blocked_semantics.extend(_block_check_by_domain(simple_semantics, domain))
    if blocked_semantics:
        print_info = json.dumps(blocked_semantics, indent=4, ensure_ascii=False)
        if verbose:
            print(print_info)

    return blocked_semantics


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


def get_log_trace_info_from_log(sn, env="test", verbose=False):
    """
    获取dialog-system:LogTrace服务的结果
    :param sn: 请求的sn号
    :param env: 请求的执行环境, default="test"
    :param verbose: 是否打印日志信息，默认为不打印
    """
    log_id_map = get_log_id(sn, env)
    if not log_id_map:
        return None

    service_name = "dialog-system:LogTrace"
    service_info = get_service_info(sn, log_id_map, service_name, env)
    query, resp = _parse_service_info(service_info)
    print(format_string(f"log trace info: env={env}, query={query}"))

    log_trace_info = json.dumps(resp, ensure_ascii=False, indent=4)
    log_trace_info = log_trace_info.replace("\\r", "\r")
    log_trace_info = log_trace_info.replace("\\n", "\n")
    log_trace_info = log_trace_info.replace("\\t", "\t")
    if verbose:
        print(log_trace_info)

    return log_trace_info


def get_do_nlu_info_from_log(sn, env="test", verbose=False):
    """
    获取dialog-system:doNlu服务的结果
    :param sn: 请求的sn号
    :param env: 请求的执行环境, default="test"
    :param verbose: 是否打印日志信息，默认为不打印
    """
    log_id_map = get_log_id(sn, env)
    service_name = "dialog-system:doNlu"
    service_info = get_service_info(sn, log_id_map, service_name, env)
    query, resp = _parse_service_info(service_info)
    print(format_string(f"do_nlu info: env={env}, query={query}"))

    semantics = resp.get("semantics", [])
    nlu_info = None
    if semantics:
        child_semantics = semantics[0]["childSemantics"]
        nlu_info = [parse_nlu_info_from_log(it) for it in child_semantics]

    if nlu_info:
        # filter unimportant semantics
        nlu_info = rm_extract_domain(nlu_info)
        nlu_info = rm_internal_command(nlu_info)

        print_info = json.dumps(nlu_info, indent=4, ensure_ascii=False)
        if verbose:
            print(print_info)

    return nlu_info


def main():
    env = "service"
    sn = "t20240206145925940281423872"
    domain_lst = ["Dev.oven", ""]
    block_check(sn, domain_lst, env, verbose=True)

    get_nlu_receiver_info_from_log(sn, env, verbose=True)

    get_do_nlu_info_from_log(sn, env, verbose=True)

    get_tpl_match_info_from_log(sn, env, verbose=True)

    get_log_trace_info_from_log(sn, env, verbose=True)
    return


if __name__ == "__main__":
    main()

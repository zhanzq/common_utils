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
import yaml

from common_utils.const.web import USER_AGENT
from common_utils.utils import format_string


def json_to_yaml(data):
    stra = json.dumps(data)
    dyaml = yaml.load(stra, Loader=yaml.FullLoader)

    return dyaml


class LogParser:
    def __init__(self, sn=None, env="test"):
        self._mid_sn = None
        self._sn = sn
        self._env = env
        self._log_id_map = {}

    def update_config(self, **kwargs):
        if "sn" in kwargs:
            self._sn = kwargs.get("sn")
            self._update_log_id_map()
        if "env" in kwargs:
            self._env = kwargs.get("env")

    def _update_log_id_map(self):
        self._log_id_map = self.get_log_id(self._sn)

    def get_log_id_map(self):
        if not self._log_id_map:
            self._update_log_id_map()

        return self._log_id_map

    def get_simulation_device_lst(self):
        req_body = self.get_request_body()
        device_lst = req_body.get("otherParams").get("simulationDevices")
        master_device_id = req_body.get("masterDeviceId")
        if device_lst:
            # 有模拟设备信息
            device_infos = []
            for device_info in device_lst.split("#"):
                device_info = device_info.split("|")
                try:
                    info = {}
                    info["deviceId"] = device_info[0]
                    info["deviceName"] = device_info[1]
                    info["deviceType"] = device_info[2]
                    info["floor"] = device_info[3]
                    info["room"] = device_info[4]
                    info["online"] = device_info[5] != "false" and device_info[5] != "0"
                    device_infos.append(info)
                except Exception as e:
                    print(e)
            return master_device_id, device_infos
        else:
            return None, []

    def get_scene_lst(self, verbose=False):
        service_name = "IftttExecService:querySceneInfo"
        scene_lst = []
        try:
            resp = self.get_service_info(service_name=service_name)
            scene_resp = json.loads(resp.get("data").get("response"))
            scene_lst = [it.get("sceneName") for it in scene_resp.get("sceneDtos")]
        except Exception as e:
            print(e)

        if verbose:
            print("场景列表信息：")
            print(", ".join(scene_lst))
            print("\n\n")
        return scene_lst

    def get_device_lst(self, by_type=True, verbose=False):
        """
        获取用户的设备列表信息
        :param by_type: 是否按设备类型返回设备列表，默认为True
        :param verbose: 是否打印详细信息, 默认不打印
        :return: master_device_info: 主控设备信息, device_info：设备列表分类的yaml格式, device_lst：详细的设备列表信息
        """
        master_device_id, device_lst = self.get_simulation_device_lst()
        if not master_device_id or not device_lst:
            service_name = "DataCenterDubboServiceImpl:dateResult"
            resp_obj = self.get_service_info(service_name=service_name)
            resp = json.loads(resp_obj["data"]["response"])
            rooms = resp.get("roomResponse", {})
            device_lst = rooms.get("deviceRoomInfos", [])
            master_device_id = resp_obj.get("data").get("deviceId")

        master_device_info = self._get_master_device_info(master_device_id=master_device_id, device_lst=device_lst)
        device_infos = []
        for device in device_lst:
            device_info = self.parse_device_info(device)
            device_infos.append(device_info)

        device_infos.sort(key=lambda it: (it["floor"], it["room"], it["type"], it["name"]))

        device_mp = self._convert_to_device_map_by_type(device_infos) if by_type \
            else self._convert_to_device_map_by_floor(device_infos)

        if verbose:
            print("主控信息：")
            print(master_device_info)

            print("\n\n设备列表信息：")
            self._print_device_info(device_mp, by_yaml=True)

        return master_device_info, device_infos, device_lst

    @staticmethod
    def process_integratedstove(device_info):
        """
        处理集成灶的设备信息，给出型号，分腔/一体机
        :param device_info: 所有的设备信息
        :return: device_info
        """
        device_type = device_info.get("deviceType")
        name = device_info.get("deviceName")
        if device_type == "IntegratedStove":
            device_code = device_info.get("deviceCode")
            if device_code.startswith("3F006"):
                name += " (蒸烤一体机)"
            elif device_code.startswith("3F007"):
                name += " (分腔蒸烤箱)"
            device_info["deviceName"] = name

        return device_info

    def parse_device_info(self, device_info):
        """
        解析设备信息，抽取简要的设备信息
        :param device_info:
        :return:
        """
        self.process_integratedstove(device_info)
        floor = device_info.get("floor", "")
        room = device_info.get("room", "")
        name = device_info.get("deviceName")
        device_type = device_info.get("deviceType")

        out_info = {
            "floor": floor,
            "room": room,
            "name": name,
            "type": device_type
        }

        return out_info

    def _get_master_device_info(self, master_device_id, device_lst):
        """
        获取主控设备信息
        :param master_device_id:
        :param device_lst:
        :return: master_device_info, str
        """
        for device in device_lst:
            device_id = device.get("deviceId")
            if master_device_id == device_id:
                master_device_info = self.parse_device_info(device)

                return master_device_info

        return None

    @staticmethod
    def _convert_to_device_map_by_floor(device_infos):
        """
        按楼层分类设备信息
        :param device_infos:
        :return: device_map
        """
        device_mp = {}
        for device_info in device_infos:
            floor = device_info.get("floor")
            room = device_info.get("room")
            _type = device_info.get("type")
            name = device_info.get("name")
            if floor not in device_mp:
                device_mp[floor] = {}
            if room not in device_mp[floor]:
                device_mp[floor][room] = {}
            if _type not in device_mp[floor][room]:
                device_mp[floor][room][_type] = []

            device_mp[floor][room][_type].append(name)

        for floor in device_mp:
            for room in device_mp[floor]:
                for _type in device_mp[floor][room]:
                    device_mp[floor][room][_type].sort()
                    device_mp[floor][room][_type] = ", ".join(device_mp[floor][room][_type])

        return device_mp

    @staticmethod
    def _convert_to_device_map_by_type(device_infos):
        """
        按类型分类设备信息
        :param device_infos:
        :return: device_map
        """
        device_mp = {}
        for device_info in device_infos:
            floor = device_info.get("floor")
            room = device_info.get("room")
            _type = device_info.get("type")
            name = device_info.get("name")
            if _type not in device_mp:
                device_mp[_type] = {}
            if floor not in device_mp[_type]:
                device_mp[_type][floor] = {}
            if room not in device_mp[_type][floor]:
                device_mp[_type][floor][room] = []

            device_mp[_type][floor][room].append(name)

        for _type in device_mp:
            for floor in device_mp[_type]:
                for room in device_mp[_type][floor]:
                    device_mp[_type][floor][room].sort()
                    device_mp[_type][floor][room] = ", ".join(device_mp[_type][floor][room])

        return device_mp

    @staticmethod
    def _print_device_info(device_mp, by_yaml=False):
        """
        打印设备信息
        :param device_mp:
        :param by_yaml: 是否按yaml格式，默认为False, 即json格式
        :return:
        """
        if by_yaml:
            s = json_to_yaml(device_mp)
            json_str = yaml.dump(s, indent=4, allow_unicode=True)
        else:
            json_str = json.dumps(device_mp, indent=4, ensure_ascii=False)

        print(json_str)

        return json_str

    @staticmethod
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

    @staticmethod
    def _get_sign(url, timestamp):
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

    def get_log_id(self, sn, is_last_req=True):
        """
        获取日志id信息
        :param sn: 请求的sn号
        :param is_last_req: 是否为半流式NLP的最终请求, default=True
        :return: dict()
        """
        env = self._env
        # date: 服务日志写入时间, 格式为"%Y%m%d",如"2023-03-08"
        date_start = 0
        while sn[date_start] != '2':
            date_start += 1
        date = f"{sn[date_start:date_start+4]}-{sn[date_start+4:date_start+6]}-{sn[date_start+6:date_start+8]}"

        url_base = {
            "test": "https://aitest.haiersmarthomes.com:11001/bomp-logdata-adapter/datalog/getlogList",
            "sim": "https://aisim.haiersmarthomes.com/bomp-logdata-adapter/datalog/getlogList",
            "service": "https://aiservice.haier.net/bomp-logdata-adapter/datalog/getlogList"
        }[env]

        url = url_base + f"?startDate={date}+00:00&accept={sn}&pageNum=1&pageSize=100"
        payload = {}
        timestamp = time.time_ns()//10**6
        sign = self._get_sign(url=url, timestamp=str(timestamp))
        headers = {
            "sign": sign,
            "timestamp": str(timestamp),
            "user-agent": USER_AGENT
        }

        for _ in range(3):
            try:
                response = requests.request("GET", url, headers=headers, data=payload)
                log_id_ret = json.loads(response.text)
                log_id_map = self._parse_log_id(log_id_ret)
                if log_id_map and is_last_req:
                    keys = log_id_map.keys()
                    for key in keys:
                        log_id_map[key] = (sn, log_id_map[key])
                    log_id = log_id_map.get("dialog-system:doNlpAnalysis", [self._sn, None])[1]
                    middle_sn = self.get_middle_sn(log_id=log_id)
                    if middle_sn:
                        print(f"middle sn: {middle_sn}")
                        mid_log_id_map = self.get_log_id(sn=middle_sn, is_last_req=False)
                        for key, val in mid_log_id_map.items():
                            log_id_map[key] = (middle_sn, val)
                        self._mid_sn = middle_sn
                return log_id_map
            except Exception as e:
                print(e)
                time.sleep(0.1)

        return {}

    def parse_nlu_receiver_info_from_log(self, resp_nlu_receiver):
        # multi_media_semantics = resp_nlu_receiver.get("multiMediaResult").get("semantics")[0]
        model_nlu_semantics = resp_nlu_receiver.get("modelNluResult").get("semantics")[0]
        # ccg_semantics = resp_nlu_receiver.get("ccgNluResult").get("semantics")[0]
        tpl_nlu_semantics = resp_nlu_receiver.get("templateNluResult").get("semantics")[0]
        nlu_receiver_info = {
            # "multi_media": [parse_nlu_info_from_log(it) for it in multi_media_semantics.get("childSemantics", [])],
            "model_nlu": [self.parse_nlu_info_from_log(it) for it in model_nlu_semantics.get("childSemantics", [])],
            # "ccg": [parse_nlu_info_from_log(it) for it in ccg_semantics.get("childSemantics", [])],
            "tpl_nlu": [self.parse_nlu_info_from_log(it) for it in tpl_nlu_semantics.get("childSemantics", [])],
        }

        return nlu_receiver_info

    @staticmethod
    def get_origin_query(param):
        for key in ["rawQuery", "rawInput", "originQuery"]:
            if key in param:
                return param[key]

        return None

    @staticmethod
    def get_rewrite_query(param):
        for key in ["query", "userInput"]:
            if key in param:
                return param[key]

        return None

    def _parse_service_info(self, service_info):
        if not service_info:
            return "服务出错，未抽取出query", {}
        data = service_info.get("data", {})
        req = json.loads(data["reqBody"]) if "reqBody" in data else {}
        param = req.get("args0", req)
        query = f'{self.get_origin_query(param)} -> {self.get_rewrite_query(param)}'
        # context = param.get("contextQuery")

        resp = json.loads(data["response"]) if "response" in data else None
        resp = resp.get("resp", resp)

        return query, resp

    def get_request_body(self):
        service_name = "dialog-system:doNlpAnalysis"
        resp_obj = self.get_service_info(service_name=service_name)
        req = resp_obj.get("data").get("reqBody")
        args = json.loads(req)

        post_json = args.get("args0", {})
        post_json.pop("sn", None)
        return post_json

    def get_query_by_sn(self, verbose=False):
        """
        获取dialog-system:doNlpAnalysis服务的结果
        :param verbose: 是否打印详细信息, 默认不打印
        """
        service_name = "dialog-system:doNlpAnalysis"
        if service_name not in self.get_log_id_map():
            return "ERROR doNlpAnalysis"
        service_info = self.get_service_info(service_name)
        query, _ = self._parse_service_info(service_info)
        if verbose:
            print_info = {
                "env": self._env,
                "sn": self._sn,
                "query": query
            }
            print_info = json.dumps(print_info, indent=4, ensure_ascii=False)
            print(print_info)

        return query

    def get_nlu_receiver_info_from_log(self, verbose=False, debug=True):
        """
            获取dialog-system:NluReceiver服务的结果
            :param verbose: 是否打印详细信息, 默认不打印
            :param debug: 是否打印调试信息, 默认打印
            """
        service_name = "dialog-system:NluReceiver"
        if service_name not in self.get_log_id_map():
            return "ERROR dialog-system:NluReceiver"
        service_info = self.get_service_info(service_name)
        query, resp = self._parse_service_info(service_info)
        if debug:
            print(format_string(f"nlu receiver info: env={self._env}, query={query}"))

        nlu_receiver_info = self.parse_nlu_receiver_info_from_log(resp_nlu_receiver=resp)

        # filter unimportant semantics
        for key in nlu_receiver_info:
            nlu_receiver_info[key] = self.rm_extract_domain(nlu_receiver_info[key])
            nlu_receiver_info[key] = self.rm_internal_command(nlu_receiver_info[key])
            nlu_receiver_info[key] = self.rm_block_semantics(nlu_receiver_info[key])

        if nlu_receiver_info:
            print_info = json.dumps(nlu_receiver_info, indent=4, ensure_ascii=False)

            if verbose:
                print(print_info)

        return nlu_receiver_info

    def get_service_info_by_log_id(self, log_id, sn=None):
        """
        根据日志id，获取具体服务的结果信息
        :param log_id: 服务对应的日志id
        :param sn: 服务对应的sn号, 默认为None, 即使用初始化的sn号
        """
        if not log_id:
            return None

        if not sn:
            sn = self._sn
        # date: 服务日志写入时间, 格式为"%Y%m%d",如"20230308"
        date_start = 0
        while sn[date_start] != '2':
            date_start += 1
        date = f"{sn[date_start:date_start + 8]}"

        url_base = {
            "test": "https://aitest.haiersmarthomes.com:11001/bomp-logdata-adapter/datalog/getHbaseChainLogDetail",
            "sim": "https://aisim.haiersmarthomes.com/bomp-logdata-adapter/datalog/getHbaseChainLogDetail",
            "service": "https://aiservice.haier.net/bomp-logdata-adapter/datalog/getHbaseChainLogDetail"
        }[self._env]

        url = url_base + f"?id={log_id}&date={date}&sn={sn}"
        payload = {}
        timestamp = time.time_ns() // 10 ** 6
        sign = self._get_sign(url=url, timestamp=str(timestamp))

        headers = {
            "sign": sign,
            "timestamp": str(timestamp),
            "user-agent": USER_AGENT
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        service_info = json.loads(response.text)
        if not service_info.get("data") or  not service_info["data"].get("reqBody"):
            return self.get_service_info_by_log_id(log_id=log_id, sn=self._mid_sn)
        else:
            return service_info

    def get_service_info(self, service_name):
        """
        获取具体服务的结果信息
        :param service_name: 服务名称，如"NluTemplate:nlu"
        """
        if not self._log_id_map:
            self._update_log_id_map()
        if service_name not in self._log_id_map:
            return None
        else:
            log_id = self._log_id_map.get(service_name)[1]
            return self.get_service_info_by_log_id(log_id)

    def get_middle_sn(self, log_id):
        service_info = self.get_service_info_by_log_id(log_id)
        if not service_info:
            return None
        resp = service_info.get("data").get("response")
        resp = json.loads(resp)
        middle_sn = resp.get("data").get("middleSn")
        return middle_sn

    @staticmethod
    def get_semantics(resp_obj,
                      remove_blocks=None,
                      remove_extract_domain=True,
                      remove_internal_command=False):
        """
        获取服务（如nlu, dm, template等）返回的结果中的semantics信息，并进行过滤
        :param remove_blocks: 额外需要过滤的Block*领域列表, 如["Music","Weather"]
        :param remove_extract_domain: 过滤不必要的Extract*, 默认为True
        :param remove_internal_command: 不能过滤InternalCommand, 可能跟温度/亮度专题相关
        :param resp_obj: 服务返回的json格式数据
        :return:
        """
        if remove_blocks is None:
            print(f"error: remove_blocks is None")
            return None
            # remove_blocks = ["BlockTemplate", "BlockNLU", "BlockCorpus", "BlockCCG", "BlockKg", "BlockIceNlu",
            #                  "BlockDp", "BlockGuoChuang"]
        if not resp_obj or "semantics" not in resp_obj or not resp_obj["semantics"]:
            return []

        semantics = []
        for item in resp_obj["semantics"]:
            if not item or "childSemantics" not in item or not item["childSemantics"]:
                continue

            child_semantics = item["childSemantics"]
            for block_domain in remove_blocks:
                child_semantics = LogParser.remove_blocks(block_domain, child_semantics)
            if remove_extract_domain:
                child_semantics = LogParser.rm_extract_domain(child_semantics)
            if remove_internal_command:
                child_semantics = LogParser.rm_internal_command(child_semantics)

            semantics.extend(child_semantics)

        return semantics

    @staticmethod
    def remove_blocks(block_domain, child_semantics):
        """
        生成过滤Block*领域的函数
        :param block_domain: 需要过滤的Block*领域
        :param child_semantics: 待过滤的语义信息
        :return:
        """
        if block_domain == "BlockTemplate":
            return LogParser.rm_block_template(child_semantics)
        else:
            return LogParser.rm_block_by_domain(semantics=child_semantics, block_domain=block_domain)



    @staticmethod
    def get_semantics_info(resp_obj, remove_blocks=None):
        """
        获取服务（如nlu, dm, template等）返回的结果中的semantics信息，并进行解析
        :param resp_obj: 服务返回的json格式数据
        :param remove_blocks: 额外需要过滤的Block*领域列表, 如["Music","Weather"]
        :return:
        """
        if remove_blocks is None:
            remove_blocks = [
                "BlockTemplate", "BlockNLU", "BlockCorpus", "BlockCCG", "BlockKg", "BlockIceNlu", "BlockDp",
                "BlockGuoChuang", "BlockCentralModel", "BlockChat"]
        semantics = LogParser.get_semantics(resp_obj, remove_blocks=remove_blocks)
        channel = resp_obj["retChannel"]
        if channel == "nluTemplate":
            semantics_info = [LogParser._parse_tpl_match_semantic(it) for it in semantics]
        else:
            semantics_info = [LogParser.parse_nlu_info_from_log(it) for it in semantics]

        return semantics_info

    @staticmethod
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

    @staticmethod
    def rm_block_semantics(semantics, remove_nlu=True):
        """
        过滤nlu_info中的Block类语义信息，如**BlockTemplate**
        :param semantics: 待过滤的语义信息
        :param remove_nlu: 是否去除BlockNLU语义, 默认去除BlockNLU
        :return:
        """
        if not semantics:
            return semantics
        filtered = []
        block_domain = set()
        for semantic in semantics:
            intent = semantic.get("intent", "")
            domain = semantic.get("domain", "")
            if intent.startswith("Block"):
                if not remove_nlu and domain.startswith("BlockNLU"):
                    pass
                else:
                    block_domain.add(intent[5:])

        for semantic in semantics:
            domain = semantic.get("domain", "")
            if "Block" not in domain and domain not in block_domain:
                filtered.append(semantic)

        return filtered

    @staticmethod
    def rm_block_template(semantics):
        """
        过滤nlu_info中的BlockTemplate类语义信息
        :param semantics: 待过滤的语义信息
        :return:
        """
        if not semantics:
            return semantics
        filtered = []
        block_domain = set()    # 模板禁掉的领域
        for semantic in semantics:
            intent = semantic.get("intent", "")
            domain = semantic.get("domain", "")
            if domain == "BlockTemplate":
                block_domain.add(intent[5:])

        for semantic in semantics:
            domain = semantic.get("domain", "")
            if domain != "BlockTemplate" and domain not in block_domain:
                filtered.append(semantic)

        return filtered

    @staticmethod
    def rm_block_by_domain(semantics, block_domain):
        """
        过滤nlu_info中的Block类语义信息
        :param semantics: 待过滤的语义信息
        :param block_domain: 待过滤的领域
        :return:
        """
        if not semantics:
            return semantics
        filtered = []

        for semantic in semantics:
            domain = semantic.get("domain", "")
            if domain != block_domain:
                filtered.append(semantic)

        return filtered

    @staticmethod
    def rm_internal_command(semantics):
        """
        过滤nlu_info中的InternalCommand类语义信息
        :param semantics: 待过滤的语义信息
        :return:
        """
        if not semantics:
            return semantics
        filtered = []
        for semantic in semantics:
            if "domain" in semantic and semantic["domain"] != "InternalCommand":
                filtered.append(semantic)

        return filtered

    @staticmethod
    def rm_extract_domain(nlu_info):
        """
        过滤nlu_info中的Extract类的领域信息，如"ExtractNer", "ExtractExecutorType"
        :param nlu_info: 待过滤的nlu信息
        :return:
        """
        if not nlu_info:
            return nlu_info
        filtered = []
        for it in nlu_info:
            if "domain" in it and it["domain"] and not it["domain"].startswith("Extract"):
                filtered.append(it)

        return filtered

    def get_tpl_match_info_from_log(self, verbose=False):
        """
        获取模板匹配NluTemplate:nlu结果
        :param verbose: 是否打印详细日志信息，默认为不打印
        """
        service_name = "NluTemplate:nlu"
        if service_name not in self.get_log_id_map():
            return "ERROR NluTemplate:nlu"
        service_info = self.get_service_info(service_name)
        query, resp = self._parse_service_info(service_info)

        print(format_string(f"template match result: env={self._env}, query={query}"))
        semantics = resp.get("semantics", [])
        simple_semantics = None
        if semantics:
            child_semantics = semantics[0]["childSemantics"]
            simple_semantics = [self._parse_tpl_match_semantic(it) for it in child_semantics]

        simple_semantics = self.rm_block_semantics(simple_semantics, remove_nlu=False)
        simple_semantics = self.rm_extract_domain(simple_semantics)
        simple_semantics = self.rm_internal_command(simple_semantics)
        if simple_semantics:
            print_info = json.dumps(simple_semantics, indent=4, ensure_ascii=False)
            if verbose:
                print(print_info)

        return simple_semantics

    @staticmethod
    def _block_check_by_domain(semantics, domain):
        """
        过滤nlu_info中的Block类语义信息，如**BlockTemplate**
        :param semantics: 待过滤的语义信息
        :param domain: 待检查的领域
        :return:
        """
        filtered = []
        for semantic in semantics:
            category = semantic.get("category", "")
            cur_domain = semantic.get("intent", "").lower()
            # 完全匹配检查
            if category == "BlockTemplate" and cur_domain == f"block{domain.lower()}":
                filtered.append(semantic)

        return filtered

    def block_check(self, domain_lst, verbose=False):
        """
        获取模板匹配NluTemplate:nlu结果
        :param domain_lst: 需要检查的领域
        :param verbose: 是否打印详细日志信息，默认为不打印
        """
        service_name = "NluTemplate:nlu"
        if service_name not in self.get_log_id_map():
            return "ERROR NluTemplate:nlu"
        service_info = self.get_service_info(service_name)
        query, resp = self._parse_service_info(service_info)

        print(format_string(f"block check: domains: {domain_lst}, env={self._env}, query={query}"))
        semantics = resp.get("semantics", [])
        simple_semantics = []
        if semantics:
            child_semantics = semantics[0]["childSemantics"]
            simple_semantics = [self._parse_tpl_match_semantic(it) for it in child_semantics]

        blocked_semantics = []
        for domain in domain_lst:
            blocked_semantics.extend(self._block_check_by_domain(simple_semantics, domain))
        if blocked_semantics:
            print_info = json.dumps(blocked_semantics, indent=4, ensure_ascii=False)
            if verbose:
                print(print_info)

        return blocked_semantics

    @staticmethod
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
            "channel":"nlu_model",
            "intent":"decreaseWarmGear"
        }
        """
        slots = child_semantics.get("slots", [])
        slots = {it.get("name", None): it.get("value", None) for it in slots}
        nlu_info = {
            "channel": child_semantics.get("channel", "nlu_model"),
            "domain": child_semantics.get("domain", None),
            "intent": child_semantics.get("intent", None),
            "slots": slots,
            "intent_score": child_semantics.get("intentScore", 0),
        }

        return nlu_info

    def get_log_trace_info_from_log(self, verbose=False):
        """
        获取dialog-system:LogTrace服务的结果
        :param verbose: 是否打印日志信息，默认为不打印
        """
        service_name = "dialog-system:LogTrace"
        if service_name not in self.get_log_id_map():
            return "ERROR LogTrace"
        service_info = self.get_service_info(service_name)
        query, resp = self._parse_service_info(service_info)
        print(format_string(f"log trace info: env={self._env}, query={query}"))

        log_trace_info = json.dumps(resp, ensure_ascii=False, indent=4)
        log_trace_info = log_trace_info.replace("\\r", "\r")
        log_trace_info = log_trace_info.replace("\\n", "\n")
        log_trace_info = log_trace_info.replace("\\t", "\t")
        if verbose:
            print(log_trace_info)

        return log_trace_info

    def get_device_exec_result(self, verbose=True):
        """
        获取DeviceExecServiceImpl:deviceExecProcess服务的结果
        :param verbose: 是否打印日志信息，默认为不打印
        """
        sn = self._sn
        service_name = "DeviceExecServiceImpl:deviceExecProcess"
        service_id = self.get_log_id_map().get(service_name)
        print(format_string(f"deviceExecProcess info: env={self._env}, sn={sn}"))

        date_str = sn[1:9] if sn[0] == "t" else sn[:8]
        base_url = "https://aitest.haiersmarthomes.com:11001/bomp-logdata-adapter/datalog/getHbaseChainLogDetail?"
        url = base_url + f"id={service_id}&date={date_str}&sn={sn}"
        timestamp = time.time_ns() // 10 ** 6
        sign = self._get_sign(url=url, timestamp=str(timestamp))
        headers = {
            "accept-language": "zh-CN,zh;q=0.9",
            "sign": sign,
            "timestamp": str(timestamp),
            "user-agent": USER_AGENT
        }
        method = "GET"
        payload = ""

        response = requests.request(method, url, headers=headers, data=payload)
        obj_resp = json.loads(response.text)

        data = obj_resp.get("data")
        req = json.loads(data.get("reqBody")).get("args0")
        device_exec_result = req.get("nlpResult").get("results")

        if verbose:
            print(json.dumps(device_exec_result, indent=4, ensure_ascii=False))

        return device_exec_result

    def get_do_nlu_info_from_log(self, verbose=False, debug=True):
        """
        获取dialog-system:doNlu服务的结果
        :param verbose: 是否打印日志信息，默认为不打印
        :param debug: 是否打印调试信息，默认为打印
        """
        service_name = "dialog-system:doNlu"
        if service_name not in self.get_log_id_map():
            return "ERROR doNlu"
        service_info = self.get_service_info(service_name)
        query, resp = self._parse_service_info(service_info)
        if debug:
            print(format_string(f"do_nlu info: env={self._env}, query={query}"))

        semantics = resp.get("semantics", [])
        nlu_info = None
        if semantics:
            child_semantics = []
            for it in semantics:
                child_semantics.extend(it["childSemantics"])
            nlu_info = [self.parse_nlu_info_from_log(it) for it in child_semantics]

        if nlu_info:
            # filter unimportant semantics
            nlu_info = self.rm_extract_domain(nlu_info)
            nlu_info = self.rm_internal_command(nlu_info)

            print_info = json.dumps(nlu_info, indent=4, ensure_ascii=False)
            if verbose:
                print(print_info)

        return nlu_info

    def get_do_nlp_analysis_info_from_log(self, verbose=False, debug=True):
        """
        获取dialog-system:doNlpAnalysis服务的结果
        :param verbose: 是否打印日志信息，默认为不打印
        :param debug: 是否打印调试信息，默认为打印
        """
        service_name = "dialog-system:doNlpAnalysis"
        if service_name not in self.get_log_id_map():
            return "ERROR doNlpAnalysis"
        service_info = self.get_service_info(service_name)
        request_json = service_info.get("data").get("reqBody")
        args = json.loads(request_json)
        request_data = args.get("args0", {})
        query, resp = self._parse_service_info(service_info)
        if debug:
            print(format_string(f"do_nlp_analysis info: env={self._env}, query={query}"))

        data = resp.get("data")
        if not data:
            return data
        nlp_analysis_info = {
            "category": data.get("category"),
            "nlpVersion": data.get("nlpVersion"),
            "masterDeviceId": request_data.get("masterDeviceId"),
            "entryDeviceType": data.get("entryDeviceType"),
            "isDialog": data.get("isDialog"),
            "middleSn": data.get("middleSn"),
            "nlp_response": data.get("response"),
            "centralControlInput": data.get("centralControlInput"),
            "centralControlOutput": data.get("centralControlOutput"),
            "results": data.get("results")
        }

        print_info = json.dumps(nlp_analysis_info, indent=4, ensure_ascii=False)
        if verbose:
            print(print_info)

        return nlp_analysis_info


def main():
    parser = LogParser(env="service")
    sn = "20241213173113652000743991"
    parser.update_config(sn=sn)

    domain_lst = ["Dev.oven", ""]

    parser.get_device_lst(by_type=True)

    parser.block_check(domain_lst, verbose=True)

    parser.get_nlu_receiver_info_from_log(verbose=True)

    parser.get_do_nlu_info_from_log(verbose=True)

    parser.get_tpl_match_info_from_log(verbose=True)

    parser.get_log_trace_info_from_log(verbose=True)
    return


if __name__ == "__main__":
    main()

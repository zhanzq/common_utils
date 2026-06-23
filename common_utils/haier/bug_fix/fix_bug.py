# encoding=utf-8
# created @2026/4/2
# created by zhanzq
#
import requests
import json
from common_utils.utils import get_version
from common_utils.const.web import USER_AGENT
import random
import time


class BugFix:
    def __init__(self, principle="zhanzhiqiang", token=None):
        self.principle = principle
        self.headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8"
        }
        if token:
            self.headers["x-auth-token"] = token
        self.bugs = []

    def set_cookie(self, cookie):
        """
        设置cookie，提取token并设置到headers中
        :param cookie: 从网页中复制的cookie字符串，包含token信息
        :return:
        """
        # 从cookie字符串中提取token并设置到headers中
        self.token = cookie.split("token=")[1].split("; ")[0]
        self.headers["x-auth-token"] = self.token

    def set_token(self, token):
        """
        直接设置token
        :param token: token字符串
        :return:
        """
        if token:
            self.headers["x-auth-token"] = token
        else:
            print(f"error: token不能为空")

    def add_comments_for_task(self, task_id, comments=None, verbose=True):
        """
        为任务添加备注
        :param task_id: 任务ID
        :param comments: 备注内容，可以是字符串或字符串列表，如果为None，则使用默认备注内容
        :param verbose:
        :return:
        """
        if not task_id:
            print(f"error: task_id为空，无法添加备注")
            return None
        if verbose:
            print("正在添加备注...")

        url = f"https://zone.haier.net:30931/zone/task-service/tasks/{task_id}/comments"
        if not comments:
            comments = [
                ["已修复并部署成功，可复测"],
                ["已修复"],
                ["修复好了，可以复测了"],
                ["已完成修复"],
                ["bug已经修复好了"]
            ]
            comments = random.choice(comments)

        content = ""
        if type(comments) is str:
            comments = [comments]

        for comment in comments:
            content += f"<p>{comment}</p>"
        payload = {
            "content": content
        }
        response = requests.request("POST", url, headers=self.headers, data=json.dumps(payload, ensure_ascii=False))
        obj_resp = json.loads(response.text)

        time.sleep(3)
        return obj_resp


    def get_bugs(self, verbose=True):
        """
        获取bug列表
        :param verbose:
        :return:
        """
        if verbose:
            print(f"正在获取bug列表...")

        url = "https://zone.haier.net:30931/zone/bff-service/workbench/user-bugs"
        payload = {
            "processedFlag": False,  # False: 未处理(打开/处理中)， True: 已处理(开发完成/已关闭)
            # "page": 1,
            # "pageSize": -1  # 默认为最大值
        }

        payload = json.dumps(payload)
        response = requests.post(url=url, headers=self.headers, data=payload)

        resp_json = json.loads(response.text)
        bugs = resp_json.get("data", {}).get("list", {})
        name_to_env = {
            "TEST": "test",  # 验收环境
            "PRE": "sim",  # 仿真环境
            "PRD": "service",  # 生产环境
        }
        for bug in bugs:
            env = name_to_env[bug.get("environment")]
            bug["env"] = env
        self.bugs = bugs
        time.sleep(3)
        return

    def get_filtered_bugs(self, **args):
        """
        根据传入的过滤条件对 bug 列表进行过滤
        :param args: 过滤条件，如 creatorId="xxx", projectName="yyy"
            所属迭代: projectName
            所属需求: demandName
            创建人: creatorId
            状态: status, [OPEN, PROCESSING, DEV_COMPLETED, CLOSED]
        :return: 过滤后的 bug 列表
        """
        filtered_bugs = []

        for bug in self.bugs:
            matched = True
            for key, value in args.items():
                # key 不存在 或 值不相等，直接不匹配
                if key not in bug or bug.get(key) is None or bug.get(key).strip() != value.strip():
                    matched = False
                    break

            if matched:
                filtered_bugs.append(bug.get("id"))

        return filtered_bugs


    def confirm_solution(self, bug_id, verbose=True):
        """
        确认解决方案
        :param bug_id: bug ID
        :param verbose:
        :return:
        """
        if verbose:
            print(f"正在确认解决方案...")

        url = f"https://zone.haier.net:30931/zone/quality-service/bugs/{bug_id}/cause-analysis"

        payload = {
            "solution": "NEED_REPAIR",  # ["NEED_REPAIR", "DELAY_REPAIR", "NOT_RESOLVED", "TRANSFORM_TO_REQUIREMENT"]
            # 需要解决，延期解决，不予解决，转需求
            "repairType": "OTHER",  # ["CODE", "SYSTEM_CONFIGURATE", "DATA_UPDATE", "SYMPATHETIC_PROBLEM", "OTHER"]
            # 编码，系统配置，数据更新，同因问题，其他
            "remark": "修复"  # comments
        }

        payload = json.dumps(payload, ensure_ascii=True)
        response = requests.request("POST", url, headers=self.headers, data=payload)
        obj_resp = json.loads(response.text)

        time.sleep(3)
        return obj_resp


    def get_bug_info(self, verbose=True):
        """
        只返回第一个处理中的bug
        """

        if verbose:
            print(f"正在获取bug信息...")

        url = "https://zone.haier.net:30931/zone/quality-service/bugs/page-by?page=1&pageSize=50&follow=false"

        payload = {
            "filterItems": [  # 处理中
                {
                    "logicType": "AND",
                    "operatorType": "=",
                    "fieldKey": "status",
                    "fieldValues": [
                        "PROCESSING"
                    ],
                    "type": "common",
                    "key": 1768358612206
                },
                {  # 负责人
                    "logicType": "AND",
                    "operatorType": "=",
                    "fieldKey": "principalId", # principal是指负责人，creator是指创建人
                    "fieldValues": [
                        self.principle
                    ],
                    "key": 1768358626576,
                    "type": "common",
                    "disabled": False
                }
            ],
            "isSave": False,
            "type": "BUG"
        }
        response = requests.post(url=url, headers=self.headers, data=json.dumps(payload))
        resp_json = json.loads(response.text)
        bug_info = resp_json.get("data", {}).get("list", [{}])

        if not bug_info:
            print(f"error: 未获得bug相关信息")
        else:
            bug_info = bug_info[0]
            print(f"bug key: {bug_info.get('key')}")

        time.sleep(3)
        return bug_info


    def start_task(self, task_id, verbose=True):
        if not task_id:
            print(f"error: task_id为空，无法启动任务")
            return None
        if verbose:
            print(f"启动任务...")

        url = f"https://zone.haier.net:30931/zone/bff-service/tasks/{task_id}/workflow?transaction=start"

        response = requests.request("POST", url, headers=self.headers, data="{}")
        obj_resp = json.loads(response.text)

        time.sleep(3)
        return obj_resp


    def stop_task(self, task_id, verbose=True):
        """
        完成任务
        """

        if verbose:
            print(f"停止任务...")

        url = f"https://zone.haier.net:30931/zone/bff-service/tasks/{task_id}/workflow?transaction=complete"
        response = requests.request("POST", url, headers=self.headers, data="{}")
        obj_resp = json.loads(response.text)

        time.sleep(3)
        return obj_resp


    def create_task_for_bug(self, bug_info, verbose=True):
        if verbose:
            print(f"正在创建bug解决任务...")

        url = "https://zone.haier.net:30931/zone/bff-service/tasks"
        if not bug_info.get("key"):
            print(f"error: 未找到bug相关信息")
            return None

        plan_date = get_version("%Y-%m-%d")  # 获取当天的日期
        payload = {
            "key": bug_info.get("key"),
            "bugId": bug_info.get("id"),
            "contextId": bug_info.get("id"),
            "contextType": "BUG",
            "description": "",
            "name": f"解决【{bug_info.get('key')} {bug_info.get('name')}】缺陷",
            "planEndDate": f"{plan_date} 23:59:59",
            "planStartDate": f"{plan_date} 00:00:00",
            "planWorkTime": "1",
            "principalId": bug_info.get("principalId"),
            "priority": "MEDIUM",
            "type": "OTHER",  # 默认为OTHER, 其他
        }
        response = requests.request("POST", url, headers=self.headers, data=json.dumps(payload, ensure_ascii=False))
        obj_resp = json.loads(response.text)
        task_id = obj_resp.get("data")

        time.sleep(3)
        return task_id


    def resolve_bug(self, bug_id, verbose=True):
        """
        解决bug
        """
        if verbose:
            print(f"开始解决bug: {bug_id} ...")
        if bug_id:
            # bug确认
            self.confirm_solution(bug_id, verbose=verbose)
        else:
            print(f"error: bug_id不能为空")
            return
        # 获取bug信息
        bug_info = self.get_bug_info(verbose=verbose)
        if not bug_info:
            return
        # 创建任务
        task_id = self.create_task_for_bug(bug_info, verbose=verbose)
        if not task_id:
            return
        # 启动任务
        self.start_task(task_id, verbose=verbose)
        # 添加备注
        self.add_comments_for_task(task_id, verbose=verbose)
        # 关闭任务
        self.stop_task(task_id)
        if verbose:
            print(f"bug: {bug_id} 已解决")
        return

def main():
    principle = "zhanzhiqiang"  # 负责人
    token = "fa044bee-064d-475b-af9f-22ddf5cd54aa"
    bug_fix = BugFix(principle=principle, token=token)
    bug_fix.get_bugs()
    filtered_bugs = bug_fix.get_filtered_bugs(
        demandName="【净饮机】温度推荐增加饮品种类需求",  # 所属需求
        # projectName="【净饮机】温度推荐增加饮品种类需求",   # 所属迭代
        # creatorId="wangshuangshuang",  # 创建人
        status="OPEN")

    print(filtered_bugs)

if __name__ == "__main__":
    main()

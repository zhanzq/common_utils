# encoding=utf-8
# created @2024/2/6
# created by zhanzq
#

import os
import time
import requests
from playsound import playsound
from common_utils.const.web import USER_AGENT


def youdao_english_tts(sentence, save_path=None):
    """
    使用youdao api将英文转为mp3音频数据
    :param sentence: 待转换的英文文本
    :param save_path: mp3音频数据保存的路径，默认为None, 即不保存，直接播放
    :return:
    """
    url = f"https://dict.youdao.com/dictvoice?audio={sentence}&le=eng&type=1"

    headers = {
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "audio",
        "User-Agent": USER_AGENT
    }
    method = "GET"
    payload = ""

    try:
        resp = requests.request(method, url, headers=headers, data=payload)
        if save_path is None:
            timestamp = time.time()
            save_path = f"./tmp_{timestamp}.mp3"
            save_mp3(content=resp.content, save_path=save_path)
            playsound(save_path)
            os.remove(save_path)
        else:
            save_mp3(content=resp.content, save_path=save_path)
            print(f"save to {save_path}")
    except Exception as e:
        print(e)

    return


def save_mp3(content, save_path):
    with open(save_path, "wb") as writer:
        writer.write(content)

    return


def main():
    sentence = "hello, world!"
    save_path = None
    youdao_english_tts(sentence=sentence, save_path=save_path)


if __name__ == "__main__":
    main()

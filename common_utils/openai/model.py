# !/usr/bin/env python
# encoding=utf-8
# author: zhanzq
# email : zhanzhiqiang09@126.com 
# date  : 2023/5/30
#


import os
import time
import json
import requests


def davinci(query, tries=0, max_tries=3):
    time.sleep(1)
    api_key = os.environ["OPENAI_API_KEY"]
    url = "https://api.openai.com/v1/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = json.dumps({
        "model": "text-davinci-003",
        "prompt": f"{query}\n",
        "max_tokens": 2048,
        "temperature": 0.9
    })
    proxies = {
        "https": "127.0.0.1:1087"
    }

    try:
        response = requests.request("POST", url=url, data=data, headers=headers, proxies=proxies)
        response = json.loads(response.text)
        return response["choices"][0]["text"].strip()
    except Exception as e:
        print(e)
        tries += 1
        if tries >= max_tries:
            print("davinci调用失败")
            # 相应失败就返回空
            return None
        else:
            return davinci(query, tries, max_tries)


def chatGPT(sentence, tries=0, max_tries=3):
    time.sleep(5)
    url = "https://api.openai.com/v1/chat/completions"

    api_key = os.environ["OPENAI_API_KEY"]
    payload = json.dumps({
      "model": "gpt-3.5-turbo",
      "messages": [
        {
          "role": "user",
          "content": f"{sentence}\n"
        }
      ]
    })
    headers = {
      'Content-Type': 'application/json',
      'Authorization': f'Bearer {api_key}'
    }

    proxies = {
        "https": "127.0.0.1:1087"
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload, proxies=proxies)
        result = json.loads(response.text)
        result = result['choices'][0]['message']["content"]
        return result
    except:
        tries += 1
        if tries >= max_tries:
            print("chatGPT调用失败")
            # 相应失败就返回空
            return None
        else:
            return chatGPT(sentence, tries, max_tries)


def main():
    query = "什么叫原子纠缠"
    resp_chatgpt = chatGPT(query)
    print(f"chatGPT: \n{resp_chatgpt}")

    resp_davinci = davinci(query)
    print(f"davinci: \n{resp_davinci}")

    return


if __name__ == "__main__":
    main()

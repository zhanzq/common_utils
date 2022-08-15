# !/usr/bin/env python
# encoding=utf-8
# author: zhanzq
# email : zhanzhiqiang09@126.com 
# date  : 2022/6/6
#


def lcs(s, t):
    """
    get all longest common substring between **s** and **t**
    :param s: type(s) is str or str list
    :param t: type(t) must be same with type(s)
    :return: list, contains all lcs, maybe with repetition
    """
    max_val = 0
    out_lst = set()
    sz1 = len(s) + 1
    sz2 = len(t) + 1
    dp = [[0 for _ in range(sz2)] for _ in range(sz1)]
    for i in range(1, sz1):
        for j in range(1, sz2):
            if s[i-1] == t[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
                if max_val < dp[i][j]:
                    max_val = dp[i][j]
                    out_lst = [s[i-dp[i][j]:i]]
                elif max_val == dp[i][j]:
                    out_lst.append(s[i-dp[i][j]:i])

    return out_lst


def test_lcs():
    pr_lst = [
        ("a bc d", "bc"),
        ("abc abc", "bc"),
        ("abc ab cd", "ab ab"),
        (["我", "喜欢", "你"], ["我", "也", "喜欢", "你"]),
    ]
    for s, t in pr_lst:
        print("s = {}, t = {}, LCS = {}".format(s, t, lcs(s, t)))

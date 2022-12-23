# !/usr/bin/env python
# encoding=utf-8
# author: zhanzq
# email : zhanzhiqiang09@126.com 
# date  : 2022/6/6
#


def get_edit_path(dp, pre_len=0, pst_len=0):
    """
    according to edit distance matrix, return the path,
    'i': insert a new element into second
    'd': delete an element from second
    'r': replace the element in first with the one in second
    's': keep the same
    :param dp: the input edit distance matrix
    :param pre_len: the prefix length, default 0
    :param pst_len: the postfix length, default 0
    :return:
    """
    i = len(dp) - 1
    j = len(dp[0]) - 1

    edit_path = ""
    while i > 0 or j > 0:
        if i == 0:
            edit_path += 'd'
            j -= 1
        elif j == 0:
            edit_path += 'i'
            i -= 1
        else:
            if dp[i][j] == dp[i - 1][j] + 1:
                edit_path += 'i'
                i -= 1
            elif dp[i][j] == dp[i][j - 1] + 2:
                edit_path += 'd'
                j -= 1
            else:
                if dp[i][j] == dp[i - 1][j - 1]:
                    edit_path += 's'
                else:
                    edit_path += 'r'
                i -= 1
                j -= 1

    edit_path = "s"*pre_len + edit_path[::-1] + "s"*pst_len

    return edit_path


def get_alignment_by_edit_path(source, target, edit_path):
    """
    get alignment between source and target with edit path
    :param source: with type **str** or **str list**
    :param target: with type **str** or **str list**
    :param edit_path: the edit path of converting target to source
    :return:
    """

    out1 = []
    out2 = []
    i, j = 0, 0
    for edit in edit_path:
        if edit == 'd':
            out1.append(' ' * len(target[j]))
            out2.append(target[j])
            j += 1
        elif edit == 'i':
            out2.append(' ' * len(source[i]))
            out1.append(source[i])
            i += 1
        elif edit == 's':
            out1.append(source[i])
            out2.append(target[j])
            i += 1
            j += 1
        else:
            out1.append(source[i])
            out1.append(' ' * len(target[j]))
            out2.append(' ' * len(source[i]))
            out2.append(target[j])
            i += 1
            j += 1

    if type(source) is str:
        out1 = "".join(out1)
        out2 = "".join(out2)

    return out1, out2


def get_edit_distance_matrix(source, target):
    """
    calculate edit distance matrix between source and target,
    :param source: with type **str** or **str list**
    :param target: with type **str** or **str list**
    :return:
    """

    sz1 = len(source)
    sz2 = len(target)

    dp = [[0 for _ in range(sz2 + 1)] for _ in range(sz1 + 1)]

    # initialize
    for i in range(sz1 + 1):
        dp[i][0] = i

    for j in range(sz2 + 1):
        dp[0][j] = j

    for i in range(sz1):
        for j in range(sz2):
            if source[i] == target[j]:
                dp[i + 1][j + 1] = dp[i][j]
            else:
                dp[i + 1][j + 1] = min(dp[i][j + 1] + 1, dp[i + 1][j] + 2, dp[i][j] + 4)

    return dp


def get_edit_distance_matrix_with_pre_pst(source, target):
    """
    calculate edit distance matrix between source and target,
    :param source: with type **str** or **str list**
    :param target: with type **str** or **str list**
    :return: edit distance matrix **dp**, prefix length **pre_len** and postfix length **pst_len**
    """
    pre_len, pst_len = 0, 0

    sz1 = len(source)
    sz2 = len(target)

    i = 0
    while i < sz1 and i < sz2:
        if source[i] == target[i]:
            pre_len += 1
            i += 1
        else:
            break
    j = 1
    while j <= sz1 and j <= sz2:
        if source[-j] == target[-j]:
            pst_len += 1
            j += 1
        else:
            break

    if pst_len == sz1 and sz1 == sz2:
        pst_len = 0
    if pst_len == 0:
        source1, target1 = source[pre_len:], target[pre_len:]
    else:
        source1, target1 = source[pre_len:-pst_len], target[pre_len:-pst_len]
    sz1, sz2 = len(source1), len(target1)

    dp = [[0 for _ in range(sz2 + 1)] for _ in range(sz1 + 1)]

    # initialize
    for i in range(sz1 + 1):
        dp[i][0] = i

    for j in range(sz2 + 1):
        dp[0][j] = j

    for i in range(sz1):
        for j in range(sz2):
            if source1[i] == target1[j]:
                dp[i + 1][j + 1] = dp[i][j]
            else:
                dp[i + 1][j + 1] = min(dp[i][j + 1] + 1, dp[i + 1][j] + 2, dp[i][j] + 4)

    return dp, pre_len, pst_len


def _print_edit_distance_matrix(dp):
    """
    print edit distance matrix
    :param dp: the input edit distance matrix
    :return:
    """
    m, n = len(dp), len(dp[0])
    for i in range(m):
        tpl = "{:2d}" * n
        print(tpl.format(*dp[i]))

    return

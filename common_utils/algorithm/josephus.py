# encoding=utf-8
# created @2024/2/6
# created by zhanzq
#


def josephus(m, k):
    """
        m个人，报数为k的约瑟夫问题，即m个人编号为0~m-1，站成一圈从编号为0的人开始从1数数，
    数到k的人淘汰，后面的人重新从1数数
    :param m: 总人数
    :param k: 最大的数字
    :return: 返回的结果为最后剩余人的编号（从0开始编号）
    推导公式f(m, k) = (f(m-1, k) + k)%m

    """
    res = 0
    for i in range(2, m + 1):
        # res即为上一轮的解
        res = (res + k) % i

    return res


def test_josephus():
    lst = list(range(10))
    lst = [f"报数{it + 1}" for it in lst]
    s = "\t".join(lst)
    print("\t", end="")
    print(s, end="\n")

    for m in range(1, 11):
        print(f"{m}人\t", end="")
        for k in range(1, 11):
            print(f"{josephus(m, k) + 1}\t", end="")
        print("")
    return

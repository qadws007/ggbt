import pandas as pd


def SUM(s, n):
    # 如果n等于0，则使用累进求和
    if n == 0:
        return s.cumsum()
    return s.rolling(n).sum()


def EVERY(s, n):
    R = SUM(s, n)
    return pd.Series(list(IF(r == n, True, False)[0]), index=s.index)


def LONGCROSS(a, b, n):
    '''
    两条线维持一定周期后交叉
    LONGCROSS（A,B,N）表示A在N周期内，都小于B，本周期时，大于B。
    :param a:
    :param b:
    :param n:
    :return:确定返回1，否则返回0
    '''
    if not isinstance(b, pd.Series):
        raise ValueError('b 必须是序列')
    return EVERY((REF(a, 1) < REF(B, 1)), n) & (a < b)

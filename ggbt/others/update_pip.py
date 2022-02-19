import pip
from subprocess import call
from pip._internal.utils.misc import get_installed_distributions

n = 1
s = len(get_installed_distributions())
for dist in get_installed_distributions():
    r = s - n
    call("pip install --upgrade " + dist.project_name, shell=True)
    print("共有{}个库，正在更新第{}个库，还剩{}库待更新，请耐心等待.......".format(s, n, r))
    n += 1

print("更新完毕！")
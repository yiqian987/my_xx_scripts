"""
cron: 50 59 * * * *
new Env('财富岛兑换红包');
"""
import os
import re
import time
import json
import datetime
import requests
from notify import send
from requests import RequestException
from ql_util import get_random_str
from ql_api import get_envs, disable_env, post_envs, put_envs


# 默认配置(看不懂代码也勿动)
cfd_start_time = -0.15
cfd_offset_time = 0.01

# 基础配置勿动
pattern_pin = re.compile(r'pt_pin=([\w\W]*?);')
pattern_data = re.compile(r'\(([\w\W]*?)\)')


# 获取下个整点和时间戳
def get_date() -> str and int:
    # 当前时间
    now_time = datetime.datetime.now()
    # 把根据当前时间计算下一个整点时间戳
    integer_time = (now_time + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:00:00")
    time_array = time.strptime(integer_time, "%Y-%m-%d %H:%M:%S")
    time_stamp = int(time.mktime(time_array))
    return integer_time, time_stamp


# 获取要执行兑换的cookie
def get_cookie():
    ck_list = []
    pin = "null"
    cookie = None
    cookies = get_envs("CFD_COOKIE")
    for ck in cookies:
        if ck.get('status') == 0:
            ck_list.append(ck)
    if len(ck_list) >= 1:
        cookie = ck_list[0]
        re_list = pattern_pin.search(cookie.get('value'))
        if re_list is not None:
            pin = re_list.group(1)
        print('共配置{}条CK,已载入用户[{}]'.format(len(ck_list), pin))
    else:
        print('共配置{}条CK,请添加环境变量,或查看环境变量状态'.format(len(ck_list)))
    return pin, cookie


# 获取配置参数
def get_config():
    start_dist = {}
    start_times = get_envs("CFD_START_TIME")
    if len(start_times) >= 1:
        start_dist = start_times[0]
        start_time = float(start_dist.get('value'))
        print('从环境变量中载入时间变量[{}]'.format(start_time))
    else:
        start_time = cfd_start_time
        u_data = post_envs('CFD_START_TIME', str(start_time), '财富岛兑换时间配置,自动生成,勿动')
        if len(u_data) == 1:
            start_dist = u_data[0]
        print('从默认配置中载入时间变量[{}]'.format(start_time))
    return start_time, start_dist


# 抢购红包请求函数
def cfd_qq(def_start_time):
    # 进行时间等待,然后发送请求
    end_time = time.time()
    while end_time < def_start_time:
        end_time = time.time()
    # 记录请求时间,发送请求
    t1 = time.time()
    d1 = datetime.datetime.now().strftime("%H:%M:%S.%f")
    res = requests.get(cfd_url, headers=headers)
    t2 = time.time()
    # 正则对结果进行提取
    re_list = pattern_data.search(res.text)
    # 进行json转换
    data = json.loads(re_list.group(1))
    msg = data['sErrMsg']
    # 根据返回值判断
    if data['iRet'] == 0:
        # 抢到了
        msg = "可能抢到了"
        put_envs(u_cookie.get('id'), u_cookie.get('name'), u_cookie.get('value'), msg)
        disable_env(u_cookie.get('id'))
        send("💖惊喜财富岛红包抢购提醒！", "💖可能抢到了100红包！速去！")
    elif data['iRet'] == 2016:
        # 需要减
        start_time = float(u_start_time) - float(cfd_offset_time)
        put_envs(u_start_dist.get('id'), u_start_dist.get('name'), str(start_time)[:8])
        # send("💖惊喜财富岛红包抢购提醒！", "❌来晚了，再接再厉")
    elif data['iRet'] == 2013:
        # 需要加
        start_time = float(u_start_time) + float(cfd_offset_time)
        put_envs(u_start_dist.get('id'), u_start_dist.get('name'), str(start_time)[:8])
        # send("💖惊喜财富岛红包抢购提醒！", "❌来早了，再接再厉")
    elif data['iRet'] == 1014:
        # URL过期
        send("💖惊喜财富岛红包抢购提醒！", "❌URL都过期了，去抓个新的吧！")
        pass
    elif data['iRet'] == 2007:
        # 财富值不够
        put_envs(u_cookie.get('id'), u_cookie.get('name'), u_cookie.get('value'), msg)
        disable_env(u_cookie.get('id'))
        send("💖惊喜财富岛红包抢购提醒！", "❌财富值都不够，慢慢攒着吧！")
    elif data['iRet'] == 9999:
        # 账号过期
        put_envs(u_cookie.get('id'), u_cookie.get('name'), u_cookie.get('value'), msg)
        disable_env(u_cookie.get('id'))
        send("💖惊喜财富岛红包抢购提醒！", "❌账号都过期了快去更新CK！")
    print("实际发送[{}]\n耗时[{:.3f}]\n用户[{}]\n结果[{}]".format(d1, (t2 - t1), u_pin, msg))


if __name__ == '__main__':
    print("- 程序初始化")
    print("脚本进入时间[{}]".format(datetime.datetime.now().strftime("%H:%M:%S.%f")))
    # 从环境变量获取url,不存在则从配置获取
    cfd_url = os.getenv("CFD_URL")
    # 获取cookie等参数
    u_pin, u_cookie = get_cookie()
    # 获取时间等参数
    u_start_time, u_start_dist = get_config()
    # 预计下个整点为
    u_integer_time, u_time_stamp = get_date()
    print("抢购整点[{}]".format(u_integer_time))
    print("- 初始化结束\n")

    print("- 主逻辑程序进入")
    UA = "jdpingou;iPhone;5.11.0;15.1.1;{};network/wifi;model/iPhone13,2;appBuild/100755;ADID/;supportApplePay/1;hasUPPay/0;pushNoticeIsOpen/1;hasOCPay/0;supportBestPay/0;session/22;pap/JA2019_3111789;brand/apple;supportJDSHWK/1;Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148".format(
        get_random_str(45, True))
    if u_cookie is None:
        print("未读取到CFD_COOKIE,程序结束")
    else:
        headers = {
            "Host": "m.jingxi.com",
            "Accept": "*/*",
            "Connection": "keep-alive",
            'Cookie': u_cookie['value'],
            "User-Agent": UA,
            "Accept-Language": "zh-CN,zh-Hans;q=0.9",
            "Referer": "https://st.jingxi.com/",
            "Accept-Encoding": "gzip, deflate, br"
        }
        u_start_sleep = float(u_time_stamp) + float(u_start_time)
        print("预计发送时间为[{}]".format(datetime.datetime.fromtimestamp(u_start_sleep).strftime("%H:%M:%S.%f")))
        if u_start_sleep - time.time() > 300:
            print("离整点时间大于5分钟,强制立即执行")
            cfd_qq(0)
        else:
            cfd_qq(u_start_sleep)
    print("- 主逻辑程序结束")

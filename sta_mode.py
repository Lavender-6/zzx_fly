#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E400-T 无人机：一键切换到【客机 / STA / 连接路由器模式】

用法（在树莓派 Thonny 或终端里）：
    python3 ~/Desktop/sta_mode.py

作用：关掉热点，让树莓派连上指定的 WiFi 路由器。
      连上之后树莓派和你的电脑在同一个局域网，都能上网。

为什么要等：从热点(AP)切回客机(STA)时，无线网卡要停掉 AP、
      把工作模式从 ap 切回 managed，这中间有几秒钟是不能用的。
      旧版本脚本断开就立刻连，所以会"秒弹连接失败"。
      现在会先等网卡就绪、等目标 WiFi 出现在扫描列表里，再连。
"""

import os
import sys
import time
import subprocess

# ==================== ↓↓↓ 参数区，按需修改 ↓↓↓ ====================

WIFI_DEVICE = "wlan0"        # 无线网卡名，一般不用改
WIFI_SSID = "kskblzdjd"      # 要连接的 WiFi 名称
WIFI_PASSWORD = "123456789"  # WiFi 密码

# 是否顺便固定 IP：True = 固定，False = 保持自动获取（DHCP）
# 现在的静态 IP 已经配好在连接里了，一般不用开
USE_STATIC_IP = False
STATIC_IP = "192.168.0.200/24"      # 想要的固定地址（换成没人用的）
GATEWAY = "192.168.0.1"             # 路由器网关地址
DNS = "223.5.5.5 114.114.114.114"   # DNS，用阿里的，解析快

# 等待时间（秒），信号差的环境可以调大
WAIT_READY = 25      # 等网卡从 AP 模式切回 managed
WAIT_SSID = 30       # 等目标 WiFi 出现在扫描列表
RETRY = 3            # 连接失败后的重试次数

# ==================== ↑↑↑ 参数区结束，下面不用改 ↑↑↑ ====================

LOG_FILE = "/tmp/wifi_switch.log"


def run(args, capture=False):
    """执行一条命令，打印命令本身和输出"""
    print("\n$ " + " ".join(args))
    sys.stdout.flush()
    if capture:
        p = subprocess.run(args, capture_output=True, text=True)
        if p.stdout.strip():
            print(p.stdout.strip())
        if p.stderr.strip():
            print("[stderr] " + p.stderr.strip())
        return p.returncode, p.stdout + p.stderr
    rc = subprocess.call(args)
    return rc, ""


def device_state(dev):
    p = subprocess.run(["nmcli", "-t", "-f", "DEVICE,STATE", "dev", "status"],
                       capture_output=True, text=True)
    for line in p.stdout.splitlines():
        parts = line.split(":")
        if len(parts) >= 2 and parts[0] == dev:
            return parts[1]
    return "unknown"


def wifi_visible(ssid):
    """目标 WiFi 是否已经在扫描列表里"""
    p = subprocess.run(["nmcli", "-t", "-f", "SSID", "dev", "wifi", "list"],
                       capture_output=True, text=True)
    return ssid in [s.strip() for s in p.stdout.splitlines() if s.strip()]


def wait_for(cond, timeout, tip):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(1)
    print("[超时] %s" % tip)
    return False


def do_connect():
    """连一次，返回是否成功"""
    cmd = ["nmcli", "dev", "wifi", "connect", WIFI_SSID,
           "password", WIFI_PASSWORD, "ifname", WIFI_DEVICE]
    rc, out = run(cmd, capture=True)
    return rc == 0


def main():
    print("=" * 54)
    print("  切换到客机（STA / 连接路由器）模式")
    print("  目标 WiFi：%s" % WIFI_SSID)
    print("  固定 IP  ：%s" % (STATIC_IP if USE_STATIC_IP else "否（自动获取）"))
    print("=" * 54)

    # 1. 断开 wlan0 上当前的连接（正在发热点的话也会被停掉）
    run(["nmcli", "dev", "disconnect", WIFI_DEVICE])

    # 2. 等网卡从 AP 模式切回 managed（这一步是"秒弹失败"的关键）
    print("\n[1/4] 等无线网卡回到 managed 模式 ...")
    wait_for(lambda: device_state(WIFI_DEVICE) == "disconnected",
             WAIT_READY, "网卡一直没回到可用状态，但还是继续试试")
    time.sleep(2)

    # 3. 扫描，等目标 WiFi 出现
    print("\n[2/4] 扫描并等待 %s 出现 ..." % WIFI_SSID)
    for i in range(WAIT_SSID // 3 + 1):
        run(["nmcli", "dev", "wifi", "rescan"], capture=True)
        time.sleep(1)
        if wifi_visible(WIFI_SSID):
            print("      已找到 %s" % WIFI_SSID)
            break
        print("      还没找到，继续等 ... (%d)" % (i + 1))
        time.sleep(2)
    else:
        print("      [警告] 一直没扫到 %s，可能是信号太弱或名字写错" % WIFI_SSID)

    # 4. 连接，失败就重试
    print("\n[3/4] 连接 %s ..." % WIFI_SSID)
    ok = False
    for i in range(RETRY):
        if do_connect():
            ok = True
            break
        print("      第 %d 次失败，等 5 秒重试 ..." % (i + 1))
        time.sleep(5)

    # 5. 兜底：用系统里已经保存过的同名连接再试一次
    if not ok:
        print("\n      常规连接都失败了，改用已保存的连接配置试一次 ...")
        rc, out = run(["nmcli", "connection", "up", WIFI_SSID], capture=True)
        ok = (rc == 0)

    # 6. 需要的话设置固定 IP
    if ok and USE_STATIC_IP:
        run(["nmcli", "connection", "modify", WIFI_SSID,
             "ipv4.addresses", STATIC_IP,
             "ipv4.gateway", GATEWAY,
             "ipv4.dns", DNS,
             "ipv4.method", "manual"])
        run(["nmcli", "connection", "up", WIFI_SSID])

    # 7. 报告结果
    print("\n[4/4] 结果")
    print("=" * 54)
    if device_state(WIFI_DEVICE) == "connected":
        p = subprocess.run(["ip", "-4", "addr", "show", WIFI_DEVICE],
                           capture_output=True, text=True)
        print("  已切换到客机模式，树莓派新地址：")
        for line in p.stdout.splitlines():
            if "inet" in line:
                print("  " + line.strip())
        print("  用这个地址 SSH：ssh ubuntu@<上面的地址>")
    else:
        print("  [失败] 没连上 %s，当前 wlan0 = %s" % (WIFI_SSID, device_state(WIFI_DEVICE)))
        print("  请检查：")
        print("    1. WiFi 名称有没有写错（区分大小写）")
        print("    2. 密码对不对")
        print("    3. 树莓派离路由器是不是太远")
        print("  应急办法：Ubuntu 右上角开一次飞行模式再关，它会自动连回来")
    print("=" * 54)


if __name__ == "__main__":
    # 没有管理员权限就自动用 sudo 重新执行自己
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        flag = ["FROM_SSH=1"] if (os.environ.get("SSH_CONNECTION")
                                  or os.environ.get("SSH_TTY")) else ["FROM_SSH=0"]
        print("需要管理员权限，正在请求 sudo ...")
        os.execvp("sudo", ["sudo", "env"] + flag + [sys.executable, os.path.abspath(__file__)])

    # 远程执行时要先躲到后台，否则断网瞬间脚本自己会被杀
    if os.environ.get("FROM_SSH") == "1" or (
            os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_TTY")):
        print("[提示] 检测到远程连接，脚本转入后台，结果看 %s" % LOG_FILE)
        sys.stdout.flush()
        if os.fork() > 0:
            os._exit(0)
        os.setsid()
        f = open(LOG_FILE, "w", buffering=1)
        os.dup2(f.fileno(), sys.stdout.fileno())
        os.dup2(f.fileno(), sys.stderr.fileno())

    main()

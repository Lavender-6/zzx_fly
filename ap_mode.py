#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E400-T 无人机：一键切换到【热点 / AP / 主机模式】

用法（在树莓派 Thonny 或终端里）：
    python3 ~/Desktop/ap_mode.py

作用：让树莓派自己发射 WiFi 热点，手机或电脑连上来之后
      ssh ubuntu@10.42.0.1 就能访问飞机。

关于密码（重要）：
    - 留空 ""           -> 真正的开放热点，不用密码
    - 8 位及以上        -> WPA2 加密，用你填的密码
    - 1~7 位（不合法）  -> 自动降级为开放热点
    注意：不能简单地"不给 nmcli 传密码"，那样 NetworkManager 会
    自己生成一个随机密码。本脚本用 connection add 手动建连接，
    完全可控。
"""

import os
import sys
import time
import subprocess

# ==================== ↓↓↓ 参数区，按需修改 ↓↓↓ ====================

WIFI_DEVICE = "wlan0"            # 无线网卡名，一般不用改
HOTSPOT_SSID = "E400-T"          # 热点名称
HOTSPOT_PASSWORD = "12345678"    # 热点密码
                                 #   留空 ""     -> 开放热点，不用密码
                                 #   8 位及以上  -> WPA2 加密
                                 #   1~7 位     -> 不合法，自动改成开放热点
HOTSPOT_CONN_NAME = "E400-T-AP"  # 系统内部保存的连接名，随意起

# ==================== ↑↑↑ 参数区结束，下面不用改 ↑↑↑ ====================

LOG_FILE = "/tmp/wifi_switch.log"


def run(args, capture=False):
    """执行一条命令，打印命令本身和结果"""
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


def wait_for(cond, timeout, tip):
    """轮询等待条件成立，返回是否等到"""
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(1)
    print("[超时] %s" % tip)
    return False


def device_state(dev):
    p = subprocess.run(["nmcli", "-t", "-f", "DEVICE,STATE", "dev", "status"],
                       capture_output=True, text=True)
    for line in p.stdout.splitlines():
        parts = line.split(":")
        if len(parts) >= 2 and parts[0] == dev:
            return parts[1]
    return "unknown"


def main():
    print("=" * 54)
    print("  切换到热点（AP / 主机）模式")
    print("  热点名称：%s" % HOTSPOT_SSID)

    pwd = HOTSPOT_PASSWORD.strip()
    if pwd == "":
        use_pwd = False
        print("  热点密码：无（开放热点）")
    elif len(pwd) < 8:
        use_pwd = False
        print("  热点密码：你填的 '%s' 只有 %d 位，WPA2 要求至少 8 位"
              % (pwd, len(pwd)))
        print("            -> 已自动改为【开放热点（无密码）】")
        print("            想加密的话把密码改成 8 位以上，比如 12345678")
    else:
        use_pwd = True
        print("  热点密码：%s（WPA2）" % pwd)
    print("=" * 54)

    # 1. 断掉 wlan0 上现有的一切（正在连的 WiFi 或正在发的热点）
    run(["nmcli", "dev", "disconnect", WIFI_DEVICE])
    time.sleep(2)

    # 2. 删掉上一次留下的同名连接，避免旧配置（尤其是旧密码）残留
    run(["nmcli", "connection", "delete", HOTSPOT_CONN_NAME])

    # 3. 手动建一条 AP 连接：不给 wifi-sec 参数 = 真正的开放热点
    cmd = ["nmcli", "connection", "add",
           "type", "wifi",
           "ifname", WIFI_DEVICE,
           "con-name", HOTSPOT_CONN_NAME,
           "autoconnect", "no",
           "ssid", HOTSPOT_SSID,
           "mode", "ap",
           "802-11-wireless.band", "bg",
           "ipv4.method", "shared"]
    if use_pwd:
        cmd += ["wifi-sec.key-mgmt", "wpa-psk", "wifi-sec.psk", pwd]

    rc, out = run(cmd, capture=True)
    if rc != 0:
        print("\n[失败] 热点连接创建失败，请把上面的报错拍给我")
        sys.exit(1)

    # 4. 启动它
    rc, out = run(["nmcli", "connection", "up", HOTSPOT_CONN_NAME], capture=True)
    if rc != 0:
        print("\n[失败] 热点启动失败，请把上面的报错拍给我")
        sys.exit(1)

    # 5. 等它真正跑起来
    ok = wait_for(lambda: device_state(WIFI_DEVICE) == "connected", 25,
                  "热点在 25 秒内没进入 connected 状态")

    print("\n" + "=" * 54)
    if ok:
        p = subprocess.run(["ip", "-4", "addr", "show", WIFI_DEVICE],
                           capture_output=True, text=True)
        print("  热点已启动")
        print("  现在用电脑 / 手机搜索 WiFi：%s" % HOTSPOT_SSID)
        if use_pwd:
            print("  密码：%s" % pwd)
        else:
            print("  密码：无，直接连")
        for line in p.stdout.splitlines():
            if "inet" in line:
                print("  树莓派自身地址：" + line.strip())
        print("  用这个地址 SSH：ssh ubuntu@10.42.0.1")
    else:
        print("  状态异常，当前 wlan0 = %s" % device_state(WIFI_DEVICE))
        print("  跑一下 nmcli dev status 看看，或者把输出拍给我")
    print("  想切回客机模式：python3 ~/Desktop/sta_mode.py")
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

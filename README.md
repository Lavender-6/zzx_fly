# zzx_fly

中科浩电 E400-T 无人机（树莓派 + 飞控）的配套工具脚本。

## 内容

| 文件 | 作用 |
| --- | --- |
| `ap_mode.py` | 一键切换到**热点 / AP / 主机模式**，让树莓派自己发射 WiFi `E400-T` |
| `sta_mode.py` | 一键切换到**客机 / STA 模式**，让树莓派连上指定路由器 |

两个脚本都支持在文件顶部「参数区」自行填写 WiFi 名称、密码、固定 IP，会自动 sudo 提权，
并且能识别 SSH 远程执行场景（切网络会断线，脚本会转入后台跑完，结果写 `/tmp/wifi_switch.log`）。

## 用法

在树莓派上（Thonny 或终端）：

```bash
python3 ~/Desktop/ap_mode.py      # 开热点
python3 ~/Desktop/sta_mode.py     # 连路由器
```

## 环境

- 硬件：中科浩电 E400-T，树莓派（Ubuntu 20.04 + ROS Noetic）
- 无线网卡：`wlan0`
- 客机模式下树莓派固定 IP：`192.168.0.200`，SSH：`ssh ubuntu@192.168.0.200`
- 热点模式下树莓派自身地址：`10.42.0.1`

## 两个已知的坑

1. `nmcli dev wifi hotspot` 不传 `password` 参数时，NetworkManager **不会**创建开放热点，
   而是随机生成一个 WPA 密码。要真正的开放热点，得用 `nmcli connection add` 且不带 `wifi-sec.*` 参数。
2. 从 AP 模式切回 STA 时，网卡要花几秒把工作模式从 `ap` 切回 `managed`，
   断开后立刻连接必定失败，必须先等待再连。

## 安全提示

脚本参数区里有明文的 WiFi 密码和热点密码。如果要把本仓库设为公开，
请先把这些值替换成占位符（如 `YOUR_WIFI_PASSWORD`）。

# zsl — 上一个操作者的遗留文件归档

> 整理日期：2026-09-28
> 来源：树莓派 `~/Desktop/` 和 `~/` 家目录散落的各处
> 说明：本文件夹只做**归档**，里面的脚本大多已被新方案取代，日常飞行不要再依赖它们。

## 文件清单

| 文件 | 原位置 | 年代 | 是什么 | 现在还要用吗 |
| --- | --- | --- | --- | --- |
| `launch_file.sh` | `~/Desktop/` | 2022-12 | ROS 一键启动脚本，内容只有一行 `gnome-terminal -- bash -c "roslaunch vision_to_mavros t265_all_nodes_with_E400.launch"` | ❌ **已失效**。两个原因：①开机时没有图形桌面，`gnome-terminal` 起不来，所以开机自启从来没成功过；②它启动的 `t265_all_nodes_with_E400.launch` 里 mavros 的 `tgt_system` 默认 1，而飞控 `SYSID_THISMAV=2`，连不上飞控。已被 `E400_fly.launch` 取代 |
| `zsl_4g_stream.sh` | `~/zsl`（原文件名就叫 zsl） | 2023-06 | **最有价值的一个**：4G 拨号 + MediaMTX + ffmpeg 一键推流脚本，走 Tailscale 把摄像头画面推成 RTSP | ⏸ **暂不用，野外飞行时启用**。它依赖 `~/mediamtx`（未移动）和 `ppp0`（4G 模块）。实验室阶段 4G 会抢默认路由，先别跑 |
| `startup.sh` | `~/` | 2022-12 | 同上，另一个版本的 ROS 启动脚本，也是 `gnome-terminal` 写法 | ❌ 同样失效 |
| `camera_test.py` | `~/` | 2023-05 | OpenCV 摄像头测试，试的是 `/dev/video11` | 📌 有参考价值：记录了摄像头设备号摸索过程 |
| `test.py` | `~/` | 2023-05 | OpenCV 摄像头测试，最终确认是 `/dev/video0` | 📌 **结论：图传摄像头是 `/dev/video0`** |
| `test.jpg` | `~/` | 2023-05 | 上面那个测试抓的帧 | 📌 留证 |
| `create_ap/` | `~/Desktop/` | 2023-01 | 厂商自带的 create_ap 热点工具源码（含 systemd service） | ❌ 已废弃。相关的 `hostapd` / `hotspot-ip.service` / `nat.service` / `dnsmasq` 全部已禁用，改用 `nmcli` 发热点（见 `ap_mode.py`） |
| `.launch_file.sh.swp` | `~/Desktop/` | 2023-11 | vim 编辑留下的交换文件，垃圾 | 🗑 可删 |
| `sss/` `stream/` | `~/` | 2022-12 / 2023-05 | 两个空目录 | 🗑 可删 |
| `_cmd_notes/` | `~/` | 2023-05 | 6 个被误存成**文件**的命令——当时想敲命令却存成了文件，文件名就是命令本身（如 `udo ifconfig wlan0 10.42.0.1 netmask 255.255.255.0 up`，注意 `udo` 是 `sudo` 打漏了 s）。文件内容是那条命令的输出 | 📌 有史料价值：能看出前人调网络时的挣扎过程 |

## 注意事项

1. **`/etc/rc.local` 已同步更新**：原来写的是 `sh /home/ubuntu/Desktop/launch_file.sh &`，整理后改为 `sh /home/ubuntu/Desktop/zsl/launch_file.sh &`。
   （这个自启本来就是坏的，建议后面直接改成跑 `E400_fly.launch` 的无终端版本。）
2. **`zsl_4g_stream.sh` 里硬编码了 `cd /home/ubuntu/mediamtx`**，所以 `~/mediamtx` 目录没有被移动，别去动它。
3. 下面这些是**系统/编译产物，不属于归档范围，原位未动**：
   `vision_to_mavros/`、`catkin_ws/`、`t265_ws/`、`librealsense/`、`mediamtx/`、`reqw.sh`（mavros 官方的 GeographicLib 数据集安装脚本）、两个 `.deb` 安装包。

## 有价值的结论（从这些文件里提炼出来的）

- 图传摄像头设备号 = **`/dev/video0`**
- 飞控串口 = **`/dev/ttyACM0`**，ArduPilot mini-pix，`SYSID_THISMAV = 2`
- T265 走 USB3（Bus02 5000M），必须先跑一次 ROS 让固件加载完成
- 4G 模块拨号后会出现 `ppp0`，会抢默认路由，实验室阶段要避免

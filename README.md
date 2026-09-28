# zzx_fly

中科浩电 E400-T 无人机（树莓派 + 飞控）的配套工具脚本。

## 内容

| 文件 | 作用 |
| --- | --- |
| `ap_mode.py` | 一键切换到**热点 / AP / 主机模式**，让树莓派自己发射 WiFi `E400-T` |
| `sta_mode.py` | 一键切换到**客机 / STA 模式**，让树莓派连上指定路由器 |
| `E400_fly.launch` | ROS 起飞 launch：T265 定位 + MAVROS 飞控 + 位姿桥接（**修好了连不上飞控的问题**） |

两个切换脚本都支持在文件顶部「参数区」自行填写 WiFi 名称、密码、固定 IP，会自动 sudo 提权，
并且能识别 SSH 远程执行场景（切网络会断线，脚本会转入后台跑完，结果写 `/tmp/wifi_switch.log`）。

## 起飞

```bash
roslaunch vision_to_mavros E400_fly.launch
```

把这个 launch 放到 `~/vision_to_mavros/src/vision_to_mavros/launch/` 下
（桌面 `zzx_fly` 文件夹里也留了一份副本）。
**不要再用原来的 `t265_all_nodes_with_E400.launch`**，它连不上飞控，原因见下面的坑 3。

验证：

```bash
rostopic echo /mavros/state      # connected 应为 True
rostopic hz /camera/odom/sample  # T265 起成功后应有 200Hz 左右
rostopic hz /mavros/vision_pose/pose   # 位姿桥接应为 30Hz
```

如果 `/camera/odom/sample` 存在但**没有消息**，直接重启一次 ROS 即可（见坑 5）。

## 用法

在树莓派上（Thonny 或终端）：

```bash
python3 ~/Desktop/ap_mode.py      # 开热点
python3 ~/Desktop/sta_mode.py     # 连路由器
```

## 环境

- 硬件：中科浩电 E400-T，树莓派（Ubuntu 20.04 + ROS Noetic）
- 主板：**Raspberry Pi 4 Model B Rev 1.5**（2 个蓝色 USB3 口 + 2 个黑色 USB2 口）
- 无线网卡：`wlan0`
- 客机模式下树莓派固定 IP：`192.168.0.200`，SSH：`ssh ubuntu@192.168.0.200`
- 热点模式下树莓派自身地址：`10.42.0.1`
- 飞控：ArduPilot **mini-pix**（`1209:5741`），串口 `/dev/ttyACM0`，USB CDC（波特率不生效）
- 视觉：RealSense T265。上电是 `03e7:2150`（bootloader），固件加载后重枚举为
  `8087:0b37`（正式模式，此时才跑在 USB3 5000M 上）。详见坑 4

## 踩过的坑

1. `nmcli dev wifi hotspot` 不传 `password` 参数时，NetworkManager **不会**创建开放热点，
   而是随机生成一个 WPA 密码。要真正的开放热点，得用 `nmcli connection add` 且不带 `wifi-sec.*` 参数。
2. 从 AP 模式切回 STA 时，网卡要花几秒把工作模式从 `ap` 切回 `managed`，
   断开后立刻连接必定失败，必须先等待再连。
3. **mavros 连不上飞控**：这台飞控 `SYSID_THISMAV = 2`，而 mavros 的 `apm.launch`
   里 `tgt_system` 默认写死 1。sysid 不匹配时 mavros 会丢弃所有消息，
   症状很迷惑 —— `/mavlink/from` 有数据，但 `/mavros/*` 全空、`/mavros/state` 永远
   `connected: False`。注意参数名是 **`tgt_system`**，不是 `target_system_id`。
4. **T265 的速率不能在上电瞬间判断。** 它是两阶段枚举：

   ```
   上电    → 03e7:2150 Movidius MA2X5X (bootloader)   此时 speed 恒为 480，挂在 Bus01
      ↓ 只有在跑了 ROS/驱动、固件被上传之后
   重枚举  → 8087:0b37 Intel RealSense T265            SuperSpeed，挂到 Bus02 5000M
   ```

   所以**没跑 ROS 时用 `lsusb -t` 或 `cat /sys/.../speed` 查，永远是 480M，那是假象**，
   据此判断"插错口了"会白白折腾（我们为此连换了三次口）。
   真正的判据要看驱动加载之后：出现 `Bus 002 ... 8087:0b37` 才是真的在 USB3 上。

5. **ROS 启动时序坑。** `wait_for_device_timeout = -1.0`（无限等待）。
   若 ROS 启动时 T265 还停在 bootloader，realsense2_camera 节点抓不到设备就一直空转 ——
   表现为话题列表里 `/camera/odom/sample` 存在，但**没有任何消息**，
   而且设备后来重枚举成功了也不会自动恢复。
   **解法：再重启一次 ROS**（设备只要不掉电就保持在 8087 状态，节点启动时能直接抓到）。

## 当前进度（2026-09-28）

已跑通：

| 指标 | 实测 |
| --- | --- |
| `/camera/odom/sample` 位姿 | 199 Hz |
| `/camera/gyro/sample` 陀螺仪 | 200 Hz |
| `/mavros/vision_pose/pose` | 30 Hz（T265 位姿已喂进飞控） |
| `/mavros/state` | connected True · STABILIZE · 未解锁 |

下一关：飞控 EKF 还没把外部视觉当位置源，`/mavros/local_position/pose` 为空，
自检报 `EKF2 IMU0 has stopped aiding` / `PreArm: EKF2 still initialising`（目前解锁不了）。
待配参数：`EK3_ENABLE=1`、`EK3_SRC1_POSXY/VELXY/POSZ/YAW=6`（ExternalNav）、`VISO_TYPE=1`。

## 安全提示

脚本参数区里有明文的 WiFi 密码和热点密码。如果要把本仓库设为公开，
请先把这些值替换成占位符（如 `YOUR_WIFI_PASSWORD`）。

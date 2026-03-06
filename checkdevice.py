import os
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import subprocess

# ================= 配置区 =================
# 1. 导师手机的 MAC 地址
TARGET_MAC = "BE:23:A8:3F:AA:B3" 

# 2. 邮件发送配置
SMTP_SERVER = "smtp.qq.com"     # 例如: smtp.qq.com, smtp.163.com
SMTP_PORT = 465                 # SSL端口通常是465
SENDER_EMAIL = "****@qq.com"       # 发件人邮箱
SENDER_PASSWORD = "##############"       # 邮箱授权码（非登录密码）
RECEIVER_EMAIL = "****@foxmail.com" # 收件人邮箱

# 3. 检查频率（秒），建议 30-60 秒
CHECK_INTERVAL = 1

# 4. 离线判定缓冲（分钟）。防止导师手机休眠导致误报“走了又来”
OFFLINE_BUFFER_MINS = 0.25
# =========================================

is_mentor_present = False
last_seen_time = 0

def send_warning(msg):
    """发送邮件通知"""
    message = MIMEText(msg, 'plain', 'utf-8')
    message['From'] = formataddr(["导师预警系统", SENDER_EMAIL])
    message['To'] = Header("Alert", 'utf-8')
    message['Subject'] = Header('【导师动态更新】', 'utf-8')

    try:
        # 使用SMTP_SSL连接
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], message.as_string())
        server.quit()
        print(f"邮件发送成功: {msg}")
    except Exception as e:
        print(f"邮件发送失败: {e}")

    
def check_mac_in_arp():
    # 使用 nmap 扫描整个网段（假设网段是 192.168.1.0/24）
    # -sn 代表只探测存活，不扫描端口，速度极快
    cmd = "nmap -sn 192.168.31.0/24"
    subprocess.run("arp -d *", shell=True, capture_output=True)
    subprocess.run(cmd, shell=True, capture_output=True)
    
    # 扫描完后，ARP 表一定会更新，此时再读
    with os.popen("arp -a") as f:
        arp_output = f.read().lower()
        print("======== 当前 ARP 表 ========")
        print(arp_output)
        print("=============================")
        target_mac_lower = TARGET_MAC.lower()
        # Windows 通常用连字符 (-)，Linux/Unix 通常用冒号 (:)
        # 这里同时检查两种格式，确保兼容性
        return (target_mac_lower in arp_output) or \
               (target_mac_lower.replace(":", "-") in arp_output)

print("监控中... 祝大家好运。")

while True:
    found = check_mac_in_arp()
    current_time = time.time()

    if found:
        if not is_mentor_present:
            send_warning("📢 导师已进入 WiFi 范围！")
            is_mentor_present = True
        last_seen_time = current_time # 刷新最后看见的时间
    else:
        # 如果超过缓冲时间没看见，认为导师走了
        if is_mentor_present and (current_time - last_seen_time) > (OFFLINE_BUFFER_MINS * 60):
            send_warning("✅ 导师信号已消失超过15分钟，警报解除。")
            is_mentor_present = False

    time.sleep(CHECK_INTERVAL)
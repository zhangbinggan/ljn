import time
import hmac
import hashlib
import base64
import requests
import json
import os
import logging


def feishu(title: str, content: str) -> dict:
    """
    发送飞书机器人消息

    Args:
        feishu_webhook: 飞书机器人的webhook地址
        feishu_secret: 安全设置中的签名校验密钥
        title: 消息标题
        content: 消息内容

    Returns:
        dict: 接口返回结果
    """
    # 环境变量
    FEISHU_BOT_URL = os.environ.get("FEISHU_BOT_URL")
    FEISHU_BOT_SECRET = os.environ.get("FEISHU_BOT_SECRET")

    feishu_webhook = FEISHU_BOT_URL
    feishu_secret = FEISHU_BOT_SECRET

    # 添加配置检查日志（脱敏处理）
    if feishu_webhook:
        # 脱敏处理webhook URL
        if len(feishu_webhook) > 50:
            safe_webhook = feishu_webhook[:30] + "***" + feishu_webhook[-10:]
        else:
            safe_webhook = (
                feishu_webhook[:10] + "***" + feishu_webhook[-6:]
                if len(feishu_webhook) > 16
                else "***"
            )
        logging.info(f"飞书Webhook URL(脱敏): {safe_webhook}")
    else:
        logging.info("飞书Webhook URL: 未配置")

    if feishu_secret:
        safe_secret = (
            feishu_secret[:6] + "***" + feishu_secret[-4:]
            if len(feishu_secret) > 10
            else "***"
        )
        logging.info(f"飞书Secret(脱敏): {safe_secret}")
    else:
        logging.info("飞书Secret: 未配置")

    timestamp = str(int(time.time()))

    # 计算签名
    string_to_sign = f"{timestamp}\n{feishu_secret}"
    hmac_code = hmac.new(
        string_to_sign.encode("utf-8"), digestmod=hashlib.sha256
    ).digest()
    sign = base64.b64encode(hmac_code).decode("utf-8")

    # 添加签名日志（脱敏处理）
    logging.info(f"飞书时间戳: {timestamp}")
    if feishu_secret:
        safe_secret_for_sign = (
            feishu_secret[:6] + "***" + feishu_secret[-4:]
            if len(feishu_secret) > 10
            else "***"
        )
        logging.info(f"飞书签名字符串(脱敏): {timestamp}\n{safe_secret_for_sign}")
    else:
        logging.info(f"飞书签名字符串: {timestamp}\n未配置密钥")

    safe_sign = sign[:10] + "***" + sign[-6:] if len(sign) > 16 else "***"
    logging.info(f"飞书签名(脱敏): {safe_sign}")

    # 构建请求头
    headers = {"Content-Type": "application/json"}

    # 构建消息内容
    msg = {
        "timestamp": timestamp,
        "sign": sign,
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": title,
                    "content": [[{"tag": "text", "text": content}]],
                }
            }
        },
    }

    # 脱敏处理消息载荷中的签名
    safe_msg = msg.copy()
    safe_msg["sign"] = safe_sign

    logging.info(f"飞书请求头: {headers}")
    logging.info(
        f"飞书请求载荷(脱敏): {json.dumps(safe_msg, ensure_ascii=False, indent=2)}"
    )

    # 发送请求
    try:
        if not isinstance(feishu_webhook, str):
            logging.error(f"飞书webhook未配置")
            return {"error": "飞书webhook未配置"}

        response = requests.post(feishu_webhook, headers=headers, data=json.dumps(msg))

        # 改进返回值打印
        logging.info(f"飞书响应状态码: {response.status_code}")
        logging.info(f"飞书响应头: {dict(response.headers)}")

        response_data = response.json()
        logging.info(
            f"飞书响应数据: {json.dumps(response_data, ensure_ascii=False, indent=2)}"
        )

        if response.status_code == 200 and response_data.get("code") == 0:
            logging.info(f"飞书发送通知消息成功🎉")
        else:
            logging.error(
                f"飞书发送通知消息失败😞\n错误码: {response_data.get('code')}\n错误信息: {response_data.get('msg')}"
            )

        return response_data
    except Exception as e:
        logging.error(f"飞书发送通知消息失败😞\n异常: {e}")
        logging.error(
            f"飞书响应原始内容: {response.text if 'response' in locals() else '无响应'}"
        )
        return {"error": str(e)}

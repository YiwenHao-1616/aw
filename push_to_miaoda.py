#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, datetime, requests

if len(sys.argv) &lt; 5:
    print("用法: python3 push_to_miaoda.py &lt;txt文件&gt; &lt;source&gt; &lt;edge_url&gt; &lt;sync_key&gt;")
    sys.exit(1)

txt_file, source, edge_url, sync_key = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

if source not in ("huisi", "jiahui"):
    print(f"错误: source 必须是 huisi 或 jiahui，当前: {source}"); sys.exit(1)

with open(txt_file, "r", encoding="utf-8") as f:
    text = f.read().strip()

if len(text) &lt; 20:
    print(f"错误: txt 内容过短（{len(text)} 字符）"); sys.exit(1)

payload = {"source": source, "date": datetime.date.today().isoformat(), "text": text}
print(f"[{source}] 文本 {len(text)} 字符，正在推送到秒哒 AI 识别+增删...")

try:
    resp = requests.post(edge_url, json=payload,
        headers={"x-sync-key": sync_key, "Content-Type": "application/json"}, timeout=300)
    print(f"[{source}] HTTP {resp.status_code}: {resp.text}")
    resp.raise_for_status()
except requests.exceptions.Timeout:
    print(f"[{source}] 错误: 超时（300秒），订单量过大"); sys.exit(2)
except Exception as e:
    print(f"[{source}] 错误: {e}"); sys.exit(3)

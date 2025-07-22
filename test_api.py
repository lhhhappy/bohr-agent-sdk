#!/usr/bin/env python3
import requests
import json

# 测试文件树 API
try:
    response = requests.get('http://localhost:50002/api/files/tree')
    print("Status Code:", response.status_code)
    print("Response:")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(response.text)
except Exception as e:
    print("Error:", e)

# 测试配置 API
print("\n" + "="*50 + "\n")
try:
    response = requests.get('http://localhost:50002/api/config')
    print("Config API Status Code:", response.status_code)
    if response.status_code == 200:
        data = response.json()
        print("Files config:", json.dumps(data.get('files', {}), indent=2, ensure_ascii=False))
except Exception as e:
    print("Config API Error:", e)
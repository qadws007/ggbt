#量化平台端代码（把信息传递出去）

import requests
import json

if __name__ == '__main__':
    url = 'http://127.0.0.1:500'
    data = {"imageId": "那你好", "base64Data": "您好啊", "format": "jpg", "url": "欢迎"}
    data = json.dumps(data)
    r = requests.post(url, data=data)
    print(r.text)
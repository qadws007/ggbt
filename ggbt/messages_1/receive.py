#本地端代码（接受量化平台传出来的信息）

from flask import Flask,request
import json
app = Flask(__name__)

@app.route("/", methods=["GET","POST"])
def view_func_2():

    data = request.get_json()
    if data:
        pass
    else:
        data = request.get_data()
        data = json.loads(data)

    imageId = data["imageId"]
    base64Data = data["base64Data"]
    format = data["format"]
    url = data["url"]
    print(imageId,base64Data,format,url)
    return data

if __name__ == '__main__':
    app.run(host="127.0.0.1",port=500)
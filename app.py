import json
import os
from flask import Flask, jsonify, render_template, request, send_from_directory
import requests

app = Flask(__name__)
DATA_DIR = "/app/data"
DATA_FILE = os.path.join(DATA_DIR, "links.json")
AVATAR_FILE = os.path.join(DATA_DIR, "avatar.png")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "7777777")


def load_data():
  if not os.path.exists(DATA_FILE):
    os.makedirs(DATA_DIR, exist_ok=True)
    initial_data = {
        "监控": [{
            "name": "Grafana",
            "url": "http://grafana.internal",
            "desc": "指标监控",
        }],
        "CI/CD": [{
            "name": "GitLab",
            "url": "http://gitlab.internal",
            "desc": "代码与流水线",
        }],
        "运维工具": [{
            "name": "JumpServer",
            "url": "http://bastion.internal",
            "desc": "堡垒机",
        }],
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
      json.dump(initial_data, f, ensure_ascii=False, indent=4)

  with open(DATA_FILE, "r", encoding="utf-8") as f:
    return json.load(f)


def save_data(data):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


@app.route("/")
def index():
  return render_template("index.html")


@app.route("/api/links", methods=["GET"])
def get_links():
  return jsonify(load_data())


# 添加链接
@app.route("/api/links", methods=["POST"])
def add_link():
  req_data = request.json
  category = req_data.get("category")
  name = req_data.get("name")
  url = req_data.get("url")
  desc = req_data.get("desc", "")

  if not category or not name or not url:
    return jsonify({"success": False, "message": "缺少必要参数"}), 400

  data = load_data()
  if category not in data:
    data[category] = []

  data[category].append({"name": name, "url": url, "desc": desc})
  save_data(data)
  return jsonify({"success": True, "message": "添加成功"})


# 删除网页（密码校验）
@app.route("/api/links", methods=["DELETE"])
def delete_link():
  req_data = request.json
  category = req_data.get("category")
  index = req_data.get("index")
  password = req_data.get("password")

  if password != ADMIN_PASSWORD:
    return jsonify({"success": False, "message": "密码错误，拒绝删除"}), 403

  data = load_data()
  if category in data and 0 <= index < len(data[category]):
    data[category].pop(index)
    save_data(data)
    return jsonify({"success": True, "message": "网址删除成功"})

  return jsonify({"success": False, "message": "目标不存在"}), 404


# 新增分类
@app.route("/api/category", methods=["POST"])
def add_category():
  req_data = request.json
  category = req_data.get("category")

  if not category:
    return jsonify({"success": False, "message": "分类名称不能为空"}), 400

  data = load_data()
  if category in data:
    return jsonify({"success": False, "message": "分类已存在"}), 400

  data[category] = []
  save_data(data)
  return jsonify({"success": True, "message": "分类创建成功"})


# 删除分类（密码校验）
@app.route("/api/category", methods=["DELETE"])
def delete_category():
  req_data = request.json
  category = req_data.get("category")
  password = req_data.get("password")

  if password != ADMIN_PASSWORD:
    return jsonify({"success": False, "message": "密码错误，拒绝删除"}), 403

  data = load_data()
  if category in data:
    del data[category]
    save_data(data)
    return jsonify({"success": True, "message": "分类删除成功"})

  return jsonify({"success": False, "message": "分类不存在"}), 404


# 网页连通性测试代理接口
@app.route("/api/check-status", methods=["POST"])
def check_status():
  req_data = request.json
  target_url = req_data.get("url")
  if not target_url:
    return jsonify({"status": False})
  try:
    # 尝试发起请求，设置较短超时避免阻塞
    response = requests.get(
        target_url, timeout=3, verify=False, allow_redirects=True
    )
    # 只要能正常响应（状态码小于500，或粗略判定连通）即认为绿灯
    if response.status_code < 500:
      return jsonify({"status": True})
    else:
      return jsonify({"status": False})
  except Exception:
    return jsonify({"status": False})


# 头像上传接口
@app.route("/api/avatar", methods=["POST"])
def upload_avatar():
  if "avatar" not in request.files:
    return jsonify({"success": False, "message": "未找到上传文件"}), 400
  file = request.files["avatar"]
  if file.filename == "":
    return jsonify({"success": False, "message": "文件名为空"}), 400

  os.makedirs(DATA_DIR, exist_ok=True)
  file.save(AVATAR_FILE)
  return jsonify({"success": True, "message": "头像更新成功"})


# 获取头像接口
@app.route("/api/avatar", methods=["GET"])
def get_avatar():
  if os.path.exists(AVATAR_FILE):
    return send_from_directory(DATA_DIR, "avatar.png")
  return "", 404


if __name__ == "__main__":
  load_data()
  app.run(host="0.0.0.0", port=8000)

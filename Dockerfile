FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/python:3.11-alpine3.19

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码与模板
COPY app.py .
COPY templates/ templates/

# 创建数据存储目录
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["python", "app.py"]

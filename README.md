# elyw-algo 项目文档

## 项目简介

elyw-algo是一个基于FastAPI和Vue的算法管理系统，提供算法任务调度、文件存储和容器管理等功能。

## 后端

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境
# 在.env.dev文件中配置以下关键参数：
# DB_HOST=localhost
# DB_PORT=5432
# DB_USER=postgres
# DB_PASSWORD=your_password
# DB_NAME=elyw-algo
# REDIS_HOST=localhost
# REDIS_PORT=6379

# 运行sql文件

# 1. 创建数据库
createdb -U postgres elyw-algo

# 2. 导入SQL文件
psql -U postgres -d elyw-algo -f sql/init.sql


# 运行后端
python app.py --env=dev
```

- 或者使用docker启动

```bash
docker build -t elyw-algo .

docker save elyw-algo -o elyw-algo.tar

docker load -i elyw-algo.tar

docker run -p 9099:9099 -v $(pwd)/backend:/app elyw-algo
```

## 前端

```bash
# 进入前端目录
cd frontend

# 安装依赖
yarn install

# 配置环境
# frontend\vite.config.js

# 运行前端
yarn dev

# 打包前端
yarn build:stage
yarn build:prod
```

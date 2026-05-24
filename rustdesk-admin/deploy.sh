#!/bin/bash

set -e

cd "$(dirname "$0")"

echo "=== 小翔DS 管理后台部署脚本 ==="

echo "[1/4] 检查依赖..."
if ! command -v python3 &> /dev/null; then
    echo "安装 Python3..."
    sudo apt update && sudo apt install -y python3 python3-pip python3-venv
fi

if ! command -v node &> /dev/null; then
    echo "安装 Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
fi

echo "[2/4] 安装 API 依赖..."
cd api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

echo "[3/4] 构建 Web 前端..."
cd web
npm install
npm run build
cd ..

echo "[4/4] 创建数据目录..."
mkdir -p data

echo ""
echo "=== 部署完成 ==="
echo ""
echo "启动方式："
echo "  开发模式: ./start-dev.sh"
echo "  生产模式: docker-compose up -d"
echo ""
echo "默认管理员账号: admin / admin"
echo "管理后台地址: http://localhost"
echo "API 地址: http://localhost:21114"

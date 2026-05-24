#!/bin/bash

cd "$(dirname "$0")"

echo "启动 API 服务器..."
cd api
source venv/bin/activate
python main.py &
API_PID=$!
deactivate
cd ..

echo "启动 Web 开发服务器..."
cd web
npm run dev &
WEB_PID=$!
cd ..

echo ""
echo "服务已启动:"
echo "  API: http://localhost:21114"
echo "  Web: http://localhost:3000"
echo ""
echo "按 Ctrl+C 停止"

trap "kill $API_PID $WEB_PID 2>/dev/null" EXIT
wait

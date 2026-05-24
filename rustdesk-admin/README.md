# 小翔DS 管理后台

RustDesk 远程桌面管理系统，包含 API 服务器和 Web 管理后台。

## 功能特性

- ✅ 用户管理（增删改查、权限控制）
- ✅ 设备管理（查看、分组、状态监控）
- ✅ 地址簿管理（用户独立地址簿）
- ✅ 审计日志（操作记录追踪）
- ✅ 策略管理（安全策略配置）
- ✅ 与 hbbs/hbbr 真实数据集成

## 快速开始

### 方式一：开发模式

```bash
# 1. 部署依赖
chmod +x deploy.sh
./deploy.sh

# 2. 启动服务
chmod +x start-dev.sh
./start-dev.sh
```

### 方式二：Docker 部署

```bash
# 1. 构建前端
cd web && npm install && npm run build && cd ..

# 2. 启动所有服务
docker-compose up -d
```

## 访问地址

| 服务 | 地址 |
|------|------|
| Web 管理后台 | http://localhost |
| API 服务 | http://localhost:21114 |
| hbbs 信令服务 | localhost:21116 |
| hbbr 中继服务 | localhost:21117 |

## 默认账号

- 用户名: `admin`
- 密码: `admin`

**⚠️ 生产环境请立即修改默认密码！**

## 项目结构

```
rustdesk-admin/
├── api/                    # FastAPI 后端
│   ├── main.py            # 主程序入口
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库模型
│   ├── auth.py            # 认证模块
│   └── routers/           # API 路由
│       ├── auth.py        # 用户认证
│       ├── devices.py     # 设备管理
│       ├── addressbook.py # 地址簿
│       └── audit.py       # 审计日志
├── web/                    # Vue.js 前端
│   ├── src/
│   │   ├── views/         # 页面组件
│   │   ├── api.js         # API 请求
│   │   └── router.js      # 路由配置
│   └── package.json
├── docker-compose.yml      # Docker 编排
└── deploy.sh              # 部署脚本
```

## API 文档

启动后访问 http://localhost:21114/docs 查看 Swagger API 文档。

### 主要接口

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/login | POST | 用户登录 |
| /api/users | GET/POST | 用户列表/创建 |
| /api/devices | GET | 设备列表 |
| /api/ab/get | GET | 获取地址簿 |
| /api/audit/logs | GET | 审计日志 |

## 配置说明

环境变量配置：

```bash
# API 服务端口
API_PORT=21114

# JWT 密钥（生产环境必须修改）
JWT_SECRET=your-secret-key

# hbbs 数据库路径
HBBS_DB_PATH=/path/to/hbbs/db_v2.sqlite3

# hbbs 主机地址
HBBS_HOST=your-server.com
```

## 与 RustDesk 客户端集成

1. 客户端设置服务器地址：
   - ID/中继服务器: `your-server.com:21116`
   - API 服务器: `http://your-server.com:21114`

2. 获取服务器公钥：
   ```bash
   cat data/hbbs/id_ed25519.pub
   ```

3. 客户端登录后即可使用地址簿等功能

## 技术栈

- 后端: Python FastAPI + SQLAlchemy
- 前端: Vue 3 + Element Plus
- 数据库: SQLite
- 服务器: RustDesk hbbs/hbbr

## License

MIT

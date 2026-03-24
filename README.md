# EnvTools Web - 开发环境管理器

基于 Python (Flask) + Vue 3 (Element Plus) 的开发环境管理工具。

## 快速开始

### 首次使用（需要 Node.js 构建前端）

```bash
# 1. 安装前端依赖并构建
cd frontend
npm install
npm run build
cd ..

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 启动
python app.py
```

浏览器访问 http://localhost:18090

### 部署到其他机器（只需 Python）

将整个 `ideweb` 文件夹复制到目标机器，然后：

```bash
pip install -r requirements.txt
python app.py
```

> 前提：`frontend/dist/` 目录已包含构建好的前端文件。

### 开发模式

同时启动前端开发服务器和后端：

```bash
# 终端1：启动 Python 后端
python app.py

# 终端2：启动 Vue 开发服务器（支持热更新）
cd frontend
npm run dev
```

开发时访问 http://localhost:5173（Vite 会自动代理 `/api` 到 Flask 后端）。

## 功能

- **仪表盘** - 系统信息总览，已安装环境统计
- **环境管理** - 自动扫描已安装的开发环境，支持手动添加；服务启停、状态/端口检测
- **安装中心** - 从注册表浏览和安装开发工具（支持镜像源加速）
- **环境变量** - 管理用户/系统 PATH 和环境变量，支持 `%VAR%` 引用，自动识别 bin 子目录
- **配置文件** - 自动发现并编辑各环境的配置文件（nginx.conf、my.ini 等）
- **设置** - 主题、语言、镜像源配置

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | Python 3.10+ / Flask / SQLite |
| 前端 | Vue 3 / Element Plus / Pinia / Vue Router |
| 构建 | Vite |
| 数据 | SQLite（~/.envtools/envtools.db） |

## 项目结构

```
ideweb/
├── app.py                      # Flask 主入口（注册蓝图、SPA 路由）
├── requirements.txt            # Python 依赖
├── backend/
│   ├── __init__.py             # 路径常量
│   ├── core/                   # 基础设施层
│   │   ├── database.py         # SQLite 连接、建表、迁移
│   │   └── config.py           # 应用配置 CRUD
│   ├── services/               # 业务逻辑层
│   │   ├── scanner.py          # 自动扫描已安装环境
│   │   ├── env_vars.py         # 环境变量 & PATH 管理
│   │   ├── manual_env.py       # 手动环境管理
│   │   ├── config_files.py     # 配置文件发现与编辑
│   │   ├── service_cmd.py      # 服务命令执行（启动/停止等）
│   │   ├── status_check.py     # 运行状态 & 端口检测
│   │   ├── installer.py        # 包安装/卸载
│   │   └── mirror.py           # 镜像源管理
│   ├── api/                    # Flask Blueprint 路由层
│   │   ├── config.py           # /api/config, /api/mirrors
│   │   ├── env_vars.py         # /api/env-vars, /api/path
│   │   ├── environments.py     # /api/scan, /api/manual-envs, /api/env-status
│   │   ├── packages.py         # /api/packages, /api/install
│   │   └── files.py            # /api/config-files
│   └── data/
│       └── env_defs.json       # 环境定义种子数据
├── registry/                   # 软件包注册表 (TOML 清单)
└── frontend/                   # Vue 前端
    ├── src/
    │   ├── views/              # 页面组件
    │   ├── stores/             # Pinia 状态管理
    │   ├── api/                # Axios API 调用
    │   ├── i18n/               # 国际化（中文/英文）
    │   └── components/         # 布局 & UI 组件
    └── dist/                   # 构建产物（生产用）
```

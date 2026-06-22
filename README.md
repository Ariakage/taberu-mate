<h1 align="center">TaberuMate<br/><a href="LICENSE">
    <img src="https://img.shields.io/badge/license-AGPL--3.0--only-blue.svg?style=flat-square" alt="License: AGPL-3.0-only" />
  </a><a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/python-3.13%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.13+" />
  </a><a href="https://nodejs.org/">
    <img src="https://img.shields.io/badge/node.js-24%2B-339933?style=flat-square&logo=node.js&logoColor=white" alt="Node.js 24+" />
  </a><a href="https://vuejs.org/">
    <img src="https://img.shields.io/badge/vue-3-42b883?style=flat-square&logo=vuedotjs&logoColor=white" alt="Vue 3" />
  </a><a href="https://docs.astral.sh/uv/">
    <img src="https://img.shields.io/badge/package%20manager-uv-261230?style=flat-square" alt="uv" />
  </a></h1>

<p align="center">
  简体中文 | <a href="docs/README.en.md">English</a> | <a href="docs/README.ja.md">日本語</a>
</p>

<p align="center">
  <a href="https://github.com/ariakage/taberu-mate">
    <img src="docs/assets/header.png" alt="TaberuMate Logo" />
  </a>
  <br />
  <strong>食べ友——不惧陌生，陪你旅行吃上美味喵～</strong>
</p>

## ✨ 特性

- **📷 一键拍照识别菜单**

  拿起手机拍下餐厅菜单，AI 自动识别并生成可交互的数字菜单，无需手动输入

- **🍽️ 仿扫码点餐 / 外卖的点餐体验**

  像国内扫码点餐一样，轻松浏览菜品、查看图片、价格和描述，支持多语言切换

- **🌍 智能翻译成当地语言**

  使用智能体一键将菜单翻译成你的母语（或旅行目的地语言输入输出），支持 100+ 种语言，翻译准确自然

- **🌟 智能筛选与忌口备注**

  按口味、价格、是否辣、素食等条件筛选；并类似备注一样填写忌口

- **🔏 隐私安全**

  可快速使用项目复刻属于自己的快捷平台

## 🚀 快速开始
### Step1 克隆仓库
`git clone https://github.com/Ariakage/taberu-mate.git`
### Step2-1 部署Python环境
```bash
cd taberu-mate/backend
uv sync # 请提前安装uv作为包管理器
```
### Step2-2 部署Vue环境
```bash
cd taberu-mate/frontend
npm install # 请提前安装NodeJS环境
```
### Step3 配置环境变量
后端：
```bash
cd ../backend
cp .env.example .env
```

前端：
```bash
cd ../frontend
cp .env.example .env.development
```

如果只是想先跑通菜单识别演示，可以在 `backend/.env` 中配置本地 Mock：
```bash
TABERU_MATE_AI_MENU_SCAN_MOCK_RESPONSE_PATH="/Users/ariakage/Downloads/proj/taberu-mate/temp/1.json"
```

如果要调用真实 AI 服务，请在 `backend/.env` 中补充：
```bash
TABERU_MATE_AI_API_KEY="your-api-key"
TABERU_MATE_AI_BASE_URL="https://api.openai.com/v1"
TABERU_MATE_AI_MODEL="gpt-5.5"
```

### Step4 启动后端
```bash
cd ../backend
uv run fastapi dev src/taberu_mate_backend/main.py --host 0.0.0.0 --port 8000
```

启动后可访问：
- Swagger UI: http://127.0.0.1:8000/docs
- Health Check: http://127.0.0.1:8000/api/v1/health

### Step5 启动前端
另开一个终端：
```bash
cd taberu-mate/frontend
npm run dev
```

默认访问地址：
- WebApp: http://127.0.0.1:5173/

### Step6 开始使用
1. 打开前端 WebApp
2. 在「我的」页面注册或登录账号
3. 回到首页拍摄或上传菜单
4. 在「点单」页面筛选菜品、填写备注并生成当地语言点菜单
5. 生成结果会同步到「我的」页面的饭饭档案和历史菜单中

## 🗂️ 项目结构
本仓库采用Monorepo的形式，前后端和文档均在仓库目录下
```
taberu-mate/
├── frontend/ # WebApp 前端 
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── backend/ # API 后端 （使用FastAPI）
│   ├── src/taberu_mate_backend
│   │   ├── main.py
│   │   └── ...
│   ├── tests/
│   ├── pyproject.toml
│   └── uv.lock
│
├── docs/ # 项目文档
├── .env.example
└── README.md
```

## 📖 使用文档

### 启动后端服务

```bash
cd backend
cp .env.example .env
uv run fastapi dev src/taberu_mate_backend/main.py --host 0.0.0.0 --port 8000
```

启动后可以访问：

- Swagger UI: http://127.0.0.1:8000/docs
- Health Check: http://127.0.0.1:8000/api/v1/health

### 启动前端 WebApp

```bash
cd frontend
cp .env.example .env.development
npm run dev
```

默认访问地址：

- WebApp: http://127.0.0.1:5173/

### 本地菜单识别 Mock

如果暂时不想调用真实 AI 模型，可以把后端 `.env` 里的 mock 路径指向本地示例菜单：

```bash
TABERU_MATE_AI_MENU_SCAN_MOCK_RESPONSE_PATH="/Users/ariakage/Downloads/proj/taberu-mate/temp/1.json"
```

这样菜单识别接口会直接返回示例 JSON，适合前端联调和演示。

### 更多文档

- 后端说明：[backend/README.md](backend/README.md)
- 前端说明：[frontend/README.md](frontend/README.md)
- 认证流程：[backend/docs/auth-flow.md](backend/docs/auth-flow.md)
- 菜单识别 API：[backend/docs/menu-scan-api.md](backend/docs/menu-scan-api.md)

## 🛠️ 配置说明

### 后端配置

后端配置文件位于 `backend/.env`，可从 `backend/.env.example` 复制生成。

常用配置项：

- `TABERU_MATE_DATABASE_PATH`：SQLite 数据库路径
- `TABERU_MATE_AUTH_TOKEN_SECRET`：认证密钥，部署时请替换为足够长的随机字符串
- `TABERU_MATE_AUTH_COOKIE_SECURE`：本地 HTTP 开发可设为 `false`
- `TABERU_MATE_ALLOWED_ORIGINS`：允许访问后端的前端地址
- `TABERU_MATE_AI_API_KEY`：AI 服务 API Key
- `TABERU_MATE_AI_BASE_URL`：兼容 OpenAI API 的服务地址
- `TABERU_MATE_AI_MODEL`：默认 AI 模型
- `TABERU_MATE_AI_MENU_SCAN_MOCK_RESPONSE_PATH`：本地菜单识别 Mock 文件路径

### 前端配置

前端配置文件位于 `frontend/.env.development`，可从 `frontend/.env.example` 复制生成。

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

请确保该地址指向后端 API 前缀，而不是单纯的后端端口。

### 常用检查命令

后端：

```bash
cd backend
uv run pytest
uv run ruff check .
uv run mypy src
```

前端：

```bash
cd frontend
npm run type-check
npm run test:unit -- --run
npm run build
```

## 🤝 贡献指南

欢迎提交 Issue、建议和 Pull Request。为了让协作更顺畅，建议遵循以下流程：

1. Fork 本仓库并创建功能分支
2. 修改代码前先确认对应目录的 README 和 docs
3. 后端功能请补充 pytest 测试
4. 前端交互请补充 Vitest 或组件测试
5. 提交前运行对应目录的检查命令
6. PR 中说明改动动机、主要实现和测试结果

推荐提交信息格式：

```git
feat(menu): add AI menu scanning flow
fix(auth): handle expired access tokens
docs(readme): expand frontend setup guide
test(profile): cover order history dashboard
```

## 🙏 致谢

感谢这些优秀项目让食べ友可以快速搭建起来：

- [FastAPI](https://fastapi.tiangolo.com/)：后端 API 框架
- [Vue](https://vuejs.org/)：前端应用框架
- [Vite](https://vite.dev/)：前端开发与构建工具
- [Pinia](https://pinia.vuejs.org/)：前端状态管理
- [Vant](https://vant-ui.github.io/vant/)：移动端组件库
- [Tailwind CSS](https://tailwindcss.com/)：样式工具链
- [uv](https://docs.astral.sh/uv/)：Python 依赖管理
- [OpenAI](https://openai.com/)：AI 能力与兼容 API 生态

## 🌟 Star数历史

<picture>
  <source
    media="(prefers-color-scheme: dark)"
    srcset="https://api.star-history.com/svg?repos=ariakage/taberu-mate&type=Date&theme=dark"
  />
  <source
    media="(prefers-color-scheme: light)"
    srcset="https://api.star-history.com/svg?repos=ariakage/taberu-mate&type=Date"
  />
  <img
    alt="Star History Chart"
    src="https://api.star-history.com/svg?repos=ariakage/taberu-mate&type=Date"
  />
</picture>

<div align="center">
  <strong style="font-size: 32px;">TaberuMate</strong>
  <br />
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-AGPL--3.0--only-blue.svg?style=flat-square" alt="License: AGPL-3.0-only" />
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/python-3.13%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.13+" />
  </a>
  <a href="https://nodejs.org/">
    <img src="https://img.shields.io/badge/node.js-20%2B-339933?style=flat-square&logo=node.js&logoColor=white" alt="Node.js 20+" />
  </a>
  <a href="https://vuejs.org/">
    <img src="https://img.shields.io/badge/vue-3-42b883?style=flat-square&logo=vuedotjs&logoColor=white" alt="Vue 3" />
  </a>
  <a href="https://docs.astral.sh/uv/">
    <img src="https://img.shields.io/badge/package%20manager-uv-261230?style=flat-square" alt="uv" />
  </a>
</div>

<hr />

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
### Step3 ...
...

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
│   ├── app/
│   │   ├── main.py
│   │   └── ...
│   ├── pyproject.toml
│   └── uv.lock
│
├── docs/ # 项目文档
├── .env.example
└── README.md
```

## 📖 使用文档

## 🛠️ 配置说明

## 🤝 贡献指南

## 🙏 致谢

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
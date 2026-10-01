# 在线表格智能问卷系统

一个面向问卷设计、发布、填写、回收、分析与导出的前后端分离系统。项目使用 Vue 3 构建管理端和公开填写页面，使用 FastAPI 提供接口服务，并以 MySQL 8 保存用户、问卷、答卷和统计数据。

## 项目解决什么问题

传统问卷工作经常需要在多个工具之间切换：编辑题目、生成分享链接、收集答卷、整理表格、分析结果和识别异常数据彼此割裂。本项目将这些环节整合到同一套系统中，主要解决：

- 问卷创建、发布和回收流程分散的问题；
- 单选、多选、文本等不同题型难以统一管理的问题；
- 分享链接、二维码和填写来源缺少统一追踪的问题；
- 答卷需要手工整理、统计和导出的问题；
- 填写超时、异常答卷和无效数据难以及时发现的问题；
- 从零设计问卷和总结开放文本耗时较长的问题。

AI 能力为可选功能。未配置 DeepSeek API Key 时，账号、问卷编辑、发布、填写、统计、异常检测和导出等核心功能仍可使用。

## 主要功能

### 用户与账户

- 邮箱注册、登录和 JWT 身份认证；
- 查看及修改姓名、手机号、公司等资料；
- 修改密码和上传头像；
- 登录失效后自动清除本地会话。

### 问卷设计与管理

- 创建、编辑、复制、删除、发布和关闭问卷；
- 支持单选、多选、文本、日期、评分、数字和手机号题型；
- 配置必填项、选项顺序、匿名填写、限制重复提交、提交后展示结果和填写超时时间；
- 上传或移除问卷背景图片；
- 生成公开填写链接和二维码。

### 公开填写与答卷管理

- 填写者无需登录即可通过公开码访问已发布问卷；
- 记录公开链接、二维码或微信等填写来源；
- 记录填写会话、活动时间和填写耗时；
- 校验必填题、题型、选项归属和重复提交限制；
- 查看答卷列表和答卷详情；
- 扫描异常答卷并手动标记答卷是否有效；
- 收集填写体验评分和问题反馈。

### 数据分析与导出

- 查看问卷总览、答卷趋势、来源渠道和逐题统计；
- 对选择题、评分题和文本题进行分类展示；
- 将答卷导出为 XLSX、CSV 或 JSON；
- 查看导出任务状态、下载文件和删除导出记录。

### AI 问卷助手（可选）

- 根据自然语言需求生成问卷；
- 优化已有题目和选项；
- 推荐调查维度；
- 总结文本答卷；
- 生成数据洞察并进行连续分析对话。

## 技术栈

- 前端：Vue 3、TypeScript、Vite、Lucide Vue Next
- 后端：FastAPI、SQLAlchemy AsyncIO、Pydantic、JWT
- 数据库：MySQL 8、aiomysql
- AI：LangChain、LangGraph、DeepSeek OpenAI 兼容接口
- 导出：openpyxl

## 项目结构

```text
.
├─ backend/                       # FastAPI 后端
│  ├─ config/                     # 数据库配置
│  ├─ crud/                       # 业务逻辑
│  ├─ models/                     # SQLAlchemy 模型
│  ├─ router/                     # API 路由
│  ├─ schemas/                    # 请求数据模型
│  ├─ utils/                      # JWT 和密码工具
│  ├─ .env.example                # 环境变量示例
│  ├─ main.py                     # 后端入口
│  └─ requirements.txt            # Python 依赖
├─ frontend/                      # Vue 前端
│  ├─ src/
│  ├─ package.json
│  └─ vite.config.ts
├─ database/
│  ├─ schema.sql                  # 数据库结构
│  └─ 演示数据.sql                # 可选演示数据
├─ 技术文档/
│  └─ API.md                      # 完整接口说明
├─ 项目对应讲解文档/               # 需求、设计和用户手册
├─ 01_安装依赖.bat
├─ 02_启动系统.bat
└─ 运行前必读_配置修改说明.txt
```

## 安装方法

### 环境要求

- Python 3.9 或更高版本；
- Node.js 18 或更高版本；
- MySQL 8.0 或更高版本；
- Windows 可直接使用仓库提供的批处理脚本。

### 方式一：Windows 自动安装

1. 使用 MySQL 客户端执行 `database/schema.sql`；
2. 双击根目录下的 `01_安装依赖.bat`；
3. 打开自动生成的 `backend/.env`，完成数据库和安全配置；
4. 双击 `02_启动系统.bat`。

安装脚本会创建 Python 虚拟环境、安装前后端依赖并构建前端文件。

### 方式二：手动安装

初始化数据库：

```text
mysql -u root -p -e "source C:/项目路径/database/schema.sql"
```

安装后端依赖：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

安装前端依赖：

```powershell
cd frontend
npm install
```

### 配置环境变量

编辑 `backend/.env`：

```dotenv
ASYNC_DATABASE_URL=mysql+aiomysql://root:你的数据库密码@127.0.0.1:3306/online_form?charset=utf8mb4
SECRET_KEY=请替换为至少32字符的随机字符串
FRONTEND_BASE_URL=http://localhost:5173

# 以下为可选 AI 配置
DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com

SQLALCHEMY_ECHO=false
```

数据库密码包含 `@`、`:`、`/`、`#` 等特殊字符时，需要先进行 URL 编码。不要将包含真实密码或 API Key 的 `backend/.env` 提交到仓库。

如需加载比赛演示数据，可在执行 `database/schema.sql` 后再执行 `database/演示数据.sql`。该脚本中的账号和密码仅用于本地演示，不应直接用于公网部署。

## 使用方法

### 启动后端

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
```

后端接口文档：<http://localhost:8000/docs>

### 启动前端

另开一个终端：

```powershell
cd frontend
npm run dev
```

浏览器访问：<http://localhost:5173>

开发环境下，Vite 会将 `/api` 和 `/uploads` 请求代理到 `http://127.0.0.1:8000`。

### 基本操作流程

1. 注册账号并登录；
2. 在问卷编辑器中填写标题、说明并添加题目；
3. 保存问卷后发布，获取公开链接或二维码；
4. 填写者通过公开页面提交答卷；
5. 在问卷列表、数据分析和导出页面查看结果；
6. 根据需要扫描异常答卷、标记有效性或导出数据；
7. 如已配置 DeepSeek API Key，可在编辑和分析过程中使用 AI 功能。

### 局域网访问

前后端均以 `0.0.0.0` 启动后，同一局域网设备可访问：

```text
http://电脑局域网IP:5173
```

同时将 `backend/.env` 中的 `FRONTEND_BASE_URL` 改为对应地址，例如：

```dotenv
FRONTEND_BASE_URL=http://192.168.1.10:5173
```

否则生成的问卷链接和二维码仍会指向 `localhost`。

## 输入输出示例

以下示例使用后端实际提供的 JSON 接口。管理端接口需要在请求头中携带登录后取得的 JWT：

```text
Authorization: Bearer <登录返回的Token>
```

### 示例一：创建问卷

请求：`POST /api/questionnaire/create`

```json
{
  "title": "客户满意度调查",
  "description": "感谢您参与本次调查",
  "anonymous": true,
  "oneResponse": false,
  "showResult": false,
  "responseTimeoutMinutes": 30,
  "questions": [
    {
      "type": "single",
      "title": "您对本次服务是否满意？",
      "required": true,
      "sortOrder": 0,
      "options": [
        { "label": "满意", "sortOrder": 0 },
        { "label": "不满意", "sortOrder": 1 }
      ]
    },
    {
      "type": "text",
      "title": "其他建议",
      "required": false,
      "sortOrder": 1,
      "options": []
    }
  ]
}
```

响应：

```json
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "id": 1001,
    "title": "客户满意度调查",
    "status": "draft",
    "createdAt": "2026-09-17T10:00:00"
  }
}
```

### 示例二：提交公开答卷

请求：`POST /api/public/response/submit`，无需登录。

```json
{
  "publicCode": "sv_8f4d2a9c",
  "answers": [
    {
      "questionId": 501,
      "optionIds": [9001],
      "content": null
    },
    {
      "questionId": 502,
      "optionIds": [],
      "content": "希望增加批量操作"
    }
  ],
  "respondentName": "张三",
  "respondentEmail": "zhangsan@example.com",
  "source": "publicLink",
  "durationSeconds": 138,
  "sessionToken": "填写会话接口返回的令牌"
}
```

响应：

```json
{
  "code": 200,
  "message": "提交成功",
  "data": {
    "responseId": 70001,
    "submittedAt": "2026-09-17T10:38:00",
    "showResult": false
  }
}
```

示例中的 ID、公开码、Token 和时间仅用于说明，实际值以接口返回为准。完整接口定义参见[技术文档/API.md](技术文档/API.md)。

## 相关文档

- [完整 API 文档](技术文档/API.md)
- [功能需求说明书](项目对应讲解文档/01_功能需求说明书.md)
- [概要设计说明书](项目对应讲解文档/02_概要设计说明书.md)
- [详细设计说明书](项目对应讲解文档/03_详细设计说明书.md)
- [数据库设计说明书](项目对应讲解文档/04_数据库设计说明书.md)
- [软件界面设计书](项目对应讲解文档/05_软件界面设计书.md)
- [用户操作手册](项目对应讲解文档/06_用户操作手册.md)
- [运行前配置说明](运行前必读_配置修改说明.txt)

## License

本项目采用 [MIT License](LICENSE)。

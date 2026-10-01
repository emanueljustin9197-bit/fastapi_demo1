# API 接口文档

## 概述

本文档基于当前项目后端实际代码整理，覆盖用户、问卷、公开填写、答卷、数据分析、异常检测、数据导出、AI 助手和用户反馈等 45 个接口。

## 基础 URL

```text
http://localhost:8000
```

后端启动后可访问自动接口页：

```text
http://localhost:8000/docs
```

## 认证方式

除注册、登录、公开问卷、公开提交、填写会话、填写活动、公开反馈和二维码接口外，其余接口均需要在请求头中携带登录返回的 Token：

```text
Authorization: Bearer token值
```

Token 无效、过期或所属用户已停用时返回 `401`。

## 通用约定

### JSON 响应

普通接口统一返回：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

分页接口的 `data` 通常为：

```json
{
  "list": [],
  "total": 0,
  "hasMore": false
}
```

二维码和导出下载接口直接返回文件流，不使用通用 JSON 结构。

### 日期时间

- 日期：`YYYY-MM-DD`
- 日期时间：ISO 8601，例如 `2026-09-17T10:30:00`
- 后端内部时间以服务器时间为准

### 常见错误

| HTTP 状态码 | 说明 |
| --- | --- |
| 400 | 业务参数不正确，例如当前密码错误或必填题未回答 |
| 401 | Token 无效、登录失效或用户已停用 |
| 404 | 数据不存在，或当前用户无权访问 |
| 409 | 数据冲突，例如邮箱已注册、重复提交或重复反馈 |
| 422 | 请求字段缺失、类型错误或不满足长度/范围限制 |
| 500 | 服务端缺少必要配置，例如未配置 AI Key |
| 502 | DeepSeek 请求失败，或 AI 返回格式无法解析 |

FastAPI 参数校验错误格式：

```json
{
  "detail": [
    {
      "loc": ["body", "fieldName"],
      "msg": "Field required",
      "type": "missing"
    }
  ]
}
```

## 公共数据结构

### 题目对象 QuestionInput

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| id | integer | 更新时可选 | 题目 ID |
| type | string | 是 | `single`、`multiple`、`text`、`date`、`rating`、`number`、`phone` |
| title | string | 是 | 题目标题 |
| required | boolean | 否 | 是否必填，默认 `false` |
| sortOrder | integer | 否 | 排序值，默认 `0` |
| options | array | 否 | 选项数组，默认 `[]`；单选和多选至少两个选项 |

### 选项对象 OptionInput

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| id | integer | 更新时可选 | 选项 ID |
| label | string | 是 | 选项文字 |
| sortOrder | integer | 否 | 排序值，默认 `0` |

### 问卷对象 QuestionnaireInput

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| id | integer | 更新时是 | 问卷 ID |
| title | string | 是 | 问卷名称 |
| description | string/null | 否 | 问卷说明 |
| anonymous | boolean | 否 | 是否匿名，默认 `true` |
| oneResponse | boolean | 否 | 是否限制同一填写者只提交一次，默认 `false` |
| showResult | boolean | 否 | 提交后是否显示结果，默认 `false` |
| questions | array | 否 | `QuestionInput` 数组，默认 `[]` |
| responseTimeoutMinutes | integer | 否 | 填写时限，范围 1-1440 分钟，默认 `30` |

## 用户管理模块

### 1. 用户注册

- **接口地址**：`POST /api/user/register`
- **认证**：不需要
- **Content-Type**：`application/json`

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| email | string | 是 | 登录邮箱，不能与现有邮箱或用户名重复 |
| password | string | 是 | 密码，长度 6-32 |
| name | string | 是 | 显示名称，长度 1-100 |

请求示例：

```json
{
  "email": "admin@example.com",
  "password": "123456",
  "name": "系统管理员"
}
```

响应示例：

```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "token": "JWT_TOKEN",
    "userInfo": {
      "id": 1,
      "email": "admin@example.com",
      "name": "系统管理员",
      "avatar": null,
      "phone": null,
      "company": null
    }
  }
}
```

### 2. 用户登录

- **接口地址**：`POST /api/user/login`
- **认证**：不需要

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| email | string | 是 | 登录邮箱 |
| password | string | 是 | 登录密码 |

```json
{
  "email": "admin@example.com",
  "password": "123456"
}
```

成功响应中的 `data` 与注册接口相同，包含 `token` 和 `userInfo`。邮箱或密码错误返回 `401`。

### 3. 获取当前用户信息

- **接口地址**：`GET /api/user/info`
- **认证**：需要

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "email": "admin@example.com",
    "name": "系统管理员",
    "avatar": "/uploads/avatars/example.png",
    "phone": "13800000000",
    "company": "星图数据科技"
  }
}
```

### 4. 更新用户信息

- **接口地址**：`PUT /api/user/update`
- **认证**：需要

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| name | string/null | 否 | 显示名称，非空时长度 1-100 |
| avatar | string/null | 否 | 头像 URL |
| phone | string/null | 否 | 手机号 |
| company | string/null | 否 | 所属组织 |

```json
{
  "name": "问卷管理员",
  "phone": "13800000000",
  "company": "星图数据科技"
}
```

返回更新后的完整 `userInfo` 对象。

### 5. 修改密码

- **接口地址**：`PUT /api/user/password`
- **认证**：需要

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| oldPassword | string | 是 | 当前密码 |
| newPassword | string | 是 | 新密码，长度 6-32 |

```json
{
  "oldPassword": "123456",
  "newPassword": "new_password"
}
```

```json
{
  "code": 200,
  "message": "密码修改成功",
  "data": null
}
```

### 6. 上传头像

- **接口地址**：`POST /api/user/avatar`
- **认证**：需要
- **Content-Type**：`multipart/form-data`

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| file | file | 是 | 头像文件 |

请求示例：

```bash
curl -X POST "http://localhost:8000/api/user/avatar" \
  -H "Authorization: Bearer JWT_TOKEN" \
  -F "file=@avatar.png"
```

返回更新后的完整 `userInfo` 对象，其中 `avatar` 为可访问的头像 URL。

## 问卷管理模块

本模块除二维码接口外均需要认证，并且只能操作当前用户自己的问卷。

### 1. 获取问卷统计

- **接口地址**：`GET /api/questionnaire/statistics`
- **认证**：需要

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "questionnaireCount": 12,
    "responseCount": 1286,
    "activeCount": 5,
    "averageCompletionRate": 87.0
  }
}
```

### 2. 获取我的问卷列表

- **接口地址**：`GET /api/questionnaire/list`
- **认证**：需要

| Query 参数 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| keyword | string | 否 | - | 标题关键词 |
| status | string | 否 | - | `draft`、`active`、`closed` |
| page | integer | 否 | 1 | 页码，最小 1 |
| pageSize | integer | 否 | 10 | 每页数量，范围 1-100 |

```text
GET /api/questionnaire/list?keyword=满意度&status=active&page=1&pageSize=10
```

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1001,
        "title": "客户满意度调查",
        "description": "感谢参与",
        "status": "active",
        "anonymous": true,
        "oneResponse": false,
        "showResult": false,
        "publicCode": "sv_8f4d2a9c",
        "publicUrl": "http://localhost:5173/s/sv_8f4d2a9c",
        "questionCount": 8,
        "responseCount": 426,
        "completionRate": 92.4,
        "createdAt": "2026-09-01T10:00:00",
        "updatedAt": "2026-09-17T10:24:00"
      }
    ],
    "total": 12,
    "hasMore": true
  }
}
```

### 3. 创建问卷

- **接口地址**：`POST /api/questionnaire/create`
- **认证**：需要
- **请求体**：`QuestionnaireInput`

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

### 4. 获取问卷详情

- **接口地址**：`GET /api/questionnaire/detail?id=1001`
- **认证**：需要

| Query 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| id | integer | 是 | 问卷 ID |

`data` 包含问卷基础字段、`responseTimeoutMinutes`、`publicCode`、`publicUrl`、`backgroundImage`、发布时间、关闭时间及完整题目和选项数组。没有自定义背景时 `backgroundImage` 为 `null`。

### 5. 更新问卷

- **接口地址**：`PUT /api/questionnaire/update`
- **认证**：需要
- **请求体**：`QuestionnaireInput`，其中 `id` 和 `title` 必填

```json
{
  "id": 1001,
  "title": "客户满意度调查（新版）",
  "description": "更新后的问卷说明",
  "anonymous": true,
  "oneResponse": true,
  "showResult": false,
  "responseTimeoutMinutes": 45,
  "questions": []
}
```

```json
{
  "code": 200,
  "message": "保存成功",
  "data": {
    "id": 1001,
    "updatedAt": "2026-09-17T10:30:00"
  }
}
```

### 6. 上传问卷背景

- **接口地址**：`POST /api/questionnaire/background?id=1001`
- **认证**：需要
- **Content-Type**：`multipart/form-data`

| 参数名 | 位置 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- | --- |
| id | Query | integer | 是 | 问卷 ID，最小 1 |
| file | Form | file | 是 | JPG、PNG 或 WEBP 图片，最大 5MB |

```json
{
  "code": 200,
  "message": "背景图片已保存",
  "data": {
    "backgroundImage": "/uploads/backgrounds/1001_example.png"
  }
}
```

上传新背景会自动删除该问卷原来的背景文件。

### 7. 移除问卷背景

- **接口地址**：`DELETE /api/questionnaire/background?id=1001`
- **认证**：需要

```json
{ "code": 200, "message": "背景图片已移除", "data": null }
```

### 8. 删除问卷

- **接口地址**：`DELETE /api/questionnaire/delete?id=1001`
- **认证**：需要

成功返回：

```json
{ "code": 200, "message": "删除成功", "data": null }
```

### 9. 复制问卷

- **接口地址**：`POST /api/questionnaire/copy`
- **认证**：需要

```json
{ "id": 1001 }
```

```json
{
  "code": 200,
  "message": "复制成功",
  "data": {
    "id": 1002,
    "title": "客户满意度调查 - 副本",
    "status": "draft"
  }
}
```

复制内容包含问卷设置、填写时限、背景图片、题目和选项，新问卷状态为草稿。

### 10. 发布问卷

- **接口地址**：`POST /api/questionnaire/publish`
- **认证**：需要

```json
{ "id": 1001 }
```

```json
{
  "code": 200,
  "message": "发布成功",
  "data": {
    "id": 1001,
    "status": "active",
    "publicCode": "sv_8f4d2a9c",
    "publicUrl": "http://localhost:5173/s/sv_8f4d2a9c",
    "qrCodeUrl": "/api/questionnaire/qrcode?publicCode=sv_8f4d2a9c",
    "publishedAt": "2026-09-17T10:35:00"
  }
}
```

### 11. 获取问卷二维码

- **接口地址**：`GET /api/questionnaire/qrcode?publicCode=sv_8f4d2a9c`
- **认证**：不需要

| Query 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| publicCode | string | 是 | 已发布问卷的公开码，长度 1-64 |

成功时返回 `image/png` 文件流。问卷不存在或未发布返回 `404`。

### 12. 停止收集

- **接口地址**：`POST /api/questionnaire/close`
- **认证**：需要

```json
{ "id": 1001 }
```

```json
{
  "code": 200,
  "message": "问卷已停止收集",
  "data": { "id": 1001, "status": "closed" }
}
```

## 公开填写模块

本模块不需要登录 Token。

### 1. 获取公开问卷

- **接口地址**：`GET /api/public/questionnaire?publicCode=sv_8f4d2a9c`
- **认证**：不需要

| Query 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| publicCode | string | 是 | 问卷公开码 |

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1001,
    "title": "客户满意度调查",
    "description": "感谢参与",
    "anonymous": true,
    "backgroundImage": "/uploads/backgrounds/1001_example.png",
    "questions": [
      {
        "id": 501,
        "type": "single",
        "title": "您对本次服务是否满意？",
        "required": true,
        "sortOrder": 0,
        "options": [
          { "id": 9001, "label": "满意", "sortOrder": 0 },
          { "id": 9002, "label": "不满意", "sortOrder": 1 }
        ]
      }
    ]
  }
}
```

只有 `active` 状态的问卷可以通过公开码获取。

### 2. 开始填写会话

- **接口地址**：`POST /api/public/response/start`
- **认证**：不需要

```json
{ "publicCode": "sv_8f4d2a9c" }
```

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "sessionToken": "填写会话令牌"
  }
}
```

该令牌用于统计完成率、识别填写超时，并应在提交答卷时通过 `sessionToken` 原样传回。

### 3. 更新填写活动时间

- **接口地址**：`POST /api/public/response/activity`
- **认证**：不需要

```json
{ "sessionToken": "填写会话令牌" }
```

```json
{ "code": 200, "message": "success", "data": null }
```

前端可在用户填写期间定时调用。令牌无效或会话已结束时接口仍返回成功，但不会更新数据。

### 4. 提交答卷

- **接口地址**：`POST /api/public/response/submit`
- **认证**：不需要

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| publicCode | string | 是 | - | 问卷公开码 |
| answers | array | 是 | - | 回答数组；非必填题可不传对应回答 |
| respondentName | string/null | 否 | null | 填写者姓名，最长 100 |
| respondentEmail | string/null | 否 | null | 填写者邮箱，最长 320 |
| source | string | 否 | `publicLink` | `publicLink`、`wechat`、`qrCode` |
| durationSeconds | integer | 否 | 0 | 填写耗时，最小 0 秒 |
| sessionToken | string/null | 否 | null | 开始填写接口返回的令牌 |

回答对象：

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| questionId | integer | 是 | 题目 ID |
| optionIds | integer[] | 否 | 单选或多选选择的选项 ID，默认 `[]` |
| content | string/null | 否 | 文本、日期、评分、数字或手机号内容 |

```json
{
  "publicCode": "sv_8f4d2a9c",
  "answers": [
    { "questionId": 501, "optionIds": [9001], "content": null },
    { "questionId": 502, "optionIds": [], "content": "希望增加批量操作" }
  ],
  "respondentName": "张三",
  "respondentEmail": "zhangsan@example.com",
  "source": "publicLink",
  "durationSeconds": 138,
  "sessionToken": "填写会话令牌"
}
```

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

后端会重新校验必填题、题目归属、选项归属和单选题选项数量。启用 `oneResponse` 后，同一填写来源的重复提交返回 `409`。

### 5. 提交填写体验反馈

- **接口地址**：`POST /api/public/feedback`
- **认证**：不需要

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| publicCode | string | 是 | 问卷公开码，长度 1-64 |
| questionnaireId | integer | 是 | 问卷 ID，最小 1 |
| responseId | integer | 是 | 已提交的答卷 ID，最小 1 |
| rating | integer | 是 | 评分 1-5 |
| issueType | string | 否 | `none`、`usability`、`content`、`performance`、`other`，默认 `none` |
| content | string/null | 否 | 反馈内容，最长 500 |

```json
{
  "publicCode": "sv_8f4d2a9c",
  "questionnaireId": 1001,
  "responseId": 70001,
  "rating": 4,
  "issueType": "usability",
  "content": "手机端部分按钮不够明显"
}
```

```json
{
  "code": 200,
  "message": "反馈提交成功",
  "data": { "id": 301 }
}
```

同一答卷只能提交一次反馈，重复提交返回 `409`。

## 答卷管理与异常检测模块

本模块全部需要认证，并且只能查看和操作当前用户问卷下的答卷。

### 1. 获取答卷列表

- **接口地址**：`GET /api/response/list`
- **认证**：需要

| Query 参数 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| questionnaireId | integer | 是 | - | 问卷 ID |
| page | integer | 否 | 1 | 页码，最小 1 |
| pageSize | integer | 否 | 10 | 每页数量，范围 1-100 |
| startDate | date | 否 | - | 开始日期，包含当天 |
| endDate | date | 否 | - | 结束日期，包含当天 |
| source | string | 否 | - | 来源筛选 |

```text
GET /api/response/list?questionnaireId=1001&page=1&pageSize=10&startDate=2026-09-01&endDate=2026-09-17
```

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 70001,
        "respondentName": "张三",
        "respondentEmail": "zhangsan@example.com",
        "source": "publicLink",
        "durationSeconds": 138,
        "isValid": true,
        "submittedAt": "2026-09-17T10:38:00"
      }
    ],
    "total": 426,
    "hasMore": true
  }
}
```

### 2. 获取答卷详情

- **接口地址**：`GET /api/response/detail?id=70001`
- **认证**：需要

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 70001,
    "questionnaireId": 1001,
    "respondentName": "张三",
    "respondentEmail": "zhangsan@example.com",
    "source": "publicLink",
    "durationSeconds": 138,
    "isValid": true,
    "submittedAt": "2026-09-17T10:38:00",
    "answers": [
      {
        "questionId": 501,
        "questionTitle": "您对本次服务是否满意？",
        "optionIds": [9001],
        "optionLabels": ["满意"],
        "content": null
      }
    ]
  }
}
```

### 3. 获取异常答卷列表

- **接口地址**：`GET /api/response/anomalies?questionnaireId=1001`
- **认证**：需要

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 70001,
        "respondentName": "张三",
        "respondentEmail": "zhangsan@example.com",
        "durationSeconds": 8,
        "submittedAt": "2026-09-17T10:38:00",
        "isValid": false,
        "riskScore": 65,
        "riskReasons": ["填写时间异常短：8 秒", "作答题目比例低于 30%"],
        "reviewStatus": "confirmed"
      }
    ],
    "total": 1
  }
}
```

列表包含风险分数不低于 40，或被人工确认为异常的答卷。

### 4. 扫描异常答卷

- **接口地址**：`POST /api/response/anomalies/scan`
- **认证**：需要

```json
{ "questionnaireId": 1001 }
```

```json
{
  "code": 200,
  "message": "检测完成",
  "data": {
    "scannedCount": 426,
    "anomalyCount": 12
  }
}
```

检测依据包括填写时间过短、作答比例过低、连续选择相同位置和文本答案高度重复。扫描不会覆盖管理员已经确认或排除的人工结论。

### 5. 修改答卷有效性

- **接口地址**：`PUT /api/response/validity`
- **认证**：需要

```json
{
  "responseId": 70001,
  "isValid": false
}
```

```json
{
  "code": 200,
  "message": "更新成功",
  "data": {
    "responseId": 70001,
    "isValid": false,
    "reviewStatus": "confirmed"
  }
}
```

`isValid=false` 时 `reviewStatus` 为 `confirmed`；`isValid=true` 时为 `dismissed`。

## 问卷分析模块

本模块全部需要认证。

### 1. 获取分析概览

- **接口地址**：`GET /api/analysis/overview?questionnaireId=1001`
- **认证**：需要

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "responseCount": 426,
    "validResponseCount": 412,
    "validRate": 96.7,
    "averageDurationSeconds": 138.0,
    "completionRate": 92.4,
    "abandonedCount": 35,
    "responseGrowthRate": 18.2
  }
}
```

### 2. 获取答卷趋势

- **接口地址**：`GET /api/analysis/trend`
- **认证**：需要

| Query 参数 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| questionnaireId | integer | 是 | - | 问卷 ID，最小 1 |
| days | integer | 否 | 7 | 统计天数，范围 1-365 |

```json
{
  "code": 200,
  "message": "success",
  "data": [
    { "date": "2026-09-15", "count": 36 },
    { "date": "2026-09-16", "count": 52 },
    { "date": "2026-09-17", "count": 47 }
  ]
}
```

### 3. 获取来源渠道统计

- **接口地址**：`GET /api/analysis/channels?questionnaireId=1001`
- **认证**：需要

```json
{
  "code": 200,
  "message": "success",
  "data": [
    { "source": "wechat", "label": "微信分享", "count": 205, "percentage": 48.1 },
    { "source": "publicLink", "label": "公开链接", "count": 136, "percentage": 31.9 },
    { "source": "qrCode", "label": "二维码", "count": 85, "percentage": 20.0 }
  ]
}
```

### 4. 获取题目统计

- **接口地址**：`GET /api/analysis/questions?questionnaireId=1001`
- **认证**：需要

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "questionId": 501,
      "type": "single",
      "title": "您对本次服务是否满意？",
      "answerCount": 426,
      "skipCount": 0,
      "options": [
        { "optionId": 9001, "label": "满意", "count": 350, "percentage": 82.2 },
        { "optionId": 9002, "label": "不满意", "count": 76, "percentage": 17.8 }
      ],
      "keywords": []
    }
  ]
}
```

## 数据导出模块

本模块全部需要认证。

### 1. 创建导出任务

- **接口地址**：`POST /api/export/create`
- **认证**：需要

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| questionnaireId | integer | 是 | - | 问卷 ID |
| format | string | 否 | `csv` | `xlsx`、`csv`、`json` |
| range | string | 否 | `all` | `all`、`week`、`custom` |
| startDate | date/null | 否 | null | 自定义开始日期 |
| endDate | date/null | 否 | null | 自定义结束日期 |
| includeMetadata | boolean | 否 | true | 是否包含答卷 ID、提交时间、来源、姓名和邮箱等元数据 |

当 `range=custom` 时应同时提供 `startDate` 和 `endDate`。

```json
{
  "questionnaireId": 1001,
  "format": "xlsx",
  "range": "all",
  "startDate": null,
  "endDate": null,
  "includeMetadata": true
}
```

```json
{
  "code": 200,
  "message": "导出任务已创建",
  "data": {
    "id": "exp_20260917_001",
    "status": "completed",
    "createdAt": "2026-09-17T11:26:00"
  }
}
```

### 2. 获取导出记录列表

- **接口地址**：`GET /api/export/list?page=1&pageSize=10`
- **认证**：需要

| Query 参数 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| page | integer | 否 | 1 | 页码，最小 1 |
| pageSize | integer | 否 | 10 | 每页数量，范围 1-100 |

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": "exp_20260917_001",
        "questionnaireId": 1001,
        "questionnaireTitle": "客户满意度调查",
        "format": "xlsx",
        "range": "all",
        "startDate": null,
        "endDate": null,
        "includeMetadata": true,
        "status": "completed",
        "progress": 100,
        "fileName": "客户满意度调查_20260917.xlsx",
        "fileSize": 183204,
        "rowCount": 426,
        "downloadUrl": "/api/export/download?id=exp_20260917_001",
        "errorMessage": null,
        "createdAt": "2026-09-17T11:26:00",
        "completedAt": "2026-09-17T11:26:08"
      }
    ],
    "total": 1,
    "hasMore": false
  }
}
```

### 3. 获取导出任务状态

- **接口地址**：`GET /api/export/status?id=exp_20260917_001`
- **认证**：需要

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "exp_20260917_001",
    "status": "completed",
    "progress": 100,
    "downloadUrl": "/api/export/download?id=exp_20260917_001",
    "errorMessage": null
  }
}
```

### 4. 下载导出文件

- **接口地址**：`GET /api/export/download?id=exp_20260917_001`
- **认证**：需要

成功时直接返回 XLSX、CSV 或 JSON 文件流，并通过 `Content-Disposition` 提供 UTF-8 文件名。任务不存在、未完成或不属于当前用户时返回 `404`。

### 5. 删除导出记录

- **接口地址**：`DELETE /api/export/delete?id=exp_20260917_001`
- **认证**：需要

```json
{ "code": 200, "message": "删除成功", "data": null }
```

## AI 问卷助手模块

本模块全部需要认证，并依赖后端配置 `DEEPSEEK_API_KEY`。AI 服务不可用或返回内容无法解析时返回 `500` 或 `502`。

### 1. AI 生成问卷

- **接口地址**：`POST /api/ai/questionnaire/generate`
- **认证**：需要

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| prompt | string | 是 | - | 问卷需求 |
| questionCount | integer | 否 | 8 | 题目数量，范围 1-50 |
| language | string | 否 | `zh-CN` | 语言 |
| title | string/null | 否 | null | 标题建议 |
| existingQuestions | object[] | 否 | `[]` | 已有题目，AI 应避免重复 |

```json
{
  "prompt": "生成一份员工满意度调查，包含工作环境、薪酬和成长机会",
  "questionCount": 8,
  "language": "zh-CN",
  "title": "员工满意度调查",
  "existingQuestions": []
}
```

```json
{
  "code": 200,
  "message": "生成成功",
  "data": {
    "title": "员工满意度调查",
    "description": "本问卷用于了解员工的工作体验。",
    "questions": [
      {
        "type": "single",
        "title": "您对当前工作环境是否满意？",
        "required": true,
        "sortOrder": 0,
        "options": [
          { "label": "满意", "sortOrder": 0 },
          { "label": "不满意", "sortOrder": 1 }
        ]
      }
    ]
  }
}
```

### 2. AI 优化题目

- **接口地址**：`POST /api/ai/question/optimize`
- **认证**：需要

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| questions | QuestionInput[] | 是 | 待优化题目 |
| requirement | string/null | 否 | 额外优化要求 |

```json
{
  "questions": [
    {
      "type": "single",
      "title": "你觉得服务咋样？",
      "required": true,
      "options": [
        { "label": "很好" },
        { "label": "一般" }
      ]
    }
  ],
  "requirement": "修改得更加正式、中立"
}
```

响应 `data.questions` 为优化后的 `QuestionInput` 数组。

### 3. AI 推荐调查维度

- **接口地址**：`POST /api/ai/questionnaire/dimensions`
- **认证**：需要

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| title | string | 是 | 问卷标题 |
| description | string/null | 否 | 问卷说明 |
| questions | QuestionInput[] | 否 | 已有题目，默认 `[]` |

```json
{
  "title": "客户体验满意度调查",
  "description": "了解客户对产品和服务的满意程度",
  "questions": []
}
```

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "dimensions": [
      { "name": "产品功能", "description": "了解功能完整性和实用性" },
      { "name": "操作体验", "description": "了解易用性和交互体验" }
    ]
  }
}
```

### 4. AI 总结文本答卷

- **接口地址**：`POST /api/ai/response/summarize`
- **认证**：需要

```json
{
  "questionnaireId": 1001,
  "questionId": 503
}
```

```json
{
  "code": 200,
  "message": "总结成功",
  "data": {
    "answerCount": 286,
    "summary": "填写者主要关注操作体验和响应速度。",
    "keywords": [
      { "text": "操作体验", "count": null },
      { "text": "响应速度", "count": null }
    ]
  }
}
```

没有文本回答时返回 `answerCount=0`、固定提示文本和空关键词数组。

### 5. AI 生成数据洞察

- **接口地址**：`POST /api/ai/analysis/insight`
- **认证**：需要

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| questionnaireId | integer | 是 | - | 问卷 ID |
| range | string | 否 | `7d` | `7d` 或 `30d` |

```json
{
  "questionnaireId": 1001,
  "range": "7d"
}
```

```json
{
  "code": 200,
  "message": "分析成功",
  "data": {
    "findings": [
      {
        "conclusion": "整体有效答卷率较高",
        "evidence": [
          {
            "sourceType": "overview",
            "sourceId": "validRate",
            "text": "有效答卷率为 96.7%"
          }
        ]
      }
    ],
    "suggestions": ["继续跟踪低评分题目", "复核异常答卷"]
  }
}
```

### 6. AI 连续分析对话

- **接口地址**：`POST /api/ai/analysis/chat`
- **认证**：需要

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| questionnaireId | integer | 是 | - | 问卷 ID，最小 1 |
| range | string | 否 | `7d` | `7d` 或 `30d` |
| conversationId | string | 是 | - | 会话 ID，长度 8-100；同一会话必须持续使用相同值 |
| message | string | 是 | - | 用户问题，长度 1-500 |

```json
{
  "questionnaireId": 1001,
  "range": "7d",
  "conversationId": "analysis-1001-user-1",
  "message": "最近一周最需要关注的问题是什么？"
}
```

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "conversationId": "analysis-1001-user-1",
    "answer": "最近一周需要重点关注服务响应速度。",
    "evidence": [
      {
        "sourceType": "question",
        "sourceId": "503",
        "text": "题目 503 的负面反馈比例较高"
      }
    ]
  }
}
```

服务端对话记忆按“用户 ID + 问卷 ID + conversationId”隔离。前端切换页面后必须保留并复用 `conversationId`，否则会被视为新会话。当前服务端记忆存放在进程内存中，后端重启后会丢失。

### 7. 清空 AI 分析对话

- **接口地址**：`POST /api/ai/analysis/chat/clear`
- **认证**：需要

```json
{
  "questionnaireId": 1001,
  "conversationId": "analysis-1001-user-1"
}
```

```json
{ "code": 200, "message": "对话已清空", "data": null }
```

## 用户反馈管理模块

### 1. 获取问卷反馈列表

- **接口地址**：`GET /api/feedback/list?questionnaireId=1001`
- **认证**：需要

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 20,
    "averageRating": 4.3,
    "issueCount": 5,
    "list": [
      {
        "id": 301,
        "responseId": 70001,
        "rating": 4,
        "issueType": "usability",
        "content": "手机端部分按钮不够明显",
        "createdAt": "2026-09-17T10:45:00"
      }
    ]
  }
}
```

## 状态与枚举说明

### 问卷状态

| 值 | 说明 |
| --- | --- |
| draft | 草稿 |
| active | 正在收集 |
| closed | 已停止收集 |

### 题目类型

| 值 | 说明 |
| --- | --- |
| single | 单选题 |
| multiple | 多选题 |
| text | 文本题 |
| date | 日期题 |
| rating | 评分题 |
| number | 数字题 |
| phone | 手机号题 |

### 答卷来源

| 值 | 说明 |
| --- | --- |
| publicLink | 公开链接 |
| wechat | 微信分享 |
| qrCode | 二维码 |

### 异常复核状态

| 值 | 说明 |
| --- | --- |
| pending | 待复核 |
| confirmed | 已确认异常，答卷无效 |
| dismissed | 已排除异常，答卷有效 |

### 导出格式与范围

| 分类 | 可用值 |
| --- | --- |
| format | `xlsx`、`csv`、`json` |
| range | `all`、`week`、`custom` |
| status | `pending`、`processing`、`completed`、`failed` |

### 反馈问题类型

| 值 | 说明 |
| --- | --- |
| none | 没有具体问题 |
| usability | 易用性问题 |
| content | 内容问题 |
| performance | 性能问题 |
| other | 其他问题 |

## 后端校验与安全说明

1. 管理端接口根据 Token 识别当前用户，只允许操作该用户自己的问卷、答卷、导出记录和反馈。
2. 问卷发布前会校验标题、题目标题以及选择题选项；单选和多选至少需要两个有效选项。
3. 提交答卷时后端会校验必填题、题型、题目归属和选项归属；选填题可以不提交回答对象。
4. 草稿和已关闭问卷不能公开填写。
5. `oneResponse=true` 时后端会阻止重复提交。
6. 密码以哈希形式保存，不在任何接口中返回。
7. DeepSeek API Key 只保存在后端环境变量中，不返回给浏览器。
8. 二维码和导出下载是文件流接口；前端不要按 JSON 解析。
9. AI 对话的 `conversationId` 由前端生成和持久化；只有用户主动清空时才调用清空接口。
10. 本文档示例中的 ID、Token、时间和统计值仅用于说明，实际值以接口返回为准。

# `online_form` 模型对照表

当前 `app/models.py` 和 `model/` 目录按 Navicat 截图及之前运行日志中出现的字段建立
了 SQLAlchemy 映射。表名保持原样，字段使用数据库的下划线命名；接口层再转换为前端
使用的 camelCase（例如 `public_code` → `publicCode`）。

`users.id` 已按 `BIGINT UNSIGNED` 映射（在 SQLite 开发模式下自动退化为普通
`BIGINT`，不影响本地运行）。其他表的主键宽度会在收到对应 `CREATE TABLE` 后继续
逐张校准。

| 表 | 主要字段 | 关系 |
|---|---|---|
| `users` | `id`, `email`, `password_hash`, `name`, `avatar`, `phone`, `company`, `is_active`, `created_at`, `updated_at` | 一个用户有多张问卷 |
| `questionnaires` | `user_id`, `title`, `description`, `status`, `anonymous`, `one_response`, `show_result`, `public_code`, `public_url`, `published_at`, `closed_at`, 时间字段 | 属于一个用户；有题目、答卷、导出任务 |
| `questions` | `questionnaire_id`, `type`, `title`, `required`, `sort_order`, 时间字段 | 属于一张问卷；有多个选项 |
| `question_options` | `question_id`, `label`, `sort_order`, `created_at` | 属于一道题 |
| `responses` | `questionnaire_id`, `source`, `duration_seconds`, `is_valid`, `submitted_ip`, `user_agent`, `submitted_at` | 属于一张问卷；有多个答案 |
| `answers` | `response_id`, `question_id`, `content` | 一份答卷中的一道题答案 |
| `answer_options` | `answer_id`, `option_id` | 答案与题目选项的关联表 |
| `export_tasks` | 字符串 `id`（例如 `exp_20260831_001`）、`user_id`, `questionnaire_id`, `format`, `data_range`, 日期范围、进度、文件信息、错误信息、时间字段 | 属于用户和问卷 |
| `notification_settings` | `user_id`, `response_notice`, `expiration_notice`, `export_notice`, 时间字段 | 旧通知设置；当前产品不启用通知 UI/API |

## 重要说明

- 题型为 `single`、`multiple` 时才写入 `question_options`；`text`、`date`、`rating`、
  `number`、`phone` 的答案写入 `answers.content`。
- 选项关联名称是 `Answer.selected_options`，对应表 `answer_options`，不要改成
  `Answer.options`。
- `Base.metadata.create_all()` 只会创建缺少的表，不会修改你 Navicat 中已经存在的表。
  连接真实数据库前，建议在 Navicat 执行 `SHOW CREATE TABLE 表名`，如果某个字段类型或
  是否允许为空与你的实际定义不同，再把结果发给我进行最后一对一校准。

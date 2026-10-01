-- ============================================================
-- 在线表格智能问卷系统 - 比赛演示数据
-- 登录账号：demo@smartform.local
-- 登录密码：Demo@2026
-- 执行顺序：先执行 database/schema.sql，再执行本文件
-- 预期结果：3 份问卷、12 份答卷
-- 说明：本文件可重复执行，只会重建上述演示账号下的问卷数据
-- ============================================================

USE `online_form`;
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 1;

START TRANSACTION;

-- 1. 演示账号
INSERT INTO `users` (
    `email`, `password_hash`, `name`, `phone`, `company`,
    `is_active`, `created_at`, `updated_at`
) VALUES (
    'demo@smartform.local',
    '$2b$12$SptpL5pxFkn5fc3D8xuFyuGEXe2G1GDQfk21HoBwo2tM8SWh2Vldq',
    '智表演示管理员',
    '13800000000',
    '数智创新中心',
    1,
    DATE_SUB(NOW(), INTERVAL 60 DAY),
    NOW()
)
ON DUPLICATE KEY UPDATE
    `id` = LAST_INSERT_ID(`id`),
    `password_hash` = VALUES(`password_hash`),
    `name` = VALUES(`name`),
    `phone` = VALUES(`phone`),
    `company` = VALUES(`company`),
    `is_active` = 1,
    `updated_at` = NOW();

SET @demo_user_id = LAST_INSERT_ID();

INSERT INTO `notification_settings` (
    `user_id`, `response_notice`, `expiration_notice`, `export_notice`
) VALUES (@demo_user_id, 1, 1, 1)
ON DUPLICATE KEY UPDATE
    `response_notice` = 1,
    `expiration_notice` = 1,
    `export_notice` = 1;

DELETE FROM `questionnaires`
WHERE `user_id` = @demo_user_id;

-- 2. 主演示问卷
INSERT INTO `questionnaires` (
    `user_id`, `title`, `description`, `status`,
    `anonymous`, `one_response`, `show_result`,
    `public_code`, `public_url`,
    `published_at`, `created_at`, `updated_at`,
    `response_timeout_minutes`
) VALUES (
    @demo_user_id,
    '校园数字化服务满意度调查',
    '了解师生对校园数字化平台、数据分析和智能问卷服务的实际体验。',
    'active',
    0, 0, 1,
    'demo-campus-service-2026',
    'http://localhost:5173/s/demo-campus-service-2026',
    DATE_SUB(NOW(), INTERVAL 20 DAY),
    DATE_SUB(NOW(), INTERVAL 25 DAY),
    NOW(),
    30
);

SET @main_questionnaire_id = LAST_INSERT_ID();

INSERT INTO `questions`
(`questionnaire_id`, `type`, `title`, `required`, `sort_order`)
VALUES
(@main_questionnaire_id, 'single', '你对平台的整体使用体验是否满意？', 1, 1);
SET @q1 = LAST_INSERT_ID();

INSERT INTO `questions`
(`questionnaire_id`, `type`, `title`, `required`, `sort_order`)
VALUES
(@main_questionnaire_id, 'multiple', '你最关注平台的哪些能力？', 1, 2);
SET @q2 = LAST_INSERT_ID();

INSERT INTO `questions`
(`questionnaire_id`, `type`, `title`, `required`, `sort_order`)
VALUES
(@main_questionnaire_id, 'rating', '请为平台整体体验评分', 1, 3);
SET @q3 = LAST_INSERT_ID();

INSERT INTO `questions`
(`questionnaire_id`, `type`, `title`, `required`, `sort_order`)
VALUES
(@main_questionnaire_id, 'text', '你希望平台下一步优先改进什么？', 1, 4);
SET @q4 = LAST_INSERT_ID();

INSERT INTO `questions`
(`questionnaire_id`, `type`, `title`, `required`, `sort_order`)
VALUES
(@main_questionnaire_id, 'number', '你每周大约使用平台多少次？', 1, 5);
SET @q5 = LAST_INSERT_ID();

INSERT INTO `questions`
(`questionnaire_id`, `type`, `title`, `required`, `sort_order`)
VALUES
(@main_questionnaire_id, 'phone', '联系电话（选填）', 0, 6);
SET @q6 = LAST_INSERT_ID();

INSERT INTO `questions`
(`questionnaire_id`, `type`, `title`, `required`, `sort_order`)
VALUES
(@main_questionnaire_id, 'date', '最近一次使用平台的日期', 0, 7);
SET @q7 = LAST_INSERT_ID();

INSERT INTO `question_options`
(`question_id`, `label`, `sort_order`)
VALUES
(@q1, '非常满意', 1),
(@q1, '满意', 2),
(@q1, '一般', 3),
(@q1, '不满意', 4),
(@q2, '问卷创建与发布', 1),
(@q2, '统计分析', 2),
(@q2, 'AI 智能辅助', 3),
(@q2, '数据导出', 4),
(@q2, '移动端填写', 5);

-- 3. 十二份演示答卷
INSERT INTO `responses` (
    `questionnaire_id`, `respondent_name`, `respondent_email`,
    `source`, `duration_seconds`, `is_valid`,
    `submitted_ip`, `user_agent`, `submitted_at`,
    `risk_score`, `risk_reasons`, `review_status`
) VALUES
(@main_questionnaire_id, '体验用户01', 'demo01@smartform.local',
 'publicLink', 186, 1, '192.0.2.11', 'Demo Browser',
 DATE_SUB(NOW(), INTERVAL 2 HOUR), 5, JSON_ARRAY(), 'pending'),

(@main_questionnaire_id, '体验用户02', 'demo02@smartform.local',
 'qrCode', 215, 1, '192.0.2.12', 'Mobile Demo',
 DATE_SUB(NOW(), INTERVAL 5 HOUR), 8, JSON_ARRAY(), 'pending'),

(@main_questionnaire_id, '体验用户03', 'demo03@smartform.local',
 'wechat', 164, 1, '192.0.2.13', 'WeChat Demo',
 DATE_SUB(NOW(), INTERVAL 1 DAY), 10, JSON_ARRAY(), 'pending'),

(@main_questionnaire_id, '体验用户04', 'demo04@smartform.local',
 'publicLink', 12, 0, '192.0.2.14', 'Demo Browser',
 DATE_SUB(NOW(), INTERVAL 1 DAY), 72,
 JSON_ARRAY('填写时间过短', '答案规律性较高'), 'confirmed'),

(@main_questionnaire_id, '体验用户05', 'demo05@smartform.local',
 'qrCode', 198, 1, '192.0.2.15', 'Mobile Demo',
 DATE_SUB(NOW(), INTERVAL 2 DAY), 6, JSON_ARRAY(), 'pending'),

(@main_questionnaire_id, '体验用户06', 'demo06@smartform.local',
 'wechat', 243, 1, '192.0.2.16', 'WeChat Demo',
 DATE_SUB(NOW(), INTERVAL 3 DAY), 12, JSON_ARRAY(), 'pending'),

(@main_questionnaire_id, '体验用户07', 'demo07@smartform.local',
 'publicLink', 175, 1, '192.0.2.17', 'Demo Browser',
 DATE_SUB(NOW(), INTERVAL 3 DAY), 4, JSON_ARRAY(), 'pending'),

(@main_questionnaire_id, '体验用户08', 'demo08@smartform.local',
 'qrCode', 221, 1, '192.0.2.18', 'Mobile Demo',
 DATE_SUB(NOW(), INTERVAL 4 DAY), 7, JSON_ARRAY(), 'pending'),

(@main_questionnaire_id, '体验用户09', 'demo09@smartform.local',
 'publicLink', 39, 1, '192.0.2.19', 'Demo Browser',
 DATE_SUB(NOW(), INTERVAL 5 DAY), 48,
 JSON_ARRAY('填写速度较快'), 'pending'),

(@main_questionnaire_id, '体验用户10', 'demo10@smartform.local',
 'wechat', 207, 1, '192.0.2.20', 'WeChat Demo',
 DATE_SUB(NOW(), INTERVAL 6 DAY), 9, JSON_ARRAY(), 'pending'),

(@main_questionnaire_id, '体验用户11', 'demo11@smartform.local',
 'qrCode', 192, 1, '192.0.2.21', 'Mobile Demo',
 DATE_SUB(NOW(), INTERVAL 8 DAY), 3, JSON_ARRAY(), 'pending'),

(@main_questionnaire_id, '体验用户12', 'demo12@smartform.local',
 'publicLink', 231, 1, '192.0.2.22', 'Demo Browser',
 DATE_SUB(NOW(), INTERVAL 10 DAY), 5, JSON_ARRAY(), 'pending');

-- 4. 填写会话：12 次完成、3 次放弃
INSERT INTO `response_sessions` (
    `questionnaire_id`, `response_id`, `session_token`, `status`,
    `started_at`, `last_activity_at`, `expires_at`, `completed_at`
)
SELECT
    @main_questionnaire_id,
    r.id,
    CONCAT('demo-completed-', r.id),
    'completed',
    TIMESTAMPADD(SECOND, -r.duration_seconds, r.submitted_at),
    r.submitted_at,
    TIMESTAMPADD(
        MINUTE, 30,
        TIMESTAMPADD(SECOND, -r.duration_seconds, r.submitted_at)
    ),
    r.submitted_at
FROM `responses` r
WHERE r.questionnaire_id = @main_questionnaire_id;

INSERT INTO `response_sessions` (
    `questionnaire_id`, `session_token`, `status`,
    `started_at`, `last_activity_at`, `expires_at`
) VALUES
(@main_questionnaire_id, CONCAT('demo-expired-a-', @main_questionnaire_id),
 'expired', DATE_SUB(NOW(), INTERVAL 7 DAY),
 DATE_SUB(NOW(), INTERVAL 7 DAY), DATE_SUB(NOW(), INTERVAL 7 DAY)),
(@main_questionnaire_id, CONCAT('demo-expired-b-', @main_questionnaire_id),
 'expired', DATE_SUB(NOW(), INTERVAL 5 DAY),
 DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 5 DAY)),
(@main_questionnaire_id, CONCAT('demo-expired-c-', @main_questionnaire_id),
 'expired', DATE_SUB(NOW(), INTERVAL 2 DAY),
 DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY));

-- 5. 单选题答案
INSERT INTO `answers` (`response_id`, `question_id`, `content`)
SELECT r.id, @q1, NULL
FROM `responses` r
WHERE r.questionnaire_id = @main_questionnaire_id;

INSERT INTO `answer_options` (`answer_id`, `option_id`)
SELECT a.id, o.id
FROM `answers` a
JOIN `responses` r ON r.id = a.response_id
JOIN `question_options` o
  ON o.question_id = @q1
 AND o.sort_order =
    CASE
        WHEN CAST(SUBSTRING(r.respondent_email, 5, 2) AS UNSIGNED)
             IN (1, 2, 5, 7, 10) THEN 1
        WHEN CAST(SUBSTRING(r.respondent_email, 5, 2) AS UNSIGNED)
             IN (3, 6, 8, 11) THEN 2
        WHEN CAST(SUBSTRING(r.respondent_email, 5, 2) AS UNSIGNED)
             IN (9, 12) THEN 3
        ELSE 4
    END
WHERE a.question_id = @q1;

-- 6. 多选题答案
INSERT INTO `answers` (`response_id`, `question_id`, `content`)
SELECT r.id, @q2, NULL
FROM `responses` r
WHERE r.questionnaire_id = @main_questionnaire_id;

-- 所有人选择“问卷创建与发布”
INSERT INTO `answer_options` (`answer_id`, `option_id`)
SELECT a.id, o.id
FROM `answers` a
JOIN `question_options` o
  ON o.question_id = @q2 AND o.sort_order = 1
WHERE a.question_id = @q2;

-- 偶数编号选择“统计分析”
INSERT INTO `answer_options` (`answer_id`, `option_id`)
SELECT a.id, o.id
FROM `answers` a
JOIN `responses` r ON r.id = a.response_id
JOIN `question_options` o
  ON o.question_id = @q2 AND o.sort_order = 2
WHERE a.question_id = @q2
  AND MOD(CAST(SUBSTRING(r.respondent_email, 5, 2) AS UNSIGNED), 2) = 0;

-- 大多数用户选择“AI 智能辅助”
INSERT INTO `answer_options` (`answer_id`, `option_id`)
SELECT a.id, o.id
FROM `answers` a
JOIN `responses` r ON r.id = a.response_id
JOIN `question_options` o
  ON o.question_id = @q2 AND o.sort_order = 3
WHERE a.question_id = @q2
  AND MOD(CAST(SUBSTRING(r.respondent_email, 5, 2) AS UNSIGNED), 3) <> 0;

-- 部分用户选择“数据导出”
INSERT INTO `answer_options` (`answer_id`, `option_id`)
SELECT a.id, o.id
FROM `answers` a
JOIN `responses` r ON r.id = a.response_id
JOIN `question_options` o
  ON o.question_id = @q2 AND o.sort_order = 4
WHERE a.question_id = @q2
  AND MOD(CAST(SUBSTRING(r.respondent_email, 5, 2) AS UNSIGNED), 3) = 0;

-- 部分用户选择“移动端填写”
INSERT INTO `answer_options` (`answer_id`, `option_id`)
SELECT a.id, o.id
FROM `answers` a
JOIN `responses` r ON r.id = a.response_id
JOIN `question_options` o
  ON o.question_id = @q2 AND o.sort_order = 5
WHERE a.question_id = @q2
  AND MOD(CAST(SUBSTRING(r.respondent_email, 5, 2) AS UNSIGNED), 4) = 0;

-- 7. 评分、文本、数字、电话和日期答案
INSERT INTO `answers` (`response_id`, `question_id`, `content`)
SELECT
    r.id,
    @q3,
    CAST(
        CASE
            WHEN CAST(SUBSTRING(r.respondent_email, 5, 2) AS UNSIGNED)
                 IN (4, 9) THEN 3
            WHEN MOD(CAST(SUBSTRING(r.respondent_email, 5, 2) AS UNSIGNED), 3) = 0
                 THEN 4
            ELSE 5
        END AS CHAR
    )
FROM `responses` r
WHERE r.questionnaire_id = @main_questionnaire_id;

INSERT INTO `answers` (`response_id`, `question_id`, `content`)
SELECT
    r.id,
    @q4,
    CASE MOD(CAST(SUBSTRING(r.respondent_email, 5, 2) AS UNSIGNED), 6)
        WHEN 0 THEN '希望增加团队协作和成员权限管理功能。'
        WHEN 1 THEN '希望移动端填写页面加载速度更快。'
        WHEN 2 THEN '建议增加更多图表类型和分析维度。'
        WHEN 3 THEN '希望 AI 能根据历史问卷给出优化建议。'
        WHEN 4 THEN '建议增加群聊中直接分享问卷的功能。'
        ELSE '整体体验很好，希望增加更多问卷模板。'
    END
FROM `responses` r
WHERE r.questionnaire_id = @main_questionnaire_id;

INSERT INTO `answers` (`response_id`, `question_id`, `content`)
SELECT
    r.id,
    @q5,
    CAST(
        2 + MOD(CAST(SUBSTRING(r.respondent_email, 5, 2) AS UNSIGNED), 8)
        AS CHAR
    )
FROM `responses` r
WHERE r.questionnaire_id = @main_questionnaire_id;

INSERT INTO `answers` (`response_id`, `question_id`, `content`)
SELECT
    r.id,
    @q6,
    CONCAT(
        '1390000',
        LPAD(
            CAST(SUBSTRING(r.respondent_email, 5, 2) AS UNSIGNED),
            4,
            '0'
        )
    )
FROM `responses` r
WHERE r.questionnaire_id = @main_questionnaire_id
  AND CAST(SUBSTRING(r.respondent_email, 5, 2) AS UNSIGNED) <= 8;

INSERT INTO `answers` (`response_id`, `question_id`, `content`)
SELECT
    r.id,
    @q7,
    DATE_FORMAT(DATE(r.submitted_at), '%Y-%m-%d')
FROM `responses` r
WHERE r.questionnaire_id = @main_questionnaire_id;

-- 8. 用户提交反馈
INSERT INTO `user_feedback` (
    `questionnaire_id`, `response_id`, `rating`,
    `issue_type`, `content`, `created_at`
)
SELECT
    @main_questionnaire_id,
    r.id,
    CASE
        WHEN r.respondent_email IN (
            'demo01@smartform.local',
            'demo02@smartform.local',
            'demo05@smartform.local'
        ) THEN 5
        ELSE 4
    END,
    CASE
        WHEN r.respondent_email = 'demo04@smartform.local'
        THEN 'content'
        ELSE 'none'
    END,
    CASE
        WHEN r.respondent_email = 'demo04@smartform.local'
        THEN '部分题目说明可以再清晰一些。'
        ELSE '填写过程顺畅，页面简洁。'
    END,
    r.submitted_at
FROM `responses` r
WHERE r.questionnaire_id = @main_questionnaire_id
  AND CAST(SUBSTRING(r.respondent_email, 5, 2) AS UNSIGNED) <= 6;

-- 9. 草稿问卷
INSERT INTO `questionnaires` (
    `user_id`, `title`, `description`, `status`,
    `anonymous`, `one_response`, `show_result`,
    `created_at`, `updated_at`
) VALUES (
    @demo_user_id,
    '员工数字技能培训需求调研',
    '用于了解团队成员希望参加的培训主题和时间安排。',
    'draft',
    0, 1, 0,
    DATE_SUB(NOW(), INTERVAL 3 DAY),
    DATE_SUB(NOW(), INTERVAL 1 DAY)
);

SET @draft_questionnaire_id = LAST_INSERT_ID();

INSERT INTO `questions`
(`questionnaire_id`, `type`, `title`, `required`, `sort_order`)
VALUES
(@draft_questionnaire_id, 'single', '你最希望参加哪类培训？', 1, 1);
SET @draft_q1 = LAST_INSERT_ID();

INSERT INTO `question_options`
(`question_id`, `label`, `sort_order`)
VALUES
(@draft_q1, '数据分析', 1),
(@draft_q1, '人工智能应用', 2),
(@draft_q1, '项目管理', 3),
(@draft_q1, '团队协作', 4);

INSERT INTO `questions`
(`questionnaire_id`, `type`, `title`, `required`, `sort_order`)
VALUES
(@draft_questionnaire_id, 'text', '你对培训还有哪些建议？', 0, 2);

-- 10. 已结束问卷
INSERT INTO `questionnaires` (
    `user_id`, `title`, `description`, `status`,
    `anonymous`, `one_response`, `show_result`,
    `public_code`, `public_url`,
    `published_at`, `closed_at`,
    `created_at`, `updated_at`
) VALUES (
    @demo_user_id,
    '2026 春季产品体验活动报名',
    '活动报名已结束，该问卷用于演示历史问卷状态。',
    'closed',
    0, 1, 0,
    'demo-spring-event-2026',
    'http://localhost:5173/s/demo-spring-event-2026',
    DATE_SUB(NOW(), INTERVAL 40 DAY),
    DATE_SUB(NOW(), INTERVAL 15 DAY),
    DATE_SUB(NOW(), INTERVAL 45 DAY),
    DATE_SUB(NOW(), INTERVAL 15 DAY)
);

SET @closed_questionnaire_id = LAST_INSERT_ID();

INSERT INTO `questions`
(`questionnaire_id`, `type`, `title`, `required`, `sort_order`)
VALUES
(@closed_questionnaire_id, 'text', '姓名', 1, 1),
(@closed_questionnaire_id, 'phone', '联系电话', 1, 2),
(@closed_questionnaire_id, 'text', '报名备注', 0, 3);

COMMIT;

-- 11. 导入结果检查：应显示 3 份问卷、12 份答卷
SELECT
    u.id AS user_id,
    u.email,
    u.name,
    COUNT(DISTINCT q.id) AS questionnaire_count,
    COUNT(DISTINCT r.id) AS response_count
FROM `users` u
LEFT JOIN `questionnaires` q ON q.user_id = u.id
LEFT JOIN `responses` r ON r.questionnaire_id = q.id
WHERE u.id = @demo_user_id
GROUP BY u.id, u.email, u.name;

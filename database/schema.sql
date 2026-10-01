-- Online Form database schema for MySQL 8.0+
-- This file creates an empty database. It does not contain business data.

CREATE DATABASE IF NOT EXISTS `online_form`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `online_form`;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `answer_options`;
DROP TABLE IF EXISTS `answers`;
DROP TABLE IF EXISTS `response_sessions`;
DROP TABLE IF EXISTS `user_feedback`;
DROP TABLE IF EXISTS `export_tasks`;
DROP TABLE IF EXISTS `responses`;
DROP TABLE IF EXISTS `question_options`;
DROP TABLE IF EXISTS `questions`;
DROP TABLE IF EXISTS `questionnaires`;
DROP TABLE IF EXISTS `notification_settings`;
DROP TABLE IF EXISTS `users`;

CREATE TABLE `users` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT 'User ID',
  `email` varchar(320) NOT NULL COMMENT 'Login email',
  `password_hash` varchar(255) NOT NULL COMMENT 'Password hash',
  `name` varchar(100) NOT NULL COMMENT 'Display name',
  `avatar` varchar(500) DEFAULT NULL COMMENT 'Avatar URL',
  `phone` varchar(30) DEFAULT NULL COMMENT 'Phone number',
  `company` varchar(200) DEFAULT NULL COMMENT 'Organization',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT 'Whether the account is active',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_users_email` (`email`),
  KEY `idx_users_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Users';

CREATE TABLE `notification_settings` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `response_notice` tinyint(1) NOT NULL DEFAULT '1',
  `expiration_notice` tinyint(1) NOT NULL DEFAULT '1',
  `export_notice` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_notification_user` (`user_id`),
  CONSTRAINT `fk_notification_user`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Notification settings';

CREATE TABLE `questionnaires` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT 'Questionnaire ID',
  `user_id` bigint unsigned NOT NULL COMMENT 'Owner ID',
  `title` varchar(200) NOT NULL COMMENT 'Questionnaire title',
  `description` text COMMENT 'Questionnaire description',
  `status` enum('draft','active','closed') NOT NULL DEFAULT 'draft',
  `anonymous` tinyint(1) NOT NULL DEFAULT '1',
  `one_response` tinyint(1) NOT NULL DEFAULT '0',
  `show_result` tinyint(1) NOT NULL DEFAULT '0',
  `public_code` varchar(64) DEFAULT NULL,
  `public_url` varchar(500) DEFAULT NULL,
  `background_image` varchar(500) DEFAULT NULL COMMENT 'Public survey background image URL',
  `published_at` datetime DEFAULT NULL,
  `closed_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `response_timeout_minutes` int unsigned NOT NULL DEFAULT '30',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_questionnaires_public_code` (`public_code`),
  KEY `idx_questionnaires_user_status` (`user_id`,`status`),
  KEY `idx_questionnaires_updated_at` (`updated_at`),
  CONSTRAINT `fk_questionnaires_user`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Questionnaires';

CREATE TABLE `questions` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT 'Question ID',
  `questionnaire_id` bigint unsigned NOT NULL,
  `type` enum('single','multiple','text','date','rating','number','phone') NOT NULL,
  `title` varchar(500) NOT NULL,
  `required` tinyint(1) NOT NULL DEFAULT '0',
  `sort_order` int NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_questions_questionnaire_order` (`questionnaire_id`,`sort_order`),
  CONSTRAINT `fk_questions_questionnaire`
    FOREIGN KEY (`questionnaire_id`) REFERENCES `questionnaires` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Questions';

CREATE TABLE `question_options` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT 'Option ID',
  `question_id` bigint unsigned NOT NULL,
  `label` varchar(500) NOT NULL,
  `sort_order` int NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_question_options_question_order` (`question_id`,`sort_order`),
  CONSTRAINT `fk_question_options_question`
    FOREIGN KEY (`question_id`) REFERENCES `questions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Question options';

CREATE TABLE `responses` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT 'Response ID',
  `questionnaire_id` bigint unsigned NOT NULL,
  `respondent_name` varchar(100) DEFAULT NULL,
  `respondent_email` varchar(320) DEFAULT NULL,
  `source` enum('publicLink','wechat','qrCode') NOT NULL DEFAULT 'publicLink',
  `duration_seconds` int unsigned NOT NULL DEFAULT '0',
  `is_valid` tinyint(1) NOT NULL DEFAULT '1',
  `submitted_ip` varchar(45) DEFAULT NULL,
  `user_agent` varchar(500) DEFAULT NULL,
  `submitted_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `risk_score` int unsigned NOT NULL DEFAULT '0',
  `risk_reasons` json DEFAULT NULL,
  `review_status` varchar(20) NOT NULL DEFAULT 'pending',
  PRIMARY KEY (`id`),
  KEY `idx_responses_questionnaire_time` (`questionnaire_id`,`submitted_at`),
  KEY `idx_responses_source` (`source`),
  CONSTRAINT `fk_responses_questionnaire`
    FOREIGN KEY (`questionnaire_id`) REFERENCES `questionnaires` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Responses';

CREATE TABLE `response_sessions` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `questionnaire_id` bigint unsigned NOT NULL,
  `response_id` bigint unsigned DEFAULT NULL,
  `session_token` varchar(64) NOT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'in_progress',
  `started_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_activity_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `expires_at` datetime DEFAULT NULL,
  `completed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_response_sessions_token` (`session_token`),
  UNIQUE KEY `uk_response_sessions_response` (`response_id`),
  KEY `idx_session_questionnaire` (`questionnaire_id`),
  KEY `idx_session_status_activity` (`status`,`last_activity_at`),
  CONSTRAINT `fk_session_questionnaire`
    FOREIGN KEY (`questionnaire_id`) REFERENCES `questionnaires` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_session_response`
    FOREIGN KEY (`response_id`) REFERENCES `responses` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Response sessions';

CREATE TABLE `answers` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `response_id` bigint unsigned NOT NULL,
  `question_id` bigint unsigned NOT NULL,
  `content` text DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_answers_response_question` (`response_id`,`question_id`),
  KEY `idx_answers_question` (`question_id`),
  CONSTRAINT `fk_answers_response`
    FOREIGN KEY (`response_id`) REFERENCES `responses` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_answers_question`
    FOREIGN KEY (`question_id`) REFERENCES `questions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Answers';

CREATE TABLE `answer_options` (
  `answer_id` bigint unsigned NOT NULL,
  `option_id` bigint unsigned NOT NULL,
  PRIMARY KEY (`answer_id`,`option_id`),
  KEY `idx_answer_options_option` (`option_id`),
  CONSTRAINT `fk_answer_options_answer`
    FOREIGN KEY (`answer_id`) REFERENCES `answers` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_answer_options_option`
    FOREIGN KEY (`option_id`) REFERENCES `question_options` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Selected answer options';

CREATE TABLE `export_tasks` (
  `id` varchar(64) NOT NULL,
  `user_id` bigint unsigned NOT NULL,
  `questionnaire_id` bigint unsigned NOT NULL,
  `format` enum('xlsx','csv','json') NOT NULL,
  `data_range` enum('all','week','custom') NOT NULL DEFAULT 'all',
  `start_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  `include_metadata` tinyint(1) NOT NULL DEFAULT '1',
  `status` enum('pending','processing','completed','failed') NOT NULL DEFAULT 'pending',
  `progress` tinyint unsigned NOT NULL DEFAULT '0',
  `file_name` varchar(255) DEFAULT NULL,
  `file_path` varchar(500) DEFAULT NULL,
  `file_size` bigint unsigned DEFAULT NULL,
  `row_count` int unsigned DEFAULT NULL,
  `error_message` varchar(1000) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `completed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_export_tasks_user_created` (`user_id`,`created_at`),
  KEY `idx_export_tasks_questionnaire` (`questionnaire_id`),
  CONSTRAINT `fk_export_tasks_user`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_export_tasks_questionnaire`
    FOREIGN KEY (`questionnaire_id`) REFERENCES `questionnaires` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Export tasks';

CREATE TABLE `user_feedback` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `questionnaire_id` bigint unsigned NOT NULL,
  `response_id` bigint unsigned NOT NULL,
  `rating` tinyint unsigned NOT NULL,
  `issue_type` varchar(30) NOT NULL DEFAULT 'none',
  `content` varchar(500) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_feedback_response` (`response_id`),
  KEY `idx_user_feedback_questionnaire` (`questionnaire_id`),
  CONSTRAINT `fk_user_feedback_questionnaire`
    FOREIGN KEY (`questionnaire_id`) REFERENCES `questionnaires` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_user_feedback_response`
    FOREIGN KEY (`response_id`) REFERENCES `responses` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Submission feedback';

SET FOREIGN_KEY_CHECKS = 1;

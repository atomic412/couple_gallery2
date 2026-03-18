-- FILE CẤU TRÚC DATABASE DÀNH CHO MYSQL (couple_gallery_mysql.sql)
-- Chạy đoạn script này trong MySQL Workbench hoặc phpMyAdmin để tạo cơ sở dữ liệu.

CREATE DATABASE IF NOT EXISTS couple_gallery CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE couple_gallery;

-- 1. Bảng lưu trữ người dùng
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `username` VARCHAR(255) NOT NULL UNIQUE,
  `password_hash` VARCHAR(255) NOT NULL,
  `display_name` VARCHAR(255) NOT NULL,
  INDEX `ix_users_username` (`username`)
);

-- 2. Bảng lưu trữ ảnh (data lưu thẳng vào DB dạng BLOB)
CREATE TABLE IF NOT EXISTS `images` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `filename` VARCHAR(255),
  `content_type` VARCHAR(100) DEFAULT 'image/jpeg',
  `data` LONGBLOB,
  `uploader_id` INT NOT NULL,
  `upload_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`uploader_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
);

-- 3. Bảng lưu trữ lời nhắc nhở hằng ngày
CREATE TABLE IF NOT EXISTS `notes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `content` TEXT NOT NULL,
  `author_id` INT NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`author_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
);

-- 4. Danh sách 100 điều muốn làm cùng nhau
CREATE TABLE IF NOT EXISTS `bucket_items` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `title` VARCHAR(500) NOT NULL,
  `is_completed` TINYINT(1) DEFAULT 0
);

-- 5. Thư gửi tương lai (Time Capsule)
CREATE TABLE IF NOT EXISTS `time_capsules` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `content` TEXT NOT NULL,
  `author_id` INT NOT NULL,
  `unlock_date` DATETIME NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`author_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
);

-- 6. Điểm ghim Bản đồ Tình Yêu
CREATE TABLE IF NOT EXISTS `memory_markers` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `lat` VARCHAR(50),
  `lng` VARCHAR(50),
  `title` VARCHAR(255),
  `description` TEXT,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tự động thêm 2 tài khoản mặc định lúc ban đầu
-- Mật khẩu: 123456
INSERT IGNORE INTO `users` (`username`, `password_hash`, `display_name`) 
VALUES 
    ('bang', '123456', 'Trần Hải Bằng'),
    ('tuyet', '123456', 'Trần Thị Tuyết');

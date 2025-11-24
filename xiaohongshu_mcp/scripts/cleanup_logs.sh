#!/bin/bash
# 日志清理脚本
# 清理超过指定天数的日志文件

set -e

# 日志目录
LOG_DIR="${LOG_DIR:-/app/logs}"

# 保留天数（默认7天）
RETENTION_DAYS="${LOG_RETENTION_DAYS:-7}"

# 日志文件大小限制（MB，超过此大小的文件会被清理）
MAX_LOG_SIZE_MB="${MAX_LOG_SIZE_MB:-100}"

echo "=========================================="
echo "开始清理日志文件"
echo "日志目录: $LOG_DIR"
echo "保留天数: $RETENTION_DAYS 天"
echo "最大文件大小: $MAX_LOG_SIZE_MB MB"
echo "=========================================="

# 检查日志目录是否存在
if [ ! -d "$LOG_DIR" ]; then
    echo "警告: 日志目录不存在: $LOG_DIR"
    exit 0
fi

# 清理超过保留天数的文件
echo "清理超过 $RETENTION_DAYS 天的日志文件..."
find "$LOG_DIR" -type f -name "*.log" -mtime +$RETENTION_DAYS -delete
find "$LOG_DIR" -type f -name "*.log.*" -mtime +$RETENTION_DAYS -delete
find "$LOG_DIR" -type f -name "*.zip" -mtime +$RETENTION_DAYS -delete

# 清理超过大小限制的文件
echo "清理超过 $MAX_LOG_SIZE_MB MB 的日志文件..."
find "$LOG_DIR" -type f -name "*.log" -size +${MAX_LOG_SIZE_MB}M -delete
find "$LOG_DIR" -type f -name "*.log.*" -size +${MAX_LOG_SIZE_MB}M -delete

# 统计清理后的文件
LOG_COUNT=$(find "$LOG_DIR" -type f \( -name "*.log" -o -name "*.log.*" -o -name "*.zip" \) | wc -l)
LOG_SIZE=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1)

echo "=========================================="
echo "日志清理完成"
echo "剩余日志文件数: $LOG_COUNT"
echo "日志目录总大小: $LOG_SIZE"
echo "=========================================="


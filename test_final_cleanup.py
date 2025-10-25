#!/usr/bin/env python3
"""
最终测试脚本：验证Cookie清理功能是否正常工作
"""

import asyncio
import os
from pathlib import Path
from loguru import logger

from src.xiaohongshu_mcp_python.main import get_user_session_manager

async def test_final_cleanup():
    """测试最终的清理功能"""
    logger.info("开始最终清理测试")
    
    # 获取用户会话管理器
    user_session_manager = get_user_session_manager()
    
    # 1. 创建一个会话（这会启动浏览器并可能创建Cookie）
    logger.info("步骤1: 创建会话")
    session = await user_session_manager.get_or_create_session("test_user", headless=True, fresh=False)
    logger.info(f"创建的会话ID: {session}")
    
    # 等待浏览器启动
    await asyncio.sleep(3)
    
    # 2. 检查清理前的Cookie状态
    cookies_file = Path("cookies.json")
    if cookies_file.exists():
        size_before = cookies_file.stat().st_size
        logger.info(f"清理前 cookies.json 大小: {size_before} 字节")
    else:
        size_before = 0
        logger.info("清理前 cookies.json 不存在")
    
    # 3. 清理会话
    logger.info("步骤2: 清理会话")
    success = await user_session_manager.cleanup_user_session("test_user")
    logger.info(f"清理结果: {success}")
    
    # 等待清理完成
    await asyncio.sleep(2)
    
    # 4. 检查清理后的Cookie状态
    if cookies_file.exists():
        size_after = cookies_file.stat().st_size
        logger.info(f"清理后 cookies.json 大小: {size_after} 字节")
        
        if size_after == 0:
            logger.success("✅ Cookie文件已清空")
        elif size_after < size_before:
            logger.warning(f"⚠️ Cookie文件大小减少了 {size_before - size_after} 字节，但未完全清空")
        else:
            logger.error(f"❌ Cookie文件大小未变化或增加了")
    else:
        logger.success("✅ Cookie文件已删除")
    
    # 5. 测试fresh模式会话创建（不应该重新访问网站）
    logger.info("步骤3: 测试fresh模式会话创建")
    fresh_session = await user_session_manager.get_or_create_session("test_user2", headless=True, fresh=True)
    logger.info(f"Fresh模式会话ID: {fresh_session}")
    
    # 等待初始化完成
    await asyncio.sleep(3)
    
    # 6. 检查fresh模式后的Cookie状态
    if cookies_file.exists():
        size_fresh = cookies_file.stat().st_size
        logger.info(f"Fresh模式后 cookies.json 大小: {size_fresh} 字节")
        
        if size_fresh == 0:
            logger.success("✅ Fresh模式下Cookie文件保持为空")
        else:
            logger.error(f"❌ Fresh模式下Cookie文件被重新创建，大小: {size_fresh} 字节")
    else:
        logger.success("✅ Fresh模式下Cookie文件保持不存在")
    
    # 7. 最终清理
    logger.info("步骤4: 最终清理")
    await user_session_manager.cleanup_user_session("test_user2")
    
    logger.info("测试完成")

if __name__ == "__main__":
    asyncio.run(test_final_cleanup())
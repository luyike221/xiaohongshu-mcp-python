#!/usr/bin/env python3
"""
测试浏览器彻底清除数据功能
"""

import asyncio
import os
from pathlib import Path
from loguru import logger

from src.xiaohongshu_mcp_python.main import get_user_session_manager

async def test_clear_all_data():
    """测试浏览器彻底清除数据功能"""
    logger.info("开始测试浏览器彻底清除数据功能")
    
    # 获取用户会话管理器
    user_session_manager = get_user_session_manager()
    
    # 1. 创建一个会话（这会启动浏览器并可能创建Cookie和其他数据）
    logger.info("步骤1: 创建会话并访问网站")
    session = await user_session_manager.get_or_create_session("test_clear_user", headless=True, fresh=False)
    logger.info(f"创建的会话ID: {session}")
    
    # 等待浏览器启动和初始化
    await asyncio.sleep(5)
    
    # 2. 检查清理前的状态
    cookies_file = Path("cookies.json")
    if cookies_file.exists():
        with open(cookies_file, 'r') as f:
            content_before = f.read()
        size_before = cookies_file.stat().st_size
        logger.info(f"清理前 cookies.json 大小: {size_before} 字节")
        logger.info(f"清理前 cookies.json 内容预览: {content_before[:200]}...")
    else:
        size_before = 0
        content_before = ""
        logger.info("清理前 cookies.json 不存在")
    
    # 3. 使用新的彻底清理方法
    logger.info("步骤2: 使用彻底清理方法清理会话")
    success = await user_session_manager.cleanup_user_session("test_clear_user")
    logger.info(f"清理结果: {success}")
    
    # 等待清理完成
    await asyncio.sleep(3)
    
    # 4. 检查清理后的状态
    if cookies_file.exists():
        with open(cookies_file, 'r') as f:
            content_after = f.read()
        size_after = cookies_file.stat().st_size
        logger.info(f"清理后 cookies.json 大小: {size_after} 字节")
        logger.info(f"清理后 cookies.json 内容: {content_after}")
        
        if size_after == 0 or content_after.strip() == "[]":
            logger.success("✅ Cookie文件已彻底清空")
        elif size_after < size_before:
            logger.warning(f"⚠️ Cookie文件大小减少了 {size_before - size_after} 字节，但可能未完全清空")
        else:
            logger.error(f"❌ Cookie文件大小未变化或增加了")
    else:
        logger.success("✅ Cookie文件已删除")
    
    # 5. 测试创建新会话时是否还会重新访问网站
    logger.info("步骤3: 测试创建新会话（非fresh模式）")
    new_session = await user_session_manager.get_or_create_session("test_clear_user2", headless=True, fresh=False)
    logger.info(f"新会话ID: {new_session}")
    
    # 等待初始化完成
    await asyncio.sleep(5)
    
    # 6. 检查新会话后的Cookie状态
    if cookies_file.exists():
        with open(cookies_file, 'r') as f:
            content_new = f.read()
        size_new = cookies_file.stat().st_size
        logger.info(f"新会话后 cookies.json 大小: {size_new} 字节")
        logger.info(f"新会话后 cookies.json 内容预览: {content_new[:200]}...")
        
        if size_new > 0 and content_new.strip() != "[]":
            logger.info("ℹ️ 新会话创建了新的Cookie（这是正常的）")
        else:
            logger.info("ℹ️ 新会话未创建Cookie")
    else:
        logger.info("ℹ️ 新会话后Cookie文件仍不存在")
    
    # 7. 最终清理
    logger.info("步骤4: 最终清理")
    await user_session_manager.cleanup_user_session("test_clear_user2")
    
    # 8. 验证最终状态
    await asyncio.sleep(2)
    if cookies_file.exists():
        with open(cookies_file, 'r') as f:
            final_content = f.read()
        final_size = cookies_file.stat().st_size
        logger.info(f"最终 cookies.json 大小: {final_size} 字节")
        logger.info(f"最终 cookies.json 内容: {final_content}")
        
        if final_size == 0 or final_content.strip() == "[]":
            logger.success("✅ 最终清理成功，Cookie文件已彻底清空")
        else:
            logger.error("❌ 最终清理后Cookie文件仍有内容")
    else:
        logger.success("✅ 最终清理成功，Cookie文件已删除")
    
    logger.info("测试完成")

if __name__ == "__main__":
    asyncio.run(test_clear_all_data())
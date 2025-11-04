"""
反爬虫策略工具类
提供统一的反爬虫策略和人类行为模拟
"""

import asyncio
import random
from typing import Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from loguru import logger


class AntiBotStrategy:
    """反爬虫策略工具类"""
    
    @staticmethod
    async def add_random_delay(base_delay: float = 1.0, max_extra: int = 3, seed: Optional[str] = None) -> None:
        """
        添加随机延迟，模拟人类行为
        
        Args:
            base_delay: 基础延迟时间（秒）
            max_extra: 最大额外延迟时间（秒）
            seed: 用于生成随机数的种子
        """
        if seed:
            extra_delay = hash(seed) % max_extra
        else:
            extra_delay = random.randint(0, max_extra - 1)
        
        delay = base_delay + extra_delay
        logger.debug(f"添加随机延迟: {delay}秒")
        await asyncio.sleep(delay)
    
    @staticmethod
    async def simulate_human_navigation(page: Page, url: str, timeout: int = 60000) -> None:
        """
        模拟人类导航行为
        
        Args:
            page: Playwright页面对象
            url: 目标URL
            timeout: 超时时间（毫秒）
        """
        logger.debug(f"模拟人类导航到: {url}")
        
        # 使用更自然的等待策略
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        
        # 等待页面稳定
        await asyncio.sleep(2)
        
        # 模拟滚动行为
        await AntiBotStrategy.simulate_scroll_behavior(page)
        
        # 等待网络空闲
        try:
            await page.wait_for_load_state("networkidle", timeout=30000)
        except PlaywrightTimeoutError:
            logger.warning("等待网络空闲超时，继续执行")
    
    @staticmethod
    async def simulate_scroll_behavior(page: Page, scroll_distance: int = 100) -> None:
        """
        模拟人类滚动行为
        
        Args:
            page: Playwright页面对象
            scroll_distance: 滚动距离
        """
        logger.debug("模拟滚动行为")
        
        # 向下滚动一点
        await page.evaluate(f"window.scrollTo(0, {scroll_distance})")
        await asyncio.sleep(0.5)
        
        # 滚回顶部
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(0.3)
    
    @staticmethod
    async def simulate_natural_scrolling(page: Page, scroll_count: int = 3) -> None:
        """
        模拟自然的分步滚动行为
        
        Args:
            page: Playwright页面对象
            scroll_count: 滚动步数
        """
        logger.debug(f"模拟自然滚动，步数: {scroll_count}")
        
        try:
            current_height = await page.evaluate("document.body.scrollHeight")
            scroll_step = current_height // (scroll_count + 1)
            
            for i in range(scroll_count):
                # 添加随机延迟
                await asyncio.sleep(0.5 + random.random())
                
                # 滚动到指定位置
                scroll_position = scroll_step * (i + 1)
                await page.evaluate(f"window.scrollTo(0, {scroll_position})")
                
                # 短暂停留
                await asyncio.sleep(0.3)
            
            # 最后滚动到底部
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
        except Exception as e:
            logger.warning(f"模拟自然滚动失败: {e}")
    
    @staticmethod
    async def wait_for_page_stable(page: Page, timeout: int = 10000) -> None:
        """
        等待页面稳定
        
        Args:
            page: Playwright页面对象
            timeout: 超时时间（毫秒）
        """
        try:
            await page.wait_for_load_state("networkidle", timeout=timeout)
        except PlaywrightTimeoutError:
            logger.warning("等待页面稳定超时，继续执行")
    
    @staticmethod
    async def extract_initial_state_safely(page: Page) -> str:
        """
        安全地提取__INITIAL_STATE__数据，参考search.py的成功实现
        
        Args:
            page: Playwright页面对象
            
        Returns:
            序列化后的状态数据
        """
        logger.debug("安全提取__INITIAL_STATE__数据")
        
        # 等待__INITIAL_STATE__加载完成
        await page.wait_for_function("() => window.__INITIAL_STATE__ !== undefined", timeout=30000)
        
        # 使用与search.py相同的方法提取数据
        initial_state_js = """
        () => {
            if (window.__INITIAL_STATE__) {
                // 安全地序列化，避免循环引用
                try {
                    return JSON.stringify(window.__INITIAL_STATE__, (key, value) => {
                        // 跳过可能导致循环引用的属性
                        if (key === 'dep' || key === 'computed' || typeof value === 'function') {
                            return undefined;
                        }
                        return value;
                    });
                } catch (e) {
                    console.log('JSON序列化失败，尝试提取关键部分:', e.message);
                    // 如果还是有问题，尝试提取我们需要的部分
                    const state = window.__INITIAL_STATE__;
                    const result = {};
                    
                    // 提取用户相关数据
                    if (state.user) {
                        result.user = {};
                        if (state.user.userPageData) {
                            result.user.userPageData = state.user.userPageData;
                        }
                        if (state.user.notes) {
                            result.user.notes = {};
                            if (state.user.notes._rawValue) {
                                result.user.notes._rawValue = state.user.notes._rawValue;
                            }
                        }
                    }
                    
                    // 提取笔记相关数据
                    if (state.note) {
                        result.note = state.note;
                    }
                    
                    // 提取评论数据
                    if (state.comments) {
                        result.comments = state.comments;
                    }
                    
                    // 提取feed数据
                    if (state.feed) {
                        result.feed = state.feed;
                    }
                    
                    // 提取搜索相关数据
                    if (state.Main && state.Main.feedData) {
                        result.Main = {
                            feedData: state.Main.feedData
                        };
                    }
                    
                    try {
                        return JSON.stringify(result);
                    } catch (e2) {
                        console.log('备用方案也失败:', e2.message);
                        return "{}";
                    }
                }
            }
            return "";
        }
        """
        
        result = await page.evaluate(initial_state_js)
        return result
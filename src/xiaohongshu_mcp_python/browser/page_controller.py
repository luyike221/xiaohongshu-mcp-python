"""
页面控制器

提供页面操作的高级封装，包括导航、元素查找、等待等功能。
"""

import asyncio
from typing import Optional, Union, List, Dict, Any
from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError
from loguru import logger


class PageController:
    """页面控制器"""
    
    def __init__(self, page: Page):
        """
        初始化页面控制器
        
        Args:
            page: Playwright 页面实例
        """
        self.page = page
        self.default_timeout = 30000  # 30秒
    
    async def navigate(self, url: str, wait_until: str = "domcontentloaded") -> None:
        """
        导航到指定URL
        
        Args:
            url: 目标URL
            wait_until: 等待条件
        """
        logger.info(f"导航到: {url}")
        try:
            # 检查页面是否仍然有效
            if self.page.is_closed():
                logger.error("页面已关闭，无法导航")
                raise Exception("页面已关闭，需要重新初始化浏览器")
            
            await self.page.goto(url, wait_until=wait_until, timeout=self.default_timeout)
            logger.info("页面加载完成")
        except PlaywrightTimeoutError:
            logger.error(f"导航超时: {url}")
            raise
        except Exception as e:
            error_msg = str(e)
            if "Target page, context or browser has been closed" in error_msg or "page.is_closed" in error_msg:
                logger.error("浏览器或页面已关闭，需要重新初始化")
                raise Exception("浏览器已关闭，需要重新初始化")
            logger.error(f"导航失败: {e}")
            raise
    
    def is_page_valid(self) -> bool:
        """检查页面是否仍然有效"""
        try:
            return not self.page.is_closed()
        except Exception:
            return False
    
    async def wait_for_element(
        self, 
        selector: str, 
        timeout: Optional[int] = None,
        state: str = "visible"
    ) -> Locator:
        """
        等待元素出现
        
        Args:
            selector: CSS选择器
            timeout: 超时时间（毫秒）
            state: 元素状态 (visible, hidden, attached, detached)
        
        Returns:
            元素定位器
        """
        timeout = timeout or self.default_timeout
        logger.debug(f"等待元素: {selector} (state={state})")
        
        try:
            locator = self.page.locator(selector)
            await locator.wait_for(state=state, timeout=timeout)
            return locator
        except PlaywrightTimeoutError:
            logger.error(f"等待元素超时: {selector}")
            raise
    
    async def has_element(self, selector: str, timeout: int = 5000) -> bool:
        """
        检查元素是否存在
        
        Args:
            selector: CSS选择器
            timeout: 超时时间（毫秒）
        
        Returns:
            元素是否存在
        """
        try:
            await self.wait_for_element(selector, timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            return False
    
    async def click_element(
        self, 
        selector: str, 
        timeout: Optional[int] = None,
        force: bool = False
    ) -> None:
        """
        点击元素
        
        Args:
            selector: CSS选择器
            timeout: 超时时间（毫秒）
            force: 是否强制点击
        """
        logger.debug(f"点击元素: {selector}")
        locator = await self.wait_for_element(selector, timeout)
        await locator.click(force=force)
    
    async def input_text(
        self, 
        selector: str, 
        text: str, 
        timeout: Optional[int] = None,
        clear: bool = True
    ) -> None:
        """
        输入文本
        
        Args:
            selector: CSS选择器
            text: 输入的文本
            timeout: 超时时间（毫秒）
            clear: 是否先清空输入框
        """
        logger.debug(f"输入文本到: {selector}")
        locator = await self.wait_for_element(selector, timeout)
        
        if clear:
            await locator.clear()
        
        await locator.fill(text)
    
    async def get_text(self, selector: str, timeout: Optional[int] = None) -> str:
        """
        获取元素文本
        
        Args:
            selector: CSS选择器
            timeout: 超时时间（毫秒）
        
        Returns:
            元素文本内容
        """
        locator = await self.wait_for_element(selector, timeout)
        return await locator.text_content() or ""
    
    async def get_attribute(
        self, 
        selector: str, 
        attribute: str, 
        timeout: Optional[int] = None
    ) -> Optional[str]:
        """
        获取元素属性
        
        Args:
            selector: CSS选择器
            attribute: 属性名
            timeout: 超时时间（毫秒）
        
        Returns:
            属性值
        """
        locator = await self.wait_for_element(selector, timeout)
        return await locator.get_attribute(attribute)
    
    async def wait_for_stable(self, timeout: int = 5000) -> None:
        """
        等待页面稳定
        
        Args:
            timeout: 超时时间（毫秒）
        """
        logger.debug("等待页面稳定")
        try:
            # 首先等待网络空闲
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
            logger.debug("页面网络空闲状态达成")
        except PlaywrightTimeoutError:
            logger.warning("等待页面网络空闲超时，尝试其他等待策略")
            try:
                # 如果网络空闲失败，尝试等待DOM内容加载完成
                await self.page.wait_for_load_state("domcontentloaded", timeout=min(timeout, 5000))
                logger.debug("页面DOM内容加载完成")
                
                # 额外等待一小段时间让页面渲染完成
                await asyncio.sleep(1)
                logger.debug("页面额外等待完成")
            except PlaywrightTimeoutError:
                logger.warning("所有页面稳定性等待策略都超时")
                # 不抛出异常，让调用方决定如何处理
    
    async def scroll_to_element(self, selector: str, timeout: Optional[int] = None) -> None:
        """
        滚动到元素位置
        
        Args:
            selector: CSS选择器
            timeout: 超时时间（毫秒）
        """
        locator = await self.wait_for_element(selector, timeout)
        await locator.scroll_into_view_if_needed()
    
    async def take_screenshot(self, path: Optional[str] = None) -> bytes:
        """
        截图
        
        Args:
            path: 保存路径（可选）
        
        Returns:
            截图数据
        """
        logger.debug(f"截图: {path or '内存'}")
        return await self.page.screenshot(path=path, full_page=True)
    
    async def evaluate_script(self, script: str) -> Any:
        """
        执行JavaScript脚本
        
        Args:
            script: JavaScript代码
        
        Returns:
            脚本执行结果
        """
        logger.debug(f"执行脚本: {script[:100]}...")
        return await self.page.evaluate(script)
    
    async def wait_for_navigation(self, timeout: Optional[int] = None) -> None:
        """
        等待页面导航完成
        
        Args:
            timeout: 超时时间（毫秒）
        """
        timeout = timeout or self.default_timeout
        logger.debug("等待页面导航")
        
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
        except PlaywrightTimeoutError:
            logger.error("等待页面导航超时")
            raise
    
    async def get_cookies(self) -> List[Dict[str, Any]]:
        """
        获取当前页面的cookies
        
        Returns:
            Cookie列表
        """
        context = self.page.context
        return await context.cookies()
    
    async def set_cookies(self, cookies: List[Dict[str, Any]]) -> None:
        """
        设置cookies
        
        Args:
            cookies: Cookie列表
        """
        context = self.page.context
        await context.add_cookies(cookies)
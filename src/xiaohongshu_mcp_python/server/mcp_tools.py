"""
MCP 工具函数模块
包含所有 MCP 工具接口的实现
"""

from typing import Optional, Union, List
from loguru import logger
from fastmcp import Context, FastMCP

from ..services.service import XiaohongshuService
from ..config import PublishImageContent, PublishVideoContent, settings
from ..browser import BrowserManager
from ..storage.cookie_storage import CookieStorage
from ..managers.user_session_manager import get_user_session_manager
from ..utils.auth_helpers import check_user_login_status


# 创建 FastMCP 实例（需要在导入时创建，以便工具函数可以注册）
mcp = FastMCP("xiaohongshu-mcp-server")


def normalize_tags(tags: Optional[List[str]]) -> List[str]:
    """
    规范化标签参数
    
    只接受数组格式，清理每个标签：
    - None -> []
    - [] -> []
    - ["美食", "旅行"] -> ["美食", "旅行"]
    - ["#美食", "#旅行"] -> ["美食", "旅行"] (自动移除 # 号)
    
    Args:
        tags: 标签数组，每个元素是一个标签字符串
        
    Returns:
        规范化后的标签列表
    """
    if tags is None:
        return []
    
    if not isinstance(tags, list):
        logger.warning(f"tags 参数必须是数组类型，收到: {type(tags)}")
        return []
    
    # 清理标签：移除 # 号前缀和前后空格
    normalized_tags = []
    for tag in tags:
        if not isinstance(tag, str):
            tag = str(tag)
        
        tag = tag.strip()
        if tag:
            # 移除 # 号前缀（如果存在）
            if tag.startswith("#"):
                tag = tag[1:].strip()
            # 只添加非空标签
            if tag:
                normalized_tags.append(tag)
    
    return normalized_tags

@mcp.tool
async def xiaohongshu_debug_init_browser(
    username: Optional[str] = None
) -> dict:
    """
    调试接口：加载cookie并进入小红书主页
    
    功能：
    1. 加载已保存的cookie
    2. 启动浏览器（如果未启动）
    3. 导航到小红书主页
    4. 返回操作结果
    
    Args:
        username: 用户名（可选，如果不提供则使用全局用户）
        
    Returns:
        包含操作结果的字典
    """
    try:
        current_user = username or settings.GLOBAL_USER
        logger.info(f"调试接口：为用户 {current_user} 初始化浏览器并进入主页")
        
        # 创建浏览器管理器，使用用户的cookie存储
        user_cookie_storage = CookieStorage(f"cookies_{current_user}.json")
        browser_manager = BrowserManager(cookie_storage=user_cookie_storage)
        
        # 确保浏览器已启动
        if not browser_manager.is_started():
            logger.info("浏览器未启动，正在启动...")
            await browser_manager.start()
        else:
            # 如果已启动，重新加载cookie
            logger.info("浏览器已启动，重新加载cookie...")
            await browser_manager.load_cookies()
        
        # 获取页面
        page = await browser_manager.get_page()
        
        # 导航到小红书主页
        homepage_url = "https://www.xiaohongshu.com/explore"
        logger.info(f"正在导航到小红书主页: {homepage_url}")
        await page.goto(homepage_url)
        logger.info(f"成功进入小红书主页")
        
        # 注意：这里不关闭浏览器，保持浏览器运行状态以便调试
        # 如果需要关闭，可以调用 await browser_manager.stop()
        
        return {
            "success": True,
            "status": "success",
            "username": current_user,
            "message": "已成功加载cookie并进入小红书主页"
        }
        
    except Exception as e:
        logger.error(f"调试接口执行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "message": f"调试接口执行失败: {str(e)}"
        }



@mcp.tool
async def xiaohongshu_start_login_session(headless: bool = False, fresh: bool = False, username: Optional[str] = None) -> dict:
    """
    启动小红书登录会话（基于本地 cookies）
    
    Args:
        headless: 是否使用无头模式，默认False（显示浏览器界面）
        fresh: 是否强制创建新会话，默认False（复用现有 cookies）
        username: 用户名，如果不提供则使用全局用户
        
    Returns:
        包含会话ID和状态的字典
    """
    try:
        # 使用提供的用户名或全局用户名（从 settings 读取最新值）
        current_user = username or settings.GLOBAL_USER
        logger.info(f"为用户 {current_user} 启动登录会话，headless={headless}, fresh={fresh}")
        
        user_session_manager = get_user_session_manager()
        
        if fresh:
            # 强制创建新会话，先清理现有 cookies 和会话
            logger.info(f"fresh=True，清理用户 {current_user} 的现有 cookies 和会话")
            await user_session_manager.cleanup_user_session(current_user)
        
        # 获取或创建用户会话（阻塞等待登录完成）
        # 如果本地 cookies 有效，会直接返回已登录状态
        # 如果 headless 未指定，使用 settings 中的配置
        effective_headless = headless if headless is not None else settings.BROWSER_HEADLESS
        result = await user_session_manager.get_or_create_session(
            username=current_user,
            headless=effective_headless,
            wait_for_completion=True  # 阻塞等待登录完成
        )
        
        if "error" in result:
            return {
                "success": False,
                "error": result["error"],
                "message": f"为用户 {current_user} 创建会话失败"
            }
        
        session_id = result["session_id"]
        status = result["status"]
        is_new_session = result.get("is_new", False)
        cookies_saved = result.get("cookies_saved", False)
        
        # 根据登录状态返回结果
        if status == "logged_in":
            if is_new_session:
                message = result.get("message", "登录成功")
            else:
                message = f"使用本地 cookies，用户已登录（无需重新登录）"
            
            return {
                "success": True,
                "session_id": session_id,
                "status": "logged_in",
                "username": current_user,
                "is_new_session": is_new_session,
                "message": message,
                "cookies_saved": cookies_saved
            }
        elif status == "failed":
            return {
                "success": False,
                "session_id": session_id,
                "status": "failed",
                "username": current_user,
                "error": result.get("message", "登录失败"),
                "message": f"登录失败: {result.get('message', '未知错误')}"
            }
        else:
            # 其他状态（如 waiting, initializing）
            return {
                "success": True,
                "session_id": session_id,
                "status": status,
                "username": current_user,
                "is_new_session": is_new_session,
                "message": result.get("message", f"会话状态: {status}")
            }
        
    except Exception as e:
        logger.error(f"启动登录会话失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "启动登录会话失败"
        }


@mcp.tool
async def xiaohongshu_check_login_session(username: Optional[str] = None) -> dict:
    """
    检查登录会话状态（基于本地 cookies）
    
    Args:
        username: 用户名（可选，如果不提供则使用全局用户）
        
    Returns:
        包含登录状态信息的字典
    """
    try:
        user_session_manager = get_user_session_manager()
        current_user = username or settings.GLOBAL_USER
        
        # 检查本地 cookies 状态
        user_session_status = await user_session_manager.get_user_session_status(current_user)
        
        if not user_session_status:
            return {
                "success": False,
                "status": "no_session",
                "username": current_user,
                "message": f"用户 {current_user} 没有本地 cookies，请先登录",
                "logged_in": False
            }
        
        # 检查是否登录失效
        if user_session_status.get("status") == "expired" or user_session_status.get("error") == "LOGIN_EXPIRED":
            return {
                "success": False,
                "status": "expired",
                "username": current_user,
                "message": f"用户 {current_user} 的登录已失效，请重新登录",
                "logged_in": False,
                "error": "LOGIN_EXPIRED"
            }
        
        # 返回登录状态
        status = user_session_status.get("status", "unknown")
        logged_in = user_session_status.get("logged_in", False)
        
        return {
            "success": True,
            "username": current_user,
            "status": status,
            "message": user_session_status.get("message", f"用户 {current_user} 的登录状态: {status}"),
            "logged_in": logged_in,
            "cookies_saved": user_session_status.get("cookies_saved", False)
        }
        
    except Exception as e:
        logger.error(f"检查登录会话失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "检查登录会话失败"
        }


@mcp.tool
async def xiaohongshu_cleanup_login_session(username: Optional[str] = None) -> dict:
    """
    清理登录会话（基于用户名）
    
    Args:
        username: 用户名（可选，如果不提供则使用全局用户）
        
    Returns:
        清理结果
    """
    try:
        user_session_manager = get_user_session_manager()
        current_user = username or settings.GLOBAL_USER
        success = await user_session_manager.cleanup_user_session(current_user)
        
        return {
            "success": success,
            "username": current_user,
            "message": f"用户 {current_user} 的会话已清理" if success else f"清理用户 {current_user} 的会话失败"
        }
        
    except Exception as e:
        logger.error(f"清理登录会话失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "清理登录会话失败"
        }


@mcp.tool
async def xiaohongshu_publish_content(
    title: str,
    content: str,
    images: Optional[list[str]],
    tags: Optional[list[str]] ,
    username: Optional[str] = None,
    context: Optional[Context] = None
) -> dict:
    """
    发布小红书图文内容
    
    Args:
        title: 内容标题（最多20个中文字或英文单词）
        content: 正文内容，不包含以#开头的标签内容
        images: 图片路径数组，默认 []。支持HTTP/HTTPS图片链接或本地图片绝对路径（至少需要1张图片）
        tags: 话题标签数组，默认 []。如 ["美食", "旅行", "生活"]，标签中的 # 号会自动移除
        username: 用户名（可选，如果不提供则使用全局用户）
        
    Returns:
        发布结果
    """
    try:
        # 处理默认值
        if images is None:
            images = []
        if tags is None:
            tags = []
        
        # 记录接收到的参数（用于调试）
        logger.info(f"收到发布请求 - title: {title}, content长度: {len(content)}, images数量: {len(images)}, tags: {tags} (类型: {type(tags)})")
        
        current_user = username or settings.GLOBAL_USER
        
        # 发送进度通知：开始检查登录状态
        if context:
            await context.report_progress(
                progress=10,
                total=100
            )
        
        # 检查用户登录状态（基于本地 cookies）
        login_check = await check_user_login_status(current_user)
        if not login_check.get("valid", False):
            return login_check
        
        # 发送进度通知：开始启动浏览器
        if context:
            await context.report_progress(
                progress=20,
                total=100
            )
        
        # 创建浏览器管理器，使用用户的cookie存储
        user_cookie_storage = CookieStorage(f"cookies_{current_user}.json")
        browser_manager = BrowserManager(cookie_storage=user_cookie_storage)
        await browser_manager.start()
        
        # 加载用户的cookies
        await browser_manager.load_cookies()
        logger.info(f"已为用户 {current_user} 加载cookies")
        
        try:
            service = XiaohongshuService(browser_manager)
            
            # 发送进度通知：开始发布内容
            if context:
                await context.report_progress(
                    progress=40,
                    total=100
                )
            
            # 规范化标签参数
            normalized_tags = normalize_tags(tags)
            logger.info(f"规范化后的标签: {normalized_tags}")
            
            # 构建发布请求
            publish_request = PublishImageContent(
                title=title,
                content=content,
                images=images,
                tags=normalized_tags
            )
            
            # 执行发布
            result = await service.publish_content(publish_request, current_user, context)
            
            # 发送进度通知：发布完成
            if context:
                await context.report_progress(
                    progress=100,
                    total=100
                )
            
            return {
                "success": result.success,
                "result": result.dict() if hasattr(result, 'dict') else result.__dict__,
                "message": result.message if hasattr(result, 'message') else "内容发布完成"
            }
            
        finally:
            await browser_manager.stop()
        
    except Exception as e:
        logger.error(f"发布内容失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "发布内容失败"
        }


@mcp.tool
async def xiaohongshu_publish_video(
    title: str,
    content: str,
    video: str,
    tags: Optional[list[str]] = None,
    username: Optional[str] = None,
    context: Optional[Context] = None
) -> dict:
    """
    发布小红书视频内容
    
    Args:
        title: 视频标题（最多20个中文字或英文单词）
        content: 正文内容，不包含以#开头的标签内容
        video: 视频文件路径。支持本地视频文件绝对路径
        tags: 话题标签数组，默认 []。如 ["美食", "旅行", "生活"]，标签中的 # 号会自动移除
        username: 用户名（可选，如果不提供则使用全局用户）
        
    Returns:
        发布结果
    """
    try:
        # 处理默认值
        if tags is None:
            tags = []
        
        current_user = username or settings.GLOBAL_USER
        
        # 发送进度通知：开始检查登录状态
        if context:
            await context.report_progress(
                progress=10,
                total=100
            )
        
        # 检查用户登录状态（基于本地 cookies）
        login_check = await check_user_login_status(current_user)
        if not login_check.get("valid", False):
            return login_check
        
        # 发送进度通知：开始启动浏览器
        if context:
            await context.report_progress(
                progress=20,
                total=100
            )
        
        # 创建浏览器管理器，使用用户的cookie存储
        user_cookie_storage = CookieStorage(f"cookies_{current_user}.json")
        browser_manager = BrowserManager(cookie_storage=user_cookie_storage)
        await browser_manager.start()
        
        # 加载用户的cookies
        await browser_manager.load_cookies()
        logger.info(f"已为用户 {current_user} 加载cookies")
        
        try:
            service = XiaohongshuService(browser_manager)
            
            # 发送进度通知：开始发布视频
            if context:
                await context.report_progress(
                    progress=40,
                    total=100
                )
            
            # 规范化标签参数
            normalized_tags = normalize_tags(tags)
            logger.info(f"规范化后的标签: {normalized_tags}")
            
            # 构建发布请求
            publish_request = PublishVideoContent(
                title=title,
                video_path=video,
                content=content,
                tags=normalized_tags
            )
            
            # 执行发布
            result = await service.publish_video(publish_request, current_user, context)
            
            # 发送进度通知：发布完成
            if context:
                await context.report_progress(
                    progress=100,
                    total=100
                )
            
            return {
                "success": result.success,
                "result": result.dict() if hasattr(result, 'dict') else result.__dict__,
                "message": result.message if hasattr(result, 'message') else "视频发布完成"
            }
            
        finally:
            await browser_manager.stop()
        
    except Exception as e:
        logger.error(f"发布视频失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "发布视频失败"
        }


@mcp.tool
async def xiaohongshu_search_feeds(
    keyword: str,
    username: Optional[str] = None
) -> dict:
    """
    搜索小红书内容
    
    Args:
        keyword: 搜索关键词
        username: 用户名（可选，如果不提供则使用全局用户）
        
    Returns:
        搜索结果
    """
    try:
        current_user = username or settings.GLOBAL_USER
        
        # 检查用户登录状态（基于本地 cookies）
        login_check = await check_user_login_status(current_user)
        if not login_check.get("valid", False):
            return login_check
        
        # 创建浏览器管理器，使用用户的cookie存储
        user_cookie_storage = CookieStorage(f"cookies_{current_user}.json")
        browser_manager = BrowserManager(cookie_storage=user_cookie_storage)
        await browser_manager.start()
        
        # 加载用户的cookies
        await browser_manager.load_cookies()
        logger.info(f"已为用户 {current_user} 加载cookies")
        
        try:
            service = XiaohongshuService(browser_manager)
            
            # 执行搜索
            result = await service.search_content(keyword, username=current_user)
            
            return {
                "success": True,
                "result": result.dict() if hasattr(result, 'dict') else result.__dict__,
                "message": f"搜索关键词 '{keyword}' 成功"
            }
            
        finally:
            await browser_manager.stop()
        
    except Exception as e:
        logger.error(f"搜索内容失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "搜索内容失败"
        }


@mcp.tool
async def xiaohongshu_get_feeds(
    username: Optional[str] = None
) -> dict:
    """
    获取推荐内容列表
    
    Args:
        username: 用户名（可选，如果不提供则使用全局用户）
        
    Returns:
        推荐内容列表
    """
    try:
        current_user = username or settings.GLOBAL_USER
        
        # 检查用户登录状态（基于本地 cookies）
        login_check = await check_user_login_status(current_user)
        if not login_check.get("valid", False):
            return login_check
        
        # 创建浏览器管理器，使用用户的cookie存储
        user_cookie_storage = CookieStorage(f"cookies_{current_user}.json")
        browser_manager = BrowserManager(cookie_storage=user_cookie_storage)
        await browser_manager.start()
        
        # 加载用户的cookies
        await browser_manager.load_cookies()
        logger.info(f"已为用户 {current_user} 加载cookies")
        
        try:
            service = XiaohongshuService(browser_manager)
            
            # 获取推荐内容
            result = await service.get_feeds_list(username=current_user)
            
            return {
                "success": True,
                "result": result.dict() if hasattr(result, 'dict') else result.__dict__,
                "message": "获取推荐内容成功"
            }
            
        finally:
            await browser_manager.stop()
        
    except Exception as e:
        logger.error(f"获取推荐内容失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "获取推荐内容失败"
        }


@mcp.tool
async def xiaohongshu_list_feeds(
    username: Optional[str] = None
) -> dict:
    """
    获取首页推荐Feed列表（使用__INITIAL_STATE__方法，无需登录）
    
    Args:
        username: 用户名（可选，如果不提供则使用全局用户）
        
    Returns:
        首页推荐Feed列表
    """
    try:
        current_user = username or settings.GLOBAL_USER
        
        # 创建浏览器管理器和服务实例
        browser_manager = BrowserManager()
        await browser_manager.start()
        
        try:
            service = XiaohongshuService(browser_manager)
            
            # 获取首页推荐Feed列表
            result = await service.list_feeds(username=current_user)
            
            return {
                "success": result.success,
                "result": result.dict() if hasattr(result, 'dict') else result.__dict__,
                "message": "获取首页推荐Feed成功" if result.success else result.error
            }
            
        finally:
            await browser_manager.stop()
        
    except Exception as e:
        logger.error(f"获取首页推荐Feed失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "获取首页推荐Feed失败"
        }


@mcp.tool
async def xiaohongshu_get_user_profile(
    user_id: str,
    xsec_token: str,
    username: Optional[str] = None
) -> dict:
    """
    获取小红书用户主页信息
    
    Args:
        user_id: 小红书用户ID，从Feed列表获取
        xsec_token: 访问令牌，从Feed列表的xsecToken字段获取
        username: 用户名（可选，如果不提供则使用全局用户）
        
    Returns:
        用户主页信息
    """
    try:
        current_user = username or settings.GLOBAL_USER
        
        # 检查用户登录状态（基于本地 cookies）
        login_check = await check_user_login_status(current_user)
        if not login_check.get("valid", False):
            return login_check
        
        # 创建浏览器管理器，使用用户的cookie存储
        user_cookie_storage = CookieStorage(f"cookies_{current_user}.json")
        browser_manager = BrowserManager(cookie_storage=user_cookie_storage)
        await browser_manager.start()
        
        # 加载用户的cookies
        await browser_manager.load_cookies()
        logger.info(f"已为用户 {current_user} 加载cookies")
        
        try:
            service = XiaohongshuService(browser_manager)
            
            # 获取用户资料
            result = await service.get_user_profile(user_id, xsec_token, username=current_user)
            
            return {
                "success": True,
                "result": result.dict() if hasattr(result, 'dict') else result.__dict__,
                "message": f"获取用户 {user_id} 的资料成功"
            }
            
        finally:
            await browser_manager.stop()
        
    except Exception as e:
        logger.error(f"获取用户资料失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "获取用户资料失败"
        }


@mcp.tool
async def xiaohongshu_get_feed_detail(
    feed_id: str,
    xsec_token: str = "",
    username: Optional[str] = None
) -> dict:
    """
    获取小红书笔记详情
    
    Args:
        feed_id: 笔记ID
        xsec_token: xsec_token参数（可选，用于访问特定笔记）
        username: 用户名（可选，如果不提供则使用全局用户）
        
    Returns:
        笔记详情信息，包含笔记内容、互动数据和评论
    """
    # 参数验证
    if not feed_id or not feed_id.strip():
        return {
            "success": False,
            "error": "参数错误",
            "message": "feed_id 不能为空"
        }
    
    try:
        current_user = username or settings.GLOBAL_USER
        
        # 检查用户登录状态（基于本地 cookies）
        login_check = await check_user_login_status(current_user)
        if not login_check.get("valid", False):
            return login_check
        
        # 创建浏览器管理器，使用用户的cookie存储
        user_cookie_storage = CookieStorage(f"cookies_{current_user}.json")
        browser_manager = BrowserManager(cookie_storage=user_cookie_storage)
        await browser_manager.start()
        
        # 加载用户的cookies
        await browser_manager.load_cookies()
        logger.info(f"已为用户 {current_user} 加载cookies")
        
        try:
            service = XiaohongshuService(browser_manager)
            
            # 获取笔记详情
            xsec_token_param = xsec_token if xsec_token else None
            result = await service.get_feed_detail(feed_id, xsec_token_param, username=current_user)
            
            return {
                "success": True,
                "result": result.dict() if hasattr(result, 'dict') else result.__dict__,
                "message": f"获取笔记 {feed_id} 的详情成功"
            }
            
        finally:
            await browser_manager.stop()
        
    except Exception as e:
        logger.error(f"获取笔记详情失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "获取笔记详情失败"
        }


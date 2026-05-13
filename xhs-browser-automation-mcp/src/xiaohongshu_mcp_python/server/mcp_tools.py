"""
MCP 工具函数模块
包含所有 MCP 工具接口的实现
"""

import json
from typing import Optional, Union, List
from loguru import logger
from fastmcp import Context, FastMCP

from ..services.service import XiaohongshuService
from ..config import BrowserConfig, PublishImageContent, PublishVideoContent, settings
from ..browser import BrowserManager
from ..managers.user_session_manager import get_user_session_manager


# 创建 FastMCP 实例（需要在导入时创建，以便工具函数可以注册）
mcp = FastMCP("xiaohongshu-mcp-server")


def _clip_publish_title(s: str, max_len: int = 20) -> str:
    """与 PublishImageContent.title 的 max_length 对齐。"""
    if len(s) <= max_len:
        return s
    return s[:max_len]


def _parse_debug_publish_images_raw(raw: str) -> List[str]:
    """解析 MCP_DEBUG_PUBLISH_IMAGES：JSON 数组或单一路径字符串。"""
    if not (raw or "").strip():
        return []
    raw = raw.strip()
    if raw.startswith("["):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("MCP_DEBUG_PUBLISH_IMAGES JSON 解析失败，忽略")
            return []
        if not isinstance(data, list):
            return []
        return [str(x).strip() for x in data if str(x).strip()]
    return [raw]


def _parse_debug_publish_tags_raw(raw: str) -> List[str]:
    """解析 MCP_DEBUG_PUBLISH_TAGS：JSON 数组或逗号分隔。"""
    if not (raw or "").strip():
        return []
    raw = raw.strip()
    if raw.startswith("["):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("MCP_DEBUG_PUBLISH_TAGS JSON 解析失败，忽略")
            return []
        if not isinstance(data, list):
            return []
        return [str(x).strip() for x in data if str(x).strip()]
    return [t.strip() for t in raw.split(",") if t.strip()]


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
    调试接口：使用持久化浏览器 profile 进入小红书主页。

    Args:
        username: 用户名（可选，如果不提供则使用全局用户）

    Returns:
        包含操作结果的字典
    """
    try:
        current_user = username or settings.GLOBAL_USER
        logger.info(f"调试接口：为用户 {current_user} 初始化浏览器并进入主页")

        browser_manager = BrowserManager(
            headless=settings.BROWSER_HEADLESS,
            profile_user=current_user,
        )
        
        # 确保浏览器已启动且连接有效（避免仅 is_started 为真但进程已崩溃）
        await browser_manager.ensure_started()

        page = await browser_manager.get_page()

        homepage_url = "https://www.xiaohongshu.com/explore"
        logger.info(f"正在导航到小红书主页: {homepage_url}")

        def _looks_like_browser_closed(exc: BaseException) -> bool:
            name = type(exc).__name__.lower()
            msg = str(exc).lower()
            return (
                "targetclosed" in name
                or "targetclosederror" in name
                or "has been closed" in msg
                or "browser has been closed" in msg
            )

        for attempt in range(2):
            try:
                await page.goto(
                    homepage_url,
                    wait_until="domcontentloaded",
                    timeout=BrowserConfig.PAGE_LOAD_TIMEOUT,
                )
                logger.info("成功进入小红书主页")
                break
            except Exception as e:
                if attempt == 0 and _looks_like_browser_closed(e):
                    logger.warning(
                        "导航时浏览器或页面已断开，正在重启浏览器后重试一次: {}",
                        e,
                    )
                    await browser_manager.restart()
                    page = await browser_manager.get_page()
                    continue
                raise
        
        # 注意：这里不关闭浏览器，保持浏览器运行状态以便调试
        # 如果需要关闭，可以调用 await browser_manager.stop()
        
        return {
            "success": True,
            "status": "success",
            "username": current_user,
            "message": "已成功进入小红书主页（持久化 profile）"
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
    启动小红书登录会话（持久化浏览器 profile + user_sessions 记录）
    
    Args:
        headless: 是否使用无头模式，默认False（显示浏览器界面）
        fresh: 是否强制清理该用户会话并重新登录，默认 False
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
            # 强制创建新会话：清理会话记录与专用 profile
            logger.info(f"fresh=True，清理用户 {current_user} 的现有会话与专用 profile（若有）")
            await user_session_manager.cleanup_user_session(current_user)
        
        # 阻塞等待登录完成；若 user_sessions 中已有有效记录会直接返回已登录
        # 如果 headless 未指定，使用 settings 中的配置
        effective_headless = headless if headless is not None else settings.BROWSER_HEADLESS
        result = await user_session_manager.get_or_create_session(
            username=current_user,
            headless=effective_headless,
            wait_for_completion=True,
            fresh=fresh,
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
                message = "使用本地浏览器 profile，用户已登录（无需重新登录）"
            
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
    检查登录会话状态（以持久化 Chrome profile 内页面校验为准）
    
    Args:
        username: 用户名（可选，如果不提供则使用全局用户）
        
    Returns:
        包含登录状态信息的字典
    """
    try:
        user_session_manager = get_user_session_manager()
        current_user = username or settings.GLOBAL_USER
        
        user_session_status = await user_session_manager.get_user_session_status(current_user)
        
        if not user_session_status:
            return {
                "success": False,
                "status": "no_session",
                "username": current_user,
                "message": f"用户 {current_user} 在持久化浏览器 profile 中未检测到已登录，请先使用 xiaohongshu_start_login_session 登录",
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
    title: Optional[str] = None,
    content: Optional[str] = None,
    images: Optional[Union[str, List[str]]] = None,
    tags: Optional[list[str]] = None,
    username: Optional[str] = None,
    context: Optional[Context] = None
) -> dict:
    """
    发布小红书图文内容
    
    Args:
        title: 内容标题（最多20个中文字或英文单词）；可省略，空时用 Settings / .env 调试缺省
        content: 正文内容，不包含以#开头的标签内容；可省略，空时用调试缺省
        images: 本地绝对路径或图片 URL。可为字符串单路径，或数组 ['path1','path2']。
                Windows：在 JSON 中请使用正斜杠 `C:/Users/.../a.png`，或对反斜杠双重转义；
                单独一个反斜杠在 JSON 里会被当成转义符，导致路径损坏。
                可省略；空时用环境变量 MCP_DEBUG_PUBLISH_IMAGES（单路径或 JSON 数组）
        tags: 话题标签数组，默认 []。如 ["美食", "旅行", "生活"]，标签中的 # 号会自动移除；
              全空时用 MCP_DEBUG_PUBLISH_TAGS 或占位「调试」
        username: 用户名（可选，如果不提供则使用全局用户）
        
    Returns:
        发布结果
    """
    try:
        if images is None:
            images = []
        if tags is None:
            tags = []

        t = (title or "").strip()
        c = (content or "").strip()
        if not t:
            t = _clip_publish_title(settings.MCP_DEBUG_PUBLISH_TITLE)
        if not c:
            c = settings.MCP_DEBUG_PUBLISH_CONTENT
        title, content = t, c

        if isinstance(images, str):
            if not images.strip():
                images_list: List[str] = []
            else:
                images_list = [images.strip()]
        else:
            images_list = [str(x).strip() for x in (images or []) if str(x).strip()]

        if not images_list:
            images_list = _parse_debug_publish_images_raw(settings.MCP_DEBUG_PUBLISH_IMAGES_RAW)
        images = images_list

        # 记录接收到的参数（用于调试）
        logger.info(
            f"收到发布请求 - title: {title}, content长度: {len(content)}, "
            f"images数量: {len(images)}, tags: {tags} (类型: {type(tags)})"
        )
        
        current_user = username or settings.GLOBAL_USER
        
        if context:
            await context.report_progress(progress=15, total=100)
        
        browser_manager = BrowserManager(
            headless=settings.BROWSER_HEADLESS,
            profile_user=current_user,
        )
        await browser_manager.start()
        logger.info(f"已为用户 {current_user} 启动持久化浏览器上下文")
        
        try:
            service = XiaohongshuService(browser_manager)
            
            # 发送进度通知：开始发布内容
            if context:
                await context.report_progress(
                    progress=40,
                    total=100
                )
            
            # 规范化标签参数；全空时用 .env 或占位
            normalized_tags = normalize_tags(tags)
            if not normalized_tags:
                normalized_tags = normalize_tags(
                    _parse_debug_publish_tags_raw(settings.MCP_DEBUG_PUBLISH_TAGS_RAW)
                )
            if not normalized_tags:
                normalized_tags = normalize_tags(["调试"])
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
        
        if context:
            await context.report_progress(progress=15, total=100)
        
        browser_manager = BrowserManager(
            headless=settings.BROWSER_HEADLESS,
            profile_user=current_user,
        )
        await browser_manager.start()
        logger.info(f"已为用户 {current_user} 启动持久化浏览器上下文")
        
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
        
        browser_manager = BrowserManager(
            headless=settings.BROWSER_HEADLESS,
            profile_user=current_user,
        )
        await browser_manager.start()
        logger.info(f"已为用户 {current_user} 启动持久化浏览器上下文")
        
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
        
        browser_manager = BrowserManager(
            headless=settings.BROWSER_HEADLESS,
            profile_user=current_user,
        )
        await browser_manager.start()
        logger.info(f"已为用户 {current_user} 启动持久化浏览器上下文")
        
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
        
        browser_manager = BrowserManager(
            headless=settings.BROWSER_HEADLESS,
            profile_user=current_user,
        )
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
        
        browser_manager = BrowserManager(
            headless=settings.BROWSER_HEADLESS,
            profile_user=current_user,
        )
        await browser_manager.start()
        logger.info(f"已为用户 {current_user} 启动持久化浏览器上下文")
        
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
        
        browser_manager = BrowserManager(
            headless=settings.BROWSER_HEADLESS,
            profile_user=current_user,
        )
        await browser_manager.start()
        logger.info(f"已为用户 {current_user} 启动持久化浏览器上下文")
        
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


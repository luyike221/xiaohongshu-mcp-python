"""
小红书 XPath 和 CSS 选择器配置

集中管理所有页面元素的选择器，方便维护和更新。
"""


class XHSXPath:
    """小红书 XPath 和 CSS 选择器配置"""
    
    # ============ URL 配置 ============
    XHS_URL = "https://www.xiaohongshu.com/explore"
    
    # ============ 二维码相关 ============
    QR_CSS = ".login-container .qrcode-img"
    QR_XPATH = "//img[contains(@class, 'qrcode-img')]"
    
    # ============ 登录按钮 ============
    LOGIN_BUTTON_CSS = "button:has-text(\"登录\")"
    LOGIN_BUTTON_XPATH = '//ul/div[contains(@class, "channel-list-content")]//button[normalize-space(.)="登录"]'
    
    # ============ 用户链接（登录成功标识） ============
    USER_LINK_CSS = ".main-container .user .link-wrapper .channel"
    USER_LINK_XPATH = '//ul/div[contains(@class, "channel-list-content")]/li//a[normalize-space(.)="我"]'
    USER_LINK_XPATH_STRICT = '//ul/div[contains(@class, "channel-list-content")]/li//a[normalize-space(.)="我"][contains(@class, "link-wrapper")]'  # 更精确的版本
    
    # ============ 遮罩层 ============
    MASK_CSS = "i.reds-mask"
    
    # ============ 登录框 ============
    LOGIN_MODAL_CSS = ".login-container"  # CSS选择器作为备用
    LOGIN_MODAL_XPATH = "//div[@class=\"login-container\"]/div[@class=\"left\"]"  # 登录框XPath
    
    # ============ 登录 Cookie 名称 ============
    LOGIN_COOKIES = {"xhs_sso", "xsec_token", "webId"}


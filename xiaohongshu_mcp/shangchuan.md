查看浏览器自动化部分的实现：


[3 tools called]


查看浏览器初始化和管理的代码：


[2 tools called]


浏览器自动化部分说明：

## 浏览器自动化实现详解

### 1. 浏览器初始化与管理

#### 浏览器创建

```21:46:browser/browser.go
func NewBrowser(headless bool, options ...Option) *headless_browser.Browser {
	cfg := &browserConfig{}
	for _, opt := range options {
		opt(cfg)
	}

	opts := []headless_browser.Option{
		headless_browser.WithHeadless(headless),
	}
	if cfg.binPath != "" {
		opts = append(opts, headless_browser.WithChromeBinPath(cfg.binPath))
	}

	// 加载 cookies
	cookiePath := cookies.GetCookiesFilePath()
	cookieLoader := cookies.NewLoadCookie(cookiePath)

	if data, err := cookieLoader.LoadCookies(); err == nil {
		opts = append(opts, headless_browser.WithCookies(string(data)))
		logrus.Debugf("loaded cookies from filesuccessfully")
	} else {
		logrus.Warnf("failed to load cookies: %v", err)
	}

	return headless_browser.New(opts...)
}
```

要点：
- 支持有头/无头模式
- 自动加载保存的 cookies（保持登录状态）
- 可指定 Chrome 二进制路径

#### 服务层使用模式

```212:227:service.go
// publishContent 执行内容发布
func (s *XiaohongshuService) publishContent(ctx context.Context, content xiaohongshu.PublishImageContent) error {
	b := newBrowser()
	defer b.Close()

	page := b.NewPage()
	defer page.Close()

	action, err := xiaohongshu.NewPublishImageAction(page)
	if err != nil {
		return err
	}

	// 执行发布
	return action.Publish(ctx, content)
}
```

模式：创建浏览器 → 创建页面 → 执行操作 → 自动清理

---

### 2. 页面导航与初始化

#### 进入发布页面

```34:51:xiaohongshu/publish.go
func NewPublishImageAction(page *rod.Page) (*PublishAction, error) {

	pp := page.Timeout(300 * time.Second)

	pp.MustNavigate(urlOfPublic).MustWaitIdle().MustWaitDOMStable()
	time.Sleep(1 * time.Second)

	if err := mustClickPublishTab(page, "上传图文"); err != nil {
		logrus.Errorf("点击上传图文 TAB 失败: %v", err)
		return nil, err
	}

	time.Sleep(1 * time.Second)

	return &PublishAction{
		page: pp,
	}, nil
}
```

步骤：
1. 设置超时（300 秒）
2. 导航到发布页面
3. 等待页面空闲和 DOM 稳定
4. 点击“上传图文”标签页

#### 智能点击标签页（处理遮挡）

```100:134:xiaohongshu/publish.go
func mustClickPublishTab(page *rod.Page, tabname string) error {
	page.MustElement(`div.upload-content`).MustWaitVisible()

	deadline := time.Now().Add(15 * time.Second)
	for time.Now().Before(deadline) {
		tab, blocked, err := getTabElement(page, tabname)
		if err != nil {
			logrus.Warnf("获取发布 TAB 元素失败: %v", err)
			time.Sleep(200 * time.Millisecond)
			continue
		}

		if tab == nil {
			time.Sleep(200 * time.Millisecond)
			continue
		}

		if blocked {
			logrus.Info("发布 TAB 被遮挡，尝试移除遮挡")
			removePopCover(page)
			time.Sleep(200 * time.Millisecond)
			continue
		}

		if err := tab.Click(proto.InputMouseButtonLeft, 1); err != nil {
			logrus.Warnf("点击发布 TAB 失败: %v", err)
			time.Sleep(200 * time.Millisecond)
			continue
		}

		return nil
	}

	return errors.Errorf("没有找到发布 TAB - %s", tabname)
}
```

特点：
- 15 秒内重试
- 检测元素是否被遮挡
- 自动移除弹窗遮挡
- 失败时等待后重试

#### 检测元素是否被遮挡

```168:184:xiaohongshu/publish.go
func isElementBlocked(elem *rod.Element) (bool, error) {
	result, err := elem.Eval(`() => {
		const rect = this.getBoundingClientRect();
		if (rect.width === 0 || rect.height === 0) {
			return true;
		}
		const x = rect.left + rect.width / 2;
		const y = rect.top + rect.height / 2;
		const target = document.elementFromPoint(x, y);
		return !(target === this || this.contains(target));
	}`)
	if err != nil {
		return false, err
	}

	return result.Value.Bool(), nil
}
```

原理：使用 JavaScript 在元素中心点检测是否被其他元素覆盖。

#### 移除弹窗遮挡

```79:92:xiaohongshu/publish.go
func removePopCover(page *rod.Page) {

	// 先移除弹窗封面
	has, elem, err := page.Has("div.d-popover")
	if err != nil {
		return
	}
	if has {
		elem.MustRemove()
	}

	// 兜底：点击一下空位置吧
	clickEmptyPosition(page)
}
```

---

### 3. 图片上传自动化

#### 上传图片核心逻辑

```186:209:xiaohongshu/publish.go
func uploadImages(page *rod.Page, imagesPaths []string) error {
	pp := page.Timeout(30 * time.Second)

	// 验证文件路径有效性
	validPaths := make([]string, 0, len(imagesPaths))
	for _, path := range imagesPaths {
		if _, err := os.Stat(path); os.IsNotExist(err) {
			logrus.Warnf("图片文件不存在: %s", path)
			continue
		}
		validPaths = append(validPaths, path)

		logrus.Infof("获取有效图片：%s", path)
	}

	// 等待上传输入框出现
	uploadInput := pp.MustElement(".upload-input")

	// 上传多个文件
	uploadInput.MustSetFiles(validPaths...)

	// 等待并验证上传完成
	return waitForUploadComplete(pp, len(validPaths))
}
```

步骤：
1. 验证文件是否存在
2. 等待上传输入框出现
3. 使用 `MustSetFiles` 批量上传
4. 等待上传完成

#### 等待上传完成（轮询检测）

```211:240:xiaohongshu/publish.go
// waitForUploadComplete 等待并验证上传完成
func waitForUploadComplete(page *rod.Page, expectedCount int) error {
	maxWaitTime := 60 * time.Second
	checkInterval := 500 * time.Millisecond
	start := time.Now()

	slog.Info("开始等待图片上传完成", "expected_count", expectedCount)
使用这个项目，增强反检测https://pypi.org/project/playwright-stealth/ 
	for time.Since(start) < maxWaitTime {
		// 使用具体的pr类名检查已上传的图片
		uploadedImages, err := page.Elements(".img-preview-area .pr")

		slog.Info("uploadedImages", "uploadedImages", uploadedImages)

		if err == nil {
			currentCount := len(uploadedImages)
			slog.Info("检测到已上传图片", "current_count", currentCount, "expected_count", expectedCount)
			if currentCount >= expectedCount {
				slog.Info("所有图片上传完成", "count", currentCount)
				return nil
			}
		} else {
			slog.Debug("未找到已上传图片元素")
		}

		time.Sleep(checkInterval)
	}

	return errors.New("上传超时，请检查网络连接和图片大小")
}
```

机制：
- 每 500ms 检查一次
- 通过 `.img-preview-area .pr` 选择器统计已上传图片数量
- 最多等待 60 秒
- 达到预期数量即返回成功

---

### 4. 表单填写自动化

#### 填写标题、正文和标签

```242:266:xiaohongshu/publish.go
func submitPublish(page *rod.Page, title, content string, tags []string) error {

	titleElem := page.MustElement("div.d-input input")
	titleElem.MustInput(title)

	time.Sleep(1 * time.Second)

	if contentElem, ok := getContentElement(page); ok {
		contentElem.MustInput(content)

		inputTags(contentElem, tags)

	} else {
		return errors.New("没有找到内容输入框")
	}

	time.Sleep(1 * time.Second)

	submitButton := page.MustElement("div.submit div.d-button-content")
	submitButton.MustClick()

	time.Sleep(3 * time.Second)

	return nil
}
```

流程：
1. 定位标题输入框并填写
2. 定位正文输入框并填写
3. 输入标签
4. 点击发布按钮

#### 智能查找内容输入框（兼容多种样式）

```268:292:xiaohongshu/publish.go
// 查找内容输入框 - 使用Race方法处理两种样式
func getContentElement(page *rod.Page) (*rod.Element, bool) {
	var foundElement *rod.Element
	var found bool

	page.Race().
		Element("div.ql-editor").MustHandle(func(e *rod.Element) {
		foundElement = e
		found = true
	}).
		ElementFunc(func(page *rod.Page) (*rod.Element, error) {
			return findTextboxByPlaceholder(page)
		}).MustHandle(func(e *rod.Element) {
		foundElement = e
		found = true
	}).
		MustDo()

	if found {
		return foundElement, true
	}

	slog.Warn("no content element found by any method")
	return nil, false
}
```

说明：使用 `Race()` 同时尝试两种选择器，哪个先找到就用哪个。

#### 通过 placeholder 查找输入框

```354:410:xiaohongshu/publish.go
func findTextboxByPlaceholder(page *rod.Page) (*rod.Element, error) {
	elements := page.MustElements("p")
	if elements == nil {
		return nil, errors.New("no p elements found")
	}

	// 查找包含指定placeholder的元素
	placeholderElem := findPlaceholderElement(elements, "输入正文描述")
	if placeholderElem == nil {
		return nil, errors.New("no placeholder element found")
	}

	// 向上查找textbox父元素
	textboxElem := findTextboxParent(placeholderElem)
	if textboxElem == nil {
		return nil, errors.New("no textbox parent found")
	}

	return textboxElem, nil
}

func findPlaceholderElement(elements []*rod.Element, searchText string) *rod.Element {
	for _, elem := range elements {
		placeholder, err := elem.Attribute("data-placeholder")
		if err != nil || placeholder == nil {
			continue
		}

		if strings.Contains(*placeholder, searchText) {
			return elem
		}
	}
	return nil
}

func findTextboxParent(elem *rod.Element) *rod.Element {
	currentElem := elem
	for i := 0; i < 5; i++ {
		parent, err := currentElem.Parent()
		if err != nil {
			break
		}

		role, err := parent.Attribute("role")
		if err != nil || role == nil {
			currentElem = parent
			continue
		}

		if *role == "textbox" {
			return parent
		}

		currentElem = parent
	}
	return nil
}
```

策略：通过 placeholder 文本定位，再向上查找 `role="textbox"` 的父元素。

---

### 5. 标签输入自动化

#### 输入标签（模拟用户操作）

```294:352:xiaohongshu/publish.go
func inputTags(contentElem *rod.Element, tags []string) {
	if len(tags) == 0 {
		return
	}

	time.Sleep(1 * time.Second)

	for i := 0; i < 20; i++ {
		contentElem.MustKeyActions().
			Type(input.ArrowDown).
			MustDo()
		time.Sleep(10 * time.Millisecond)
	}

	contentElem.MustKeyActions().
		Press(input.Enter).
		Press(input.Enter).
		MustDo()

	time.Sleep(1 * time.Second)

	for _, tag := range tags {
		tag = strings.TrimLeft(tag, "#")
		inputTag(contentElem, tag)
	}
}

func inputTag(contentElem *rod.Element, tag string) {
	contentElem.MustInput("#")
	time.Sleep(200 * time.Millisecond)

	for _, char := range tag {
		contentElem.MustInput(string(char))
		time.Sleep(50 * time.Millisecond)
	}

	time.Sleep(1 * time.Second)

	page := contentElem.Page()
	topicContainer, err := page.Element("#creator-editor-topic-container")
	if err == nil && topicContainer != nil {
		firstItem, err := topicContainer.Element(".item")
		if err == nil && firstItem != nil {
			firstItem.MustClick()
			slog.Info("成功点击标签联想选项", "tag", tag)
			time.Sleep(200 * time.Millisecond)
		} else {
			slog.Warn("未找到标签联想选项，直接输入空格", "tag", tag)
			// 如果没有找到联想选项，输入空格结束
			contentElem.MustInput(" ")
		}
	} else {
		slog.Warn("未找到标签联想下拉框，直接输入空格", "tag", tag)
		// 如果没有找到下拉框，输入空格结束
		contentElem.MustInput(" ")
	}

	time.Sleep(500 * time.Millisecond) // 等待标签处理完成
}
```

流程：
1. 先按多次下箭头，确保光标在输入框
2. 输入 `#` 触发标签模式
3. 逐字符输入标签名（每个字符间隔 50ms）
4. 等待联想下拉框出现
5. 点击第一个联想选项，或输入空格完成

要点：
- 模拟真实输入速度
- 处理联想下拉框
- 有容错机制

---

### 6. 元素可见性检测

```412:436:xiaohongshu/publish.go
// isElementVisible 检查元素是否可见
func isElementVisible(elem *rod.Element) bool {

	// 检查是否有隐藏样式
	style, err := elem.Attribute("style")
	if err == nil && style != nil {
		styleStr := *style

		if strings.Contains(styleStr, "left: -9999px") ||
			strings.Contains(styleStr, "top: -9999px") ||
			strings.Contains(styleStr, "position: absolute; left: -9999px") ||
			strings.Contains(styleStr, "display: none") ||
			strings.Contains(styleStr, "visibility: hidden") {
			return false
		}
	}

	visible, err := elem.Visible()
	if err != nil {
		slog.Warn("无法获取元素可见性", "error", err)
		return true
	}

	return visible
}
```

检测方式：
- 检查 `style` 属性中的隐藏样式
- 调用 `Visible()` 方法
- 双重验证确保准确性

---

### 7. 完整发布流程总结

```53:77:xiaohongshu/publish.go
func (p *PublishAction) Publish(ctx context.Context, content PublishImageContent) error {
	if len(content.ImagePaths) == 0 {
		return errors.New("图片不能为空")
	}

	page := p.page.Context(ctx)

	if err := uploadImages(page, content.ImagePaths); err != nil {
		return errors.Wrap(err, "小红书上传图片失败")
	}

	tags := content.Tags
	if len(tags) >= 10 {
		logrus.Warnf("标签数量超过10，截取前10个标签")
		tags = tags[:10]
	}

	logrus.Infof("发布内容: title=%s, images=%v, tags=%v", content.Title, len(content.ImagePaths), tags)

	if err := submitPublish(page, content.Title, content.Content, tags); err != nil {
		return errors.Wrap(err, "小红书发布失败")
	}

	return nil
}
```

完整流程：
1. 验证图片数量
2. 上传图片（带等待机制）
3. 标签数量限制（最多 10 个）
4. 填写标题、正文、标签
5. 点击发布按钮

---

### 8. 技术要点总结

- 使用 go-rod 进行浏览器自动化
- 智能等待：`MustWaitIdle()`、`MustWaitDOMStable()`、轮询检测
- 容错处理：重试机制、遮挡检测、多种选择器策略
- 模拟真实操作：输入延迟、随机点击位置
- Cookie 管理：自动加载和保存登录状态
- 超时控制：操作级和整体超时

这套实现通过模拟真实用户操作，提高了自动化发布的成功率。
# 贡献指南

感谢你对快手视频信息爬取工具的关注！我们欢迎所有形式的贡献。

## 🤝 如何贡献

### 报告问题

如果你发现了 bug 或有功能建议：

1. 查看 [Issues](https://github.com/your-username/kuaishou-video-scraper/issues) 确认问题是否已被报告
2. 如果没有，请创建新的 Issue
3. 详细描述问题，包括：
   - 操作系统和 Python 版本
   - 详细的错误信息
   - 复现步骤
   - 期望的行为

### 提交代码

1. **Fork 项目**
   ```bash
   git clone https://github.com/your-username/kuaishou-video-scraper.git
   cd kuaishou-video-scraper
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

3. **进行开发**
   - 遵循现有的代码风格
   - 添加必要的注释
   - 确保代码可以正常运行

4. **测试你的更改**
   ```bash
   python gui_app.py
   ```

5. **提交更改**
   ```bash
   git add .
   git commit -m "feat: 添加新功能描述"
   # 或
   git commit -m "fix: 修复bug描述"
   ```

6. **推送到你的仓库**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **创建 Pull Request**
   - 在 GitHub 上创建 PR
   - 详细描述你的更改
   - 链接相关的 Issues

## 📝 代码规范

### Python 代码风格

- 遵循 PEP 8 规范
- 使用 4 个空格缩进
- 行长度不超过 88 字符
- 使用有意义的变量名和函数名

### 注释规范

```python
def fetch_video_info(self, url: str) -> dict:
    """
    获取视频信息
    
    Args:
        url: 视频链接
        
    Returns:
        包含视频信息的字典
        
    Raises:
        ValueError: 当URL格式不正确时
    """
    pass
```

### 提交信息规范

使用以下格式：

- `feat: 添加新功能`
- `fix: 修复bug`
- `docs: 更新文档`
- `style: 代码格式调整`
- `refactor: 代码重构`
- `test: 添加测试`
- `chore: 其他更改`

## 🧪 测试

在提交代码前，请确保：

1. **基本功能测试**
   - 程序能正常启动
   - GUI 界面显示正常
   - 基本的爬取功能工作正常

2. **边界情况测试**
   - 空文件处理
   - 无效链接处理
   - 网络异常处理

3. **性能测试**
   - 大量数据处理
   - 高并发情况

## 📚 开发环境设置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 开发工具（推荐）

- **IDE**: PyCharm / VS Code
- **代码格式化**: black
- **代码检查**: flake8
- **类型检查**: mypy

### 3. 安装开发依赖

```bash
pip install black flake8 mypy
```

### 4. 代码格式化

```bash
black gui_app.py
flake8 gui_app.py
```

## 🎯 开发重点

### 优先级高的改进方向

1. **性能优化**
   - 提高爬取速度
   - 减少内存使用
   - 优化并发处理

2. **用户体验**
   - 改进界面设计
   - 添加更多配置选项
   - 提供更详细的进度信息

3. **稳定性**
   - 增强错误处理
   - 提高重试机制
   - 添加更多异常情况处理

4. **功能扩展**
   - 支持更多视频平台
   - 添加数据分析功能
   - 支持更多导出格式

### 代码结构

```
gui_app.py
├── WorkerThread          # 工作线程类
│   ├── fetch_video_info  # 爬取视频信息
│   └── run              # 主执行逻辑
├── MainWindow           # 主窗口类
│   ├── init_ui          # 界面初始化
│   ├── start_crawling   # 开始爬取
│   └── stop_crawling    # 停止爬取
└── utility functions    # 工具函数
```

## ❓ 常见问题

### Q: 如何调试网络请求？
A: 在代码中添加详细的日志输出，使用 `self.log_updated.emit()` 显示调试信息。

### Q: 如何测试新的视频链接格式？
A: 在 `extract_video_id()` 函数中添加新的正则表达式匹配规则。

### Q: 如何添加新的数据字段？
A: 在 `parse_video_data()` 函数中添加新的字段解析逻辑。

## 📞 联系我们

- 📧 Email: your-email@example.com
- 💬 Discussions: [GitHub Discussions](https://github.com/your-username/kuaishou-video-scraper/discussions)
- 🐛 Issues: [GitHub Issues](https://github.com/your-username/kuaishou-video-scraper/issues)

## 🙏 致谢

感谢所有贡献者的努力！你们的贡献让这个项目变得更好。

---

再次感谢你的贡献！🎉

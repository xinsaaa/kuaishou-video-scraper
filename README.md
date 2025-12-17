# 快手视频信息爬取工具

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.6+-green.svg)](https://pypi.org/project/PyQt6/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个基于 PyQt6 的快手视频信息批量爬取工具，支持异步并发处理，提供友好的图形界面。

## ✨ 功能特性

- 🚀 **异步并发**：使用 aiohttp 实现高效的异步爬取
- 🖥️ **图形界面**：基于 PyQt6 的现代化 GUI 界面
- 📊 **批量处理**：支持 Excel 文件批量导入和处理
- 🔄 **智能重试**：自动重试机制，提高成功率
- 📝 **详细日志**：实时显示爬取进度和状态
- 💾 **数据导出**：结果自动保存为 Excel 格式
- 🛡️ **错误处理**：完善的异常处理和错误记录

## 📋 系统要求

- Python 3.8 或更高版本
- Windows / macOS / Linux

## 🚀 快速开始

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/your-username/kuaishou-video-scraper.git
cd kuaishou-video-scraper

# 安装依赖
pip install -r requirements.txt
```

### 运行程序

```bash
python gui_app.py
```

### 打包为可执行文件

```bash
# 方法1：使用批处理文件（Windows）
双击 "打包为exe.bat"

# 方法2：使用Python脚本
python build_exe.py

# 方法3：直接使用PyInstaller
conda activate kuaishou  # 如果使用conda环境
pyinstaller --onefile --windowed --name="快手视频信息爬取工具" --clean --noconfirm gui_app.py
```

## 📖 使用说明

### 1. 准备输入文件

创建一个 Excel 文件，包含快手视频链接。支持以下格式：

- **短链接**：`https://v.kuaishou.com/xxxxx`
- **完整链接**：`https://www.kuaishou.com/short-video/xxxxx`
- **移动端链接**：`https://m.kuaishou.com/short-video/xxxxx`

### 2. 操作步骤

1. **选择输入文件**：点击"浏览"选择包含视频链接的 Excel 文件
2. **选择输出文件**：指定结果保存位置
3. **设置并发数**：根据网络情况调整（建议 5-20）
4. **开始爬取**：点击"开始爬取"按钮
5. **查看结果**：实时查看进度和日志信息

### 3. 输出字段

爬取成功后，Excel 文件将包含以下信息：

| 字段名 | 说明 |
|--------|------|
| 原始链接 | 输入的视频链接 |
| 视频ID | 快手视频唯一标识 |
| 作者名字 | 视频作者昵称 |
| 作者ID | 作者唯一标识 |
| 视频标题 | 视频描述文本 |
| 点赞数量 | 视频点赞数 |
| 评论数量 | 视频评论数 |
| 分享数量 | 视频分享数 |
| 播放数量 | 视频播放数 |
| 发布时间 | 视频发布时间 |
| 解析状态 | 成功/失败 |
| 错误原因 | 失败时的错误信息 |

## 🛠️ 技术栈

- **GUI框架**：PyQt6
- **HTTP客户端**：aiohttp (异步) + requests (同步)
- **数据处理**：pandas
- **Excel处理**：openpyxl
- **打包工具**：PyInstaller

## 📁 项目结构

```
kuaishou-video-scraper/
├── gui_app.py              # 主程序文件
├── build_exe.py            # 打包脚本
├── 打包为exe.bat           # Windows批处理打包
├── requirements.txt        # 依赖列表
├── README.md              # 项目说明
├── LICENSE                # 开源许可证
├── .gitignore             # Git忽略文件
└── docs/                  # 文档目录
    └── screenshots/       # 截图目录
```

## 🔧 配置说明

### 并发设置

- **低并发**（1-5）：网络较慢或需要更稳定的爬取
- **中等并发**（5-15）：一般网络环境，推荐设置
- **高并发**（15-30）：网络良好，追求速度

### 重试机制

程序内置智能重试机制：
- 超时重试：网络超时自动重试
- 错误重试：遇到临时错误自动重试
- 最大重试次数：3次

## ⚠️ 注意事项

1. **合法使用**：请遵守快手平台的使用条款和相关法律法规
2. **频率控制**：避免过于频繁的请求，建议合理设置并发数
3. **数据用途**：仅用于学习研究目的，不得用于商业用途
4. **隐私保护**：尊重用户隐私，不要爬取敏感信息

## 🐛 常见问题

### Q: 为什么有些视频爬取失败？
A: 可能的原因：
- 视频已被删除或设为私密
- 网络连接问题
- 快手反爬虫机制
- 视频链接格式不正确

### Q: 如何提高爬取成功率？
A: 建议：
- 降低并发数（5-10）
- 确保网络连接稳定
- 使用最新版本的程序
- 检查输入链接格式

### Q: 程序运行出错怎么办？
A: 解决步骤：
1. 检查Python版本（需要3.8+）
2. 重新安装依赖：`pip install -r requirements.txt`
3. 查看错误日志信息
4. 在Issues中报告问题

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支：`git checkout -b feature/AmazingFeature`
3. 提交更改：`git commit -m 'Add some AmazingFeature'`
4. 推送到分支：`git push origin feature/AmazingFeature`
5. 提交 Pull Request

## 📄 开源许可

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [PyQt6](https://pypi.org/project/PyQt6/) - 强大的GUI框架
- [aiohttp](https://aiohttp.readthedocs.io/) - 异步HTTP客户端
- [pandas](https://pandas.pydata.org/) - 数据处理库
- [PyInstaller](https://pyinstaller.readthedocs.io/) - Python打包工具

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 📧 Email: your-email@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/your-username/kuaishou-video-scraper/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/your-username/kuaishou-video-scraper/discussions)

---

⭐ 如果这个项目对你有帮助，请给个星标支持一下！

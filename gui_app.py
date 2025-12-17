"""
快手视频信息爬取工具 - GUI版本
使用 PyQt6 + asyncio + aiohttp 实现异步爬取
"""

import sys
import asyncio
import aiohttp
import re
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QProgressBar,
    QFileDialog, QSpinBox, QGroupBox, QMessageBox, QCheckBox
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont

# 已移除fake_useragent，使用固定User-Agent
# 已移除代理管理器
# 已移除浏览器监控和设备认证功能


class WorkerThread(QThread):
    """工作线程 - 执行异步爬取任务"""
    
    # 信号定义
    progress_updated = pyqtSignal(int, int)  # 当前进度, 总数
    log_updated = pyqtSignal(str)  # 日志信息
    task_finished = pyqtSignal(str)  # 完成信息
    error_occurred = pyqtSignal(str)  # 错误信息
    
    def __init__(self, input_file, url_columns, output_file, max_concurrent):
        super().__init__()
        self.input_file = input_file
        self.url_columns = url_columns
        self.output_file = output_file
        self.max_concurrent = max_concurrent
        self.is_running = True
    
    def run(self):
        """线程主函数"""
        try:
            # 在新的事件循环中运行异步任务
            asyncio.run(self.process_videos())
        except Exception as e:
            self.error_occurred.emit(f"发生错误: {str(e)}")
    
    def stop(self):
        """停止任务"""
        self.is_running = False
    
    async def process_videos(self):
        """异步处理视频信息"""
        try:
            # 不使用代理，直接请求
            
            # 读取Excel
            self.log_updated.emit(f"正在读取文件: {self.input_file}")
            df = pd.read_excel(self.input_file)
            
            # 检查列 - 优先寻找包含"发布链接"的列
            available_columns = []
            
            # 1. 寻找包含"发布链接"的列
            for col in df.columns:
                if "发布链接" in str(col):
                    available_columns.append(col)
                    break
            
            # 2. 如果没找到，使用默认的链接列
            if not available_columns:
                available_columns = [col for col in self.url_columns if col in df.columns]
            
            if not available_columns:
                self.error_occurred.emit("找不到链接列（寻找包含'发布链接'的列或默认链接列）")
                return
            
            self.log_updated.emit(f"共找到 {len(df)} 条记录")
            self.log_updated.emit(f"使用链接列: {', '.join(available_columns)}")
            
            # 提取链接
            def get_first_valid_url(row):
                for col in available_columns:
                    url = row.get(col)
                    if pd.notna(url) and url:
                        return url
                return None
            
            df['链接'] = df.apply(get_first_valid_url, axis=1)
            
            # 调试：统计链接情况
            total_links = len(df)
            valid_links_count = df['链接'].notna().sum()
            empty_links_count = total_links - valid_links_count
            
            self.log_updated.emit(f"\n链接统计:")
            self.log_updated.emit(f"  总数: {total_links}")
            self.log_updated.emit(f"  有效: {valid_links_count}")
            self.log_updated.emit(f"  空白: {empty_links_count}")
            
            # 调试：显示前几个链接样例
            valid_links = df['链接'].dropna().head(5)
            if len(valid_links) > 0:
                self.log_updated.emit(f"\n链接样例:")
                for i, link in enumerate(valid_links, 1):
                    self.log_updated.emit(f"  {i}. {link[:80]}...")
            
            # 直接处理链接，边提取ID边获取视频信息
            self.log_updated.emit(f"\n开始处理链接并获取视频信息...")
            if not self.is_running:
                return
            
            # 初始化列
            info_columns = [
                '粉丝数量', '收藏数量', '作品数量', '作者ID', '作者名字',
                '点赞数量', '评论数量', '播放量', '分享数量', '作品文案',
                '视频时长', '视频宽度', '视频高度', '发布时间'
            ]
            for col in info_columns:
                df[col] = None
            
            df['解析状态'] = '待处理'
            df['错误原因'] = ''
            df['作品ID'] = None
            
            # 直接处理所有链接：边提取ID边获取视频信息
            async with aiohttp.ClientSession() as session:
                semaphore = asyncio.Semaphore(self.max_concurrent)
                tasks = []
                total = len(df)
                
                for idx, row in df.iterrows():
                    if not self.is_running:
                        self.log_updated.emit("\n任务已取消")
                        return
                    
                    url = row['链接']
                    if pd.notna(url):
                        # 创建处理单个链接的任务（提取ID + 获取数据）
                        task = self.process_single_url_async(
                            session, url, idx, df, semaphore, total
                        )
                        tasks.append(task)
                
                # 并发执行所有任务
                try:
                    await asyncio.gather(*tasks)
                except asyncio.CancelledError:
                    self.log_updated.emit("任务已取消")
                    return
            
            # 准备输出
            output_df = self.prepare_output_dataframe(df)
            
            # 生成带时间戳的输出文件名
            from pathlib import Path
            output_path = Path(self.output_file)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_filename = f"{output_path.stem}_{timestamp}{output_path.suffix}"
            final_output_file = output_path.parent / new_filename
            
            # 保存结果
            output_df.to_excel(final_output_file, index=False)
            
            self.log_updated.emit(f"文件已保存: {final_output_file}")
            
            # 统计
            fetched = df['作者名字'].notna().sum()
            self.log_updated.emit(f"\n处理完成！")
            self.log_updated.emit(f"成功获取: {fetched}/{total}")
            
            if fetched > 0:
                self.log_updated.emit(f"\n统计信息:")
                self.log_updated.emit(f"  总播放量: {df['播放量'].sum():,}")
                self.log_updated.emit(f"  总点赞数: {df['点赞数量'].sum():,}")
                self.log_updated.emit(f"  平均播放量: {df['播放量'].mean():,.0f}")
            
            self.task_finished.emit(str(final_output_file))
            
        except Exception as e:
            self.error_occurred.emit(f"处理失败: {str(e)}")
    
    async def process_single_url_async(self, session, url, idx, df, semaphore, total):
        """处理单个URL：直接用移动端UA访问原始链接"""
        async with semaphore:
            if not self.is_running:
                return
            
            # 直接访问原始链接，让快手自动重定向到移动端页面
            await self.fetch_video_info_from_url(session, url, idx, df, total)
    
    async def fetch_video_info_from_url(self, session, url, idx, df, total):
        """直接从原始URL获取视频信息"""
        max_retries = 3
        retry_count = 0
        
        
        while retry_count < max_retries and self.is_running:
            if not self.is_running:
                return
            
            # 直接访问原始链接，让快手自动重定向到移动端页面
                
            try:
                # 调试：记录原始URL请求
                if idx % 10 == 0:
                    self.log_updated.emit(f"🌐 直接访问: {url}")
                
                # 使用固定的移动端User-Agent（避免fake_useragent在exe中的问题）
                mobile_user_agents = [
                    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                    'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36',
                    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
                    'Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36'
                ]
                import random
                headers = {
                    'User-Agent': random.choice(mobile_user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Upgrade-Insecure-Requests': '1',
                    'Connection': 'keep-alive',
                }
                
                # 不使用代理，直接发送请求
                # 发送请求，允许重定向
                async with session.get(
                    url, 
                    headers=headers, 
                    timeout=aiohttp.ClientTimeout(total=15),
                    ssl=False,
                    allow_redirects=True  # 允许自动重定向
                ) as response:
                    final_url = str(response.url)
                    if idx % 10 == 0:
                        self.log_updated.emit(f"🔄 重定向到: {final_url}")
                    
                    if response.status != 200:
                        # 统一归类为视频已删除
                        df.at[idx, '解析状态'] = '失败'
                        df.at[idx, '错误原因'] = '找不到视频，已被删除或下架'
                        self.log_updated.emit(f"❌ 视频已删除或下架 (HTTP{response.status}): {url}")
                        return
                    
                    html = await response.text()
                    
                    # 调试：记录HTML长度
                    if idx % 10 == 0:
                        self.log_updated.emit(f"📄 HTML长度: {len(html)} 字符")
                    
                    # 解析数据
                    data = self.extract_json_from_html(html)
                    if data:
                        # 调试：直接在HTML中搜索纯数字photoId
                        import re
                        numeric_photo_ids = re.findall(r'"photoId":\s*"?(\d{15,})"?', html)
                        if numeric_photo_ids and idx % 10 == 0:
                            self.log_updated.emit(f"🔍 HTML中找到纯数字photoId: {numeric_photo_ids}")
                        
                        info = self.extract_video_info(data)
                        if info:
                            # 成功解析
                            # 更新DataFrame
                            for key, value in info.items():
                                df.at[idx, key] = value
                            
                            # 强制使用纯数字photoId
                            api_photo_id = str(info.get('作品ID', ''))
                            
                            # 如果HTML中找到了纯数字photoId，直接使用第一个
                            if numeric_photo_ids:
                                api_photo_id = numeric_photo_ids[0]
                                if idx % 10 == 0:
                                    self.log_updated.emit(f"🎯 强制使用HTML中的纯数字ID: {api_photo_id}")
                            
                            df.at[idx, '作品ID'] = api_photo_id
                            
                            if api_photo_id and api_photo_id.isdigit():
                                if idx % 10 == 0:
                                    self.log_updated.emit(f"🎯 纯数字ID: {api_photo_id}")
                            else:
                                if idx % 10 == 0:
                                    self.log_updated.emit(f"📝 字符串ID: '{api_photo_id}' (长度:{len(api_photo_id)})")
                            
                            # 更新解析状态
                            df.at[idx, '解析状态'] = '成功'
                            
                            # 更新进度
                            current = df['作者名字'].notna().sum()
                            self.progress_updated.emit(current, total)
                            
                            self.log_updated.emit(
                                f"[{current}/{total}] ✓ {info.get('作者名字', 'N/A')} - "
                                f"{info.get('点赞数量', 0):,}赞"
                            )
                            return
                        else:
                            # JSON解析成功但提取视频信息失败
                            df.at[idx, '解析状态'] = '失败'
                            df.at[idx, '错误原因'] = '找不到视频，已被删除或下架'
                            self.log_updated.emit(f"❌ 视频已删除或下架: {url}")
                            return
                    else:
                        # HTML解析失败
                        df.at[idx, '解析状态'] = '失败'
                        df.at[idx, '错误原因'] = '找不到视频，已被删除或下架'
                        self.log_updated.emit(f"❌ 视频已删除或下架: {url}")
                        return
                
                # 如果到这里说明请求失败
                
                retry_count += 1
                if retry_count < max_retries:
                    await asyncio.sleep(0.5)
                    continue
                else:
                    df.at[idx, '解析状态'] = '失败'
                    df.at[idx, '错误原因'] = '找不到视频，已被删除或下架'
                    self.log_updated.emit(f"[{idx+1}/{total}] ✗ 视频已删除或下架: {url}")
                    return
            
            except asyncio.TimeoutError:
                retry_count += 1
                if retry_count < max_retries:
                    self.log_updated.emit(f"[{idx+1}/{total}] ⏱ 超时重试({retry_count}/{max_retries}): {url}")
                    await asyncio.sleep(0.5)
                    continue
                else:
                    df.at[idx, '解析状态'] = '失败'
                    df.at[idx, '错误原因'] = '找不到视频，已被删除或下架'
                    self.log_updated.emit(f"[{idx+1}/{total}] ✗ 视频已删除或下架 (超时): {url}")
                    return
            
            except Exception as e:
                self.log_updated.emit(f"异常详情 {url}: {type(e).__name__}: {str(e)}")
                
                # 异常处理
                retry_count += 1
                if retry_count < max_retries:
                    await asyncio.sleep(0.5)
                    continue
                else:
                    df.at[idx, '解析状态'] = '失败'
                    df.at[idx, '错误原因'] = '找不到视频，已被删除或下架'
                    self.log_updated.emit(f"[{idx+1}/{total}] ✗ 视频已删除或下架 (异常): {url}")
                    return
    
    async def fetch_video_info_with_id(self, session, video_id, idx, df, total):
        """使用视频ID获取视频信息"""
        max_retries = 3
        retry_count = 0
        
        
        while retry_count < max_retries and self.is_running:
            if not self.is_running:
                return
            
            try:
                api_url = f"https://m.gifshow.com/fw/photo/{video_id}"
                
                # 调试：记录API请求（每10个记录一次）
                if idx % 10 == 0:
                    self.log_updated.emit(f"API请求: {api_url}")
                
                # 使用固定的移动端User-Agent（避免fake_useragent在exe中的问题）
                mobile_user_agents = [
                    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                    'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36',
                    'Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36'
                ]
                import random
                headers = {
                    'User-Agent': random.choice(mobile_user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Upgrade-Insecure-Requests': '1',
                    'Connection': 'keep-alive',
                    'Referer': 'https://www.kuaishou.com/',
                }
                
                # 不使用代理，直接发送请求
                
                # 发送请求
                async with session.get(
                    api_url, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15),  # 增加超时时间
                    ssl=False  # 跳过SSL验证，避免证书问题
                ) as response:
                    # 调试：记录HTTP状态码（失败时）
                    if response.status != 200:
                        # 统一归类为视频已删除
                        df.at[idx, '解析状态'] = '失败'
                        df.at[idx, '错误原因'] = '找不到视频，已被删除或下架'
                        self.log_updated.emit(f"❌ 视频已删除或下架 (HTTP{response.status}): {video_id}")
                        
                        # 保存HTTP错误响应
                        try:
                            html = await response.text()
                            import os
                            current_dir = os.getcwd()
                            failed_dir = os.path.join(current_dir, "failed_responses")
                            os.makedirs(failed_dir, exist_ok=True)
                            
                            # 保存HTTP错误响应
                            failed_html_file = os.path.join(failed_dir, f"http_{response.status}_{video_id}.html")
                            with open(failed_html_file, 'w', encoding='utf-8') as f:
                                f.write(html)
                            
                            self.log_updated.emit(f"💾 已保存HTTP{response.status}响应: http_{response.status}_{video_id}.html")
                        except Exception as e:
                            self.log_updated.emit(f"⚠️ 保存HTTP错误响应出错: {str(e)}")
                    
                    if response.status == 200:
                        html = await response.text()
                        
                        # 调试：记录HTML长度和关键信息
                        if idx % 10 == 0:
                            self.log_updated.emit(f"📄 HTML长度: {len(html)} 字符")
                        
                        # 解析数据
                        data = self.extract_json_from_html(html)
                        if data:
                            # 调试：直接在HTML中搜索纯数字photoId
                            import re
                            numeric_photo_ids = re.findall(r'"photoId":\s*"?(\d{15,})"?', html)
                            if numeric_photo_ids and idx % 10 == 0:
                                self.log_updated.emit(f"🔍 HTML中找到纯数字photoId: {numeric_photo_ids}")
                            
                            info = self.extract_video_info(data)
                            if info:
                                # 成功解析
                                # 更新DataFrame
                                for key, value in info.items():
                                    df.at[idx, key] = value
                                
                                # 强制使用纯数字photoId
                                api_photo_id = str(info.get('作品ID', ''))
                                
                                # 如果HTML中找到了纯数字photoId，直接使用第一个
                                if numeric_photo_ids:
                                    api_photo_id = numeric_photo_ids[0]
                                    if idx % 10 == 0:
                                        self.log_updated.emit(f"🎯 强制使用HTML中的纯数字ID: {api_photo_id}")
                                
                                df.at[idx, '作品ID'] = api_photo_id  # 无论如何都要设置
                                
                                if api_photo_id and api_photo_id.isdigit():
                                    if idx % 10 == 0:
                                        self.log_updated.emit(f"🎯 纯数字ID: {video_id} -> {api_photo_id}")
                                else:
                                    if idx % 10 == 0:
                                        self.log_updated.emit(f"📝 字符串ID: '{api_photo_id}' (长度:{len(api_photo_id)})")
                                
                                # 更新解析状态
                                df.at[idx, '解析状态'] = '成功'
                                
                                # 更新进度
                                current = df['作者名字'].notna().sum()
                                self.progress_updated.emit(current, total)
                                
                                self.log_updated.emit(
                                    f"[{current}/{total}] ✓ {info.get('作者名字', 'N/A')} - "
                                    f"{info.get('点赞数量', 0):,}赞"
                                )
                                return
                            else:
                                # JSON解析成功但提取视频信息失败 - 统一归类为视频已删除
                                df.at[idx, '解析状态'] = '失败'
                                df.at[idx, '错误原因'] = '找不到视频，已被删除或下架'
                                self.log_updated.emit(f"❌ 视频已删除或下架: {video_id}")
                                
                                # 保存失败的HTML响应用于分析
                                try:
                                    import os
                                    # 获取当前工作目录作为保存位置
                                    current_dir = os.getcwd()
                                    failed_dir = os.path.join(current_dir, "failed_responses")
                                    os.makedirs(failed_dir, exist_ok=True)
                                    
                                    # 保存HTML
                                    failed_html_file = os.path.join(failed_dir, f"failed_{video_id}.html")
                                    with open(failed_html_file, 'w', encoding='utf-8') as f:
                                        f.write(html)
                                    
                                    # 保存JSON数据
                                    failed_json_file = os.path.join(failed_dir, f"failed_{video_id}.json")
                                    import json
                                    with open(failed_json_file, 'w', encoding='utf-8') as f:
                                        json.dump(data, f, ensure_ascii=False, indent=2)
                                    
                                    self.log_updated.emit(f"💾 已保存失败响应: failed_{video_id}.html 和 .json")
                                except Exception as e:
                                    self.log_updated.emit(f"⚠️ 保存失败响应出错: {str(e)}")
                                
                                if idx % 10 == 0:
                                    # 检查JSON结构
                                    json_keys = list(data.keys()) if isinstance(data, dict) else []
                                    self.log_updated.emit(f"📋 JSON顶层键: {json_keys[:10]}")
                                    
                                    # 检查是否有photo相关的键
                                    photo_keys = [k for k in json_keys if 'photo' in k.lower()]
                                    if photo_keys:
                                        self.log_updated.emit(f"🎬 photo相关键: {photo_keys}")
                                    
                                    # 检查第一层是否有counts和photo
                                    for key, value in data.items():
                                        if isinstance(value, dict):
                                            sub_keys = list(value.keys())
                                            if 'photo' in sub_keys and 'counts' in sub_keys:
                                                self.log_updated.emit(f"✅ 找到photo+counts结构在: {key}")
                                            elif 'photo' in sub_keys:
                                                self.log_updated.emit(f"📸 只找到photo在: {key}")
                                            elif 'counts' in sub_keys:
                                                self.log_updated.emit(f"📊 只找到counts在: {key}")
                        else:
                            # HTML解析失败 - 统一归类为视频已删除
                            df.at[idx, '解析状态'] = '失败'
                            df.at[idx, '错误原因'] = '找不到视频，已被删除或下架'
                            self.log_updated.emit(f"❌ 视频已删除或下架: {video_id}")
                            
                            # 保存HTML解析失败的响应
                            try:
                                import os
                                # 获取当前工作目录作为保存位置
                                current_dir = os.getcwd()
                                failed_dir = os.path.join(current_dir, "failed_responses")
                                os.makedirs(failed_dir, exist_ok=True)
                                
                                # 保存HTML
                                failed_html_file = os.path.join(failed_dir, f"no_json_{video_id}.html")
                                with open(failed_html_file, 'w', encoding='utf-8') as f:
                                    f.write(html)
                                
                                self.log_updated.emit(f"💾 已保存无JSON响应: no_json_{video_id}.html")
                            except Exception as e:
                                self.log_updated.emit(f"⚠️ 保存无JSON响应出错: {str(e)}")
                            
                            if idx % 10 == 0:
                                # 检查HTML是否包含INIT_STATE
                                has_init_state = "INIT_STATE" in html
                                self.log_updated.emit(f"🔍 HTML包含INIT_STATE: {has_init_state}")
                                if not has_init_state:
                                    # 可能是重定向到登录页或其他页面
                                    title_match = re.search(r'<title>(.*?)</title>', html)
                                    title = title_match.group(1) if title_match else "未知"
                                    self.log_updated.emit(f"📄 页面标题: {title}")
                
                # 如果到这里说明请求失败
                
                retry_count += 1
                if retry_count < max_retries:
                    await asyncio.sleep(0.5)  # 短暂延迟后重试
                    continue
                else:
                    df.at[idx, '解析状态'] = '失败'
                    df.at[idx, '错误原因'] = '找不到视频，已被删除或下架'
                    # 添加详细的失败信息
                    id_length = len(str(video_id))
                    self.log_updated.emit(f"[{idx+1}/{total}] ✗ 视频已删除或下架: {video_id} (长度:{id_length}位)")
                    return
            
            except asyncio.TimeoutError:
                retry_count += 1
                if retry_count < max_retries:
                    self.log_updated.emit(f"[{idx+1}/{total}] ⏱ 超时重试({retry_count}/{max_retries}): {video_id}")
                    await asyncio.sleep(0.5)
                    continue
                else:
                    df.at[idx, '解析状态'] = '失败'
                    df.at[idx, '错误原因'] = '找不到视频，已被删除或下架'
                    self.log_updated.emit(f"[{idx+1}/{total}] ✗ 视频已删除或下架 (超时): {video_id}")
                    return
            
            except Exception as e:
                # 显示详细的异常信息用于调试
                self.log_updated.emit(f"异常详情 {video_id}: {type(e).__name__}: {str(e)}")
                
                # 保存异常信息到文件
                try:
                    import os
                    current_dir = os.getcwd()
                    failed_dir = os.path.join(current_dir, "failed_responses")
                    os.makedirs(failed_dir, exist_ok=True)
                    
                    # 保存异常信息
                    exception_file = os.path.join(failed_dir, f"exception_{video_id}.txt")
                    with open(exception_file, 'w', encoding='utf-8') as f:
                        f.write(f"Video ID: {video_id}\n")
                        f.write(f"API URL: https://m.gifshow.com/fw/photo/{video_id}\n")
                        f.write(f"Exception Type: {type(e).__name__}\n")
                        f.write(f"Exception Message: {str(e)}\n")
                        f.write(f"Retry Count: {retry_count}/{max_retries}\n")
                    
                    if retry_count == max_retries - 1:  # 最后一次重试时才记录
                        self.log_updated.emit(f"💾 已保存异常信息: exception_{video_id}.txt")
                except:
                    pass  # 静默处理保存异常的错误
                
                retry_count += 1
                if retry_count < max_retries:
                    await asyncio.sleep(0.5)
                    continue
                else:
                    df.at[idx, '解析状态'] = '失败'
                    df.at[idx, '错误原因'] = '找不到视频，已被删除或下架'
                    self.log_updated.emit(f"[{idx+1}/{total}] ✗ 视频已删除或下架 (异常): {video_id}")
                    return
    
    async def extract_video_ids_async(self, urls):
        """异步批量提取作品ID"""
        total_urls = len(urls)
        valid_urls = urls.notna().sum()
        
        self.log_updated.emit(f"需要处理 {valid_urls}/{total_urls} 个链接...")
        
        results = []
        
        async with aiohttp.ClientSession() as session:
            # 创建信号量限制并发数
            semaphore = asyncio.Semaphore(10)  # 提高并发数为10
            
            tasks = []
            for i, url in enumerate(urls):
                if pd.notna(url):
                    task = self.extract_single_video_id_async(session, url, semaphore, i, total_urls)
                    tasks.append(task)
                else:
                    tasks.append(asyncio.create_task(self.return_none()))
            
            # 并发执行所有任务
            results = await asyncio.gather(*tasks)
        
        return results
    
    async def return_none(self):
        """返回None的异步函数"""
        return None
    
    async def extract_single_video_id_async(self, session, url, semaphore, index=0, total=0):
        """异步提取单个作品ID"""
        async with semaphore:
            # 每100个显示一次进度
            if index % 100 == 0 and total > 0:
                self.log_updated.emit(f"ID提取进度: {index}/{total}")
            if not url or not isinstance(url, str):
                return None
            
            url = url.strip()
            
            # 格式2和3: 直接从URL路径中提取
            if 'www.kuaishou.com/short-video/' in url:
                match = re.search(r'/short-video/([a-zA-Z0-9_-]+)', url)
                if match:
                    return match.group(1)
            
            # 格式1: 短链接，需要跟随重定向
            elif 'v.kuaishou.com' in url or 'kuaishou.com' in url:
                try:
                    from urllib.parse import urlparse, parse_qs
                    
                    # 使用固定的移动端User-Agent
                    mobile_user_agents = [
                        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                        'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36'
                    ]
                    import random
                    headers = {
                        'User-Agent': random.choice(mobile_user_agents),
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1'
                    }
                    
                    async with session.get(url, headers=headers, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        final_url = str(response.url)
                        
                        # 调试：记录重定向后的URL（每50个记录一次）
                        if index % 50 == 0:
                            self.log_updated.emit(f"重定向示例: {url} -> {final_url}")
                        
                        # 从重定向后的URL中提取
                        parsed = urlparse(final_url)
                        params = parse_qs(parsed.query)
                        
                        # 调试：显示所有参数（每10个记录一次）
                        if index % 10 == 0:
                            self.log_updated.emit(f"URL参数: {list(params.keys())}")
                        
                        # **优先提取字符串格式的photoId（如3xt9wjdp3xb9gpm）**
                        
                        # 1. 优先检查photoId是否为字符串格式（包含字母数字）
                        if 'photoId' in params:
                            photo_id = params['photoId'][0]
                            # 字符串格式ID通常包含字母和数字的组合
                            if not photo_id.isdigit() and len(photo_id) > 5:
                                if index % 10 == 0:
                                    self.log_updated.emit(f"✓ 使用字符串photoId: {photo_id}")
                                return photo_id
                        
                        # 2. 从路径中提取字符串格式ID（优先级高）
                        match = re.search(r'/photo/([a-zA-Z0-9_-]+)', final_url)
                        if match:
                            path_id = match.group(1)
                            if not path_id.isdigit():  # 确保是字符串格式
                                if index % 10 == 0:
                                    self.log_updated.emit(f"✓ 从路径提取: {path_id}")
                                return path_id
                        
                        # 3. 兼容原有的short-video格式
                        match = re.search(r'/short-video/([a-zA-Z0-9_-]+)', final_url)
                        if match:
                            short_id = match.group(1)
                            if index % 10 == 0:
                                self.log_updated.emit(f"✓ 从short-video提取: {short_id}")
                            return short_id
                        
                        # 4. 如果没有字符串格式，才考虑纯数字格式
                        if 'photoId' in params:
                            photo_id = params['photoId'][0]
                            if photo_id.isdigit():
                                if index % 10 == 0:
                                    self.log_updated.emit(f"✓ 使用数字photoId: {photo_id}")
                                return photo_id
                        
                        # 5. 最后尝试shareObjectId
                        if 'shareObjectId' in params:
                            share_object_id = params['shareObjectId'][0]
                            if share_object_id.isdigit():
                                if index % 10 == 0:
                                    self.log_updated.emit(f"✓ 使用shareObjectId: {share_object_id}")
                                return share_object_id
                        
                        # 如果都没找到，返回None
                        if index % 10 == 0:
                            self.log_updated.emit(f"✗ 未找到有效ID")
                        return None
                            
                except Exception as e:
                    # 静默处理错误，避免日志过多
                    pass
            
            return None
    
    def extract_json_from_html(self, html_content):
        """从HTML中提取JSON数据"""
        try:
            pattern = r'window\.INIT_STATE\s*=\s*({[\s\S]*?})\s*</script>'
            match = re.search(pattern, html_content)
            if match:
                json_str = match.group(1)
                return json.loads(json_str)
        except:
            pass
        return None
    
    def extract_video_info(self, data):
        """提取视频信息"""
        try:
            for key, value in data.items():
                if isinstance(value, dict) and 'photo' in value and 'counts' in value:
                    counts = value.get('counts', {})
                    photo = value.get('photo', {})
                    
                    # 处理发布时间
                    timestamp = photo.get('timestamp', 0)
                    publish_time = ''
                    if timestamp:
                        try:
                            dt = datetime.fromtimestamp(timestamp / 1000)
                            publish_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            publish_time = str(timestamp)
                    
                    return {
                        '粉丝数量': counts.get('fanCount', 0),
                        '收藏数量': counts.get('collectionCount', 0),
                        '作品数量': counts.get('photoCount', 0),
                        '作者ID': photo.get('userId', ''),
                        '作者名字': photo.get('userName', ''),
                        '点赞数量': photo.get('likeCount', 0),
                        '评论数量': photo.get('commentCount', 0),
                        '播放量': photo.get('viewCount', 0),
                        '分享数量': photo.get('shareCount', 0),
                        '作品文案': photo.get('caption', ''),
                        '视频时长': photo.get('duration', 0),
                        '视频宽度': photo.get('width', 0),
                        '视频高度': photo.get('height', 0),
                        '发布时间': publish_time,
                    }
        except:
            pass
        return None
    
    def prepare_output_dataframe(self, df):
        """准备输出DataFrame，按照指定格式输出"""
        # 调试：打印df的列名和数据统计
        self.log_updated.emit(f"\n准备输出数据...")
        self.log_updated.emit(f"DataFrame行数: {len(df)}")
        self.log_updated.emit(f"成功解析: {(df['解析状态'] == '成功').sum()} 条")
        self.log_updated.emit(f"失败: {(df['解析状态'] == '失败').sum()} 条")
        self.log_updated.emit(f"有作者名字的: {df['作者名字'].notna().sum()} 条")
        
        output_df = pd.DataFrame()
        
        # 1. 序号
        if '序号' in df.columns:
            output_df['序号'] = df['序号']
        else:
            output_df['序号'] = range(1, len(df) + 1)
        
        # 2. 源链接
        output_df['源链接'] = df['链接']
        
        # 3. 解析状态
        output_df['解析状态'] = df['解析状态']
        
        # 4. 错误原因
        output_df['错误原因'] = df['错误原因']
        
        # 5. 视频id (作品ID)
        output_df['视频id'] = df['作品ID']
        
        # 6. 长链接 - 根据作品ID生成
        def generate_long_url(video_id):
            if pd.notna(video_id):
                return f"https://www.kuaishou.com/short-video/{video_id}?utm_source=app_share&utm_medium=app_share&utm_campaign=app_share&location=app_share"
            return ''
        
        output_df['长链接'] = df['作品ID'].apply(generate_long_url)
        
        # 7. 文案
        output_df['文案'] = df['作品文案']
        
        # 8. 发布时间
        output_df['发布时间'] = df['发布时间']
        
        # 9. 点赞数
        output_df['点赞数'] = df['点赞数量']
        
        # 10. 评论数
        output_df['评论数'] = df['评论数量']
        
        # 11. 收藏数
        output_df['收藏数'] = df['收藏数量']
        
        # 12. 浏览量
        output_df['浏览量'] = df['播放量']
        
        # 13. 粉丝数
        output_df['粉丝数'] = df['粉丝数量']
        
        # 14. 快手昵称
        output_df['快手昵称'] = df['作者名字']
        
        # 15. 快手id
        output_df['快手id'] = df['作者ID']
        
        return output_df


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("快手视频信息爬取工具 v1.0")
        self.setGeometry(100, 100, 900, 700)
        
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 标题
        title_label = QLabel("快手视频信息批量爬取工具")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 文件选择组
        file_group = QGroupBox("文件设置")
        file_layout = QVBoxLayout()
        
        # 输入文件
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("输入文件:"))
        self.input_file_edit = QLineEdit()
        self.input_file_edit.setPlaceholderText("选择包含快手链接的Excel文件...")
        input_layout.addWidget(self.input_file_edit)
        self.input_file_btn = QPushButton("浏览")
        self.input_file_btn.clicked.connect(self.select_input_file)
        input_layout.addWidget(self.input_file_btn)
        file_layout.addLayout(input_layout)
        
        # 输出文件
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出文件:"))
        self.output_file_edit = QLineEdit()
        self.output_file_edit.setPlaceholderText("保存结果的Excel文件...")
        output_layout.addWidget(self.output_file_edit)
        self.output_file_btn = QPushButton("浏览")
        self.output_file_btn.clicked.connect(self.select_output_file)
        output_layout.addWidget(self.output_file_btn)
        file_layout.addLayout(output_layout)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # 设置组
        settings_group = QGroupBox("爬取设置")
        settings_layout = QHBoxLayout()
        
        settings_layout.addWidget(QLabel("并发数:"))
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setMinimum(1)
        self.concurrent_spin.setMaximum(50)
        self.concurrent_spin.setValue(10)
        self.concurrent_spin.setToolTip("同时请求的数量，使用代理时建议10-30，目标：1秒10条")
        settings_layout.addWidget(self.concurrent_spin)
        
        settings_layout.addWidget(QLabel("  "))
        
        # 已移除代理选项
        
        settings_layout.addStretch()
        
        # 性能提示
        perf_label = QLabel("⚡ 目标速度: 1秒10条")
        perf_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        settings_layout.addWidget(perf_label)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始爬取")
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px; padding: 10px;")
        self.start_btn.clicked.connect(self.start_task)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止")
        self.stop_btn.setStyleSheet("background-color: #f44336; color: white; font-size: 14px; padding: 10px;")
        self.stop_btn.clicked.connect(self.stop_task)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        main_layout.addLayout(button_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        
        # 日志区域
        log_label = QLabel("运行日志:")
        main_layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #f5f5f5; font-family: Consolas, monospace;")
        main_layout.addWidget(self.log_text)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
    
    def select_input_file(self):
        """选择输入文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择输入文件", "", "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.input_file_edit.setText(file_path)
            
            # 自动设置输出文件名
            if not self.output_file_edit.text():
                input_path = Path(file_path)
                output_path = input_path.parent / f"{input_path.stem}_结果.xlsx"
                self.output_file_edit.setText(str(output_path))
    
    def select_output_file(self):
        """选择输出文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择输出文件", "", "Excel Files (*.xlsx)"
        )
        if file_path:
            if not file_path.endswith('.xlsx'):
                file_path += '.xlsx'
            self.output_file_edit.setText(file_path)
    
    def start_task(self):
        """开始任务"""
        
        input_file = self.input_file_edit.text()
        output_file = self.output_file_edit.text()
        
        if not input_file:
            QMessageBox.warning(self, "警告", "请选择输入文件！")
            return
        
        if not output_file:
            QMessageBox.warning(self, "警告", "请选择输出文件！")
            return
        
        # 清空日志
        self.log_text.clear()
        self.progress_bar.setValue(0)
        
        # 创建工作线程
        url_columns = ['链接类型1', '链接类型2', '链接类型3']
        max_concurrent = self.concurrent_spin.value()
        
        self.worker = WorkerThread(input_file, url_columns, output_file, max_concurrent)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.log_updated.connect(self.append_log)
        self.worker.task_finished.connect(self.task_finished)
        self.worker.error_occurred.connect(self.task_error)
        
        # 启动线程
        self.worker.start()
        
        # 更新UI状态
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.statusBar().showMessage("正在爬取...")
    
    def stop_task(self):
        """停止任务"""
        if self.worker:
            self.worker.stop()
            self.append_log("\n⏹ 正在强制停止任务...")
            
            # 立即更新UI状态
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.statusBar().showMessage("任务已停止")
            
            # 强制终止线程（如果5秒后还没停止）
            QTimer.singleShot(5000, self.force_stop_worker)
    
    def force_stop_worker(self):
        """强制停止工作线程"""
        if self.worker and self.worker.isRunning():
            self.append_log("⚠️ 强制终止线程...")
            self.worker.terminate()
            self.worker.wait(2000)  # 等待2秒
            if self.worker.isRunning():
                self.worker.kill()  # 强制杀死
            self.worker = None
    
    def update_progress(self, current, total):
        """更新进度条"""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
            self.statusBar().showMessage(f"进度: {current}/{total} ({progress}%)")
    
    def append_log(self, message):
        """添加日志"""
        self.log_text.append(message)
        # 自动滚动到底部
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def task_finished(self, output_file):
        """任务完成"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(100)
        self.statusBar().showMessage("完成！")
        
        QMessageBox.information(
            self, "完成", 
            f"爬取完成！\n\n结果已保存到:\n{output_file}"
        )
    
    def task_error(self, error_msg):
        """任务错误"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.statusBar().showMessage("错误")
        
        QMessageBox.critical(self, "错误", error_msg)
    


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

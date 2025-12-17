import re
import json
import requests
import pandas as pd
from fake_useragent import UserAgent


def extract_json_from_html(html_content):
    """
    从HTML中提取INIT_STATE中的JSON数据
    
    参数:
        html_content: HTML内容字符串
    返回:
        解析后的JSON对象
    """
    try:
        # 查找 window.INIT_STATE = {...} 中的JSON数据
        pattern = r'window\.INIT_STATE\s*=\s*({[\s\S]*?})\s*</script>'
        match = re.search(pattern, html_content)
        
        if match:
            json_str = match.group(1)
            # 解析JSON
            data = json.loads(json_str)
            return data
        else:
            print("未找到 INIT_STATE 数据")
            return None
    except Exception as e:
        print(f"解析JSON失败: {str(e)}")
        return None


def extract_numeric_photo_id(photo, full_data):
    """
    强制提取纯数字格式的photoId
    """
    # 方法1：在整个JSON中暴力搜索所有数字格式的photoId
    def find_numeric_photo_ids(obj):
        numeric_ids = []
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == 'photoId' and value:
                    value_str = str(value)
                    if value_str.isdigit() and len(value_str) >= 15:  # 纯数字且长度合理
                        numeric_ids.append(value_str)
                elif isinstance(value, (dict, list)):
                    numeric_ids.extend(find_numeric_photo_ids(value))
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    numeric_ids.extend(find_numeric_photo_ids(item))
        return numeric_ids
    
    # 搜索所有纯数字photoId
    numeric_ids = find_numeric_photo_ids(full_data)
    
    # 如果找到纯数字ID，返回第一个
    if numeric_ids:
        return numeric_ids[0]
    
    # 方法2：如果没找到，尝试从photo对象获取并转换
    photo_id = photo.get('photoId', '')
    if photo_id:
        photo_id_str = str(photo_id)
        if photo_id_str.isdigit():
            return photo_id_str
    
    # 方法3：最后的兜底，返回字符串格式ID（至少有个ID）
    return str(photo_id) if photo_id else ''


def extract_video_info(data):
    """
    从JSON数据中提取视频信息
    
    参数:
        data: 解析后的JSON对象
    返回:
        包含视频信息的字典
    """
    try:
        # 遍历所有键，找到包含photo数据的键
        for key, value in data.items():
            if isinstance(value, dict) and 'photo' in value and 'counts' in value:
                counts = value.get('counts', {})
                photo = value.get('photo', {})
                
                # 处理发布时间（timestamp是毫秒级时间戳）
                timestamp = photo.get('timestamp', 0)
                publish_time = ''
                if timestamp:
                    try:
                        from datetime import datetime
                        # 转换毫秒时间戳为日期时间
                        dt = datetime.fromtimestamp(timestamp / 1000)
                        publish_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        publish_time = str(timestamp)
                
                info = {
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
                    '作品ID': extract_numeric_photo_id(photo, data),  # 智能提取纯数字photoId
                    '视频时长': photo.get('duration', 0),
                    '视频宽度': photo.get('width', 0),
                    '视频高度': photo.get('height', 0),
                    '发布时间': publish_time,
                }
                
                return info
        
        print("未找到有效的视频数据")
        return None
    except Exception as e:
        print(f"提取视频信息失败: {str(e)}")
        return None


def fetch_video_info_from_api(video_id):
    """
    通过快手移动端API获取视频信息
    
    参数:
        video_id: 快手作品ID
    返回:
        包含视频信息的字典
    """
    try:
        # 构建API URL
        api_url = f"https://m.gifshow.com/fw/photo/{video_id}"
        
        # 生成随机移动端 User-Agent
        ua = UserAgent(platforms='mobile')
        headers = {
            'User-Agent': ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # 发送请求
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # 从HTML中提取JSON数据
            data = extract_json_from_html(response.text)
            
            if data:
                # 提取视频信息
                info = extract_video_info(data)
                return info
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"获取视频信息失败: {str(e)}")
        return None


def parse_html_file(html_file_path):
    """
    解析本地HTML文件
    
    参数:
        html_file_path: HTML文件路径
    返回:
        包含视频信息的字典
    """
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 从HTML中提取JSON数据
        data = extract_json_from_html(html_content)
        
        if data:
            # 提取视频信息
            info = extract_video_info(data)
            return info
        
        return None
    except Exception as e:
        print(f"解析HTML文件失败: {str(e)}")
        return None


def batch_fetch_video_info(video_ids):
    """
    批量获取视频信息
    
    参数:
        video_ids: 作品ID列表
    返回:
        包含所有视频信息的DataFrame
    """
    results = []
    
    for i, video_id in enumerate(video_ids, 1):
        print(f"正在处理 {i}/{len(video_ids)}: {video_id}")
        
        info = fetch_video_info_from_api(video_id)
        
        if info:
            info['作品ID'] = video_id
            results.append(info)
            print(f"  ✓ 成功: {info['作者名字']} - {info['点赞数量']}赞")
        else:
            print(f"  ✗ 失败")
        
        # 添加延迟，避免请求过快
        import time
        time.sleep(1)
    
    # 转换为DataFrame
    if results:
        df = pd.DataFrame(results)
        return df
    else:
        return None


# 测试代码
if __name__ == "__main__":
    print("=== 测试1: 解析本地HTML文件 ===\n")
    
    html_file = "response.html"
    info = parse_html_file(html_file)
    
    if info:
        print("提取成功！")
        for key, value in info.items():
            print(f"{key}: {value}")
    else:
        print("提取失败")
    
    print("\n" + "="*50 + "\n")
    print("=== 测试2: 通过API获取视频信息 ===\n")
    
    # 测试单个视频ID
    video_id = "3xyi7vy99zwwnnw"
    info = fetch_video_info_from_api(video_id)
    
    if info:
        print("获取成功！")
        for key, value in info.items():
            print(f"{key}: {value}")
    else:
        print("获取失败")
    
    print("\n" + "="*50 + "\n")
    print("=== 测试3: 批量获取视频信息 ===\n")
    
    # 测试批量获取（可以从Excel中读取）
    # 示例：从之前的脚本生成的作品ID列表
    test_video_ids = [
        "3xyi7vy99zwwnnw",
        # 添加更多作品ID...
    ]
    
    # df = batch_fetch_video_info(test_video_ids)
    # if df is not None:
    #     df.to_excel("快手视频信息.xlsx", index=False)
    #     print(f"\n结果已保存到: 快手视频信息.xlsx")

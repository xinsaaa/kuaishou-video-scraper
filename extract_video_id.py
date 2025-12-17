import re
import requests
import pandas as pd
from urllib.parse import urlparse, parse_qs
from fake_useragent import UserAgent


def extract_video_id(url):

    
    if not url or not isinstance(url, str):
        return None
    
    url = url.strip()
    
    # 格式2和3: 直接从URL路径中提取
    if 'www.kuaishou.com/short-video/' in url:
        match = re.search(r'/short-video/([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)
    
    # 格式1: v.kuaishou.com 短链接，需要重定向获取真实链接
    elif 'v.kuaishou.com' in url:
        try:
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
            
            # 发送请求，不自动跟随重定向
            response = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
            final_url = response.url
            
            # 从重定向后的URL中提取photoId参数
            parsed = urlparse(final_url)
            params = parse_qs(parsed.query)
            
            if 'photoId' in params:
                return params['photoId'][0]
            
            # 或者从路径中提取
            match = re.search(r'/short-video/([a-zA-Z0-9_-]+)', final_url)
            if match:
                return match.group(1)
                
        except Exception as e:
            print(f"处理短链接失败 {url}: {str(e)}")
            return None
    
    return None


def build_mobile_api_url(video_id):
    """
    根据作品ID构建移动端API接口
    
    参数: video_id - 快手作品ID
    返回: 完整的移动端API URL
    """
    if not video_id:
        return None
    
    return f"https://m.gifshow.com/fw/photo/{video_id}"


def process_excel_file(input_file, output_file=None, url_column='链接'):
    """
    处理Excel文件，提取所有快手链接的作品ID并生成API接口
    
    参数:
        input_file: 输入的Excel文件路径
        output_file: 输出的Excel文件路径（可选，默认在原文件名后加_processed）
        url_column: 包含链接的列名
    """
    
    # 读取Excel文件
    df = pd.read_excel(input_file)
    
    if url_column not in df.columns:
        print(f"错误: 找不到列 '{url_column}'")
        print(f"可用的列: {df.columns.tolist()}")
        return
    
    # 提取作品ID
    print("开始提取作品ID...")
    df['作品ID'] = df[url_column].apply(extract_video_id)
    
    # 生成移动端API接口
    print("生成移动端API接口...")
    df['移动端API'] = df['作品ID'].apply(build_mobile_api_url)
    
    # 统计结果
    total = len(df)
    success = df['作品ID'].notna().sum()
    failed = total - success
    
    print(f"\n处理完成!")
    print(f"总计: {total} 条")
    print(f"成功: {success} 条")
    print(f"失败: {failed} 条")
    
    if failed > 0:
        print("\n失败的链接:")
        failed_df = df[df['作品ID'].isna()]
        for idx, row in failed_df.iterrows():
            print(f"  行 {idx + 2}: {row[url_column]}")
    
    # 保存结果
    if output_file is None:
        output_file = input_file.replace('.xlsx', '_processed.xlsx')
    
    df.to_excel(output_file, index=False)
    print(f"\n结果已保存到: {output_file}")
    
    return df


# 测试单个链接
if __name__ == "__main__":
    # 测试三种格式的链接
    test_urls = [
        "https://v.kuaishou.com/KJkZcGNA",
        "https://www.kuaishou.com/short-video/3xt9wjdp3xb9gpm",
        "https://www.kuaishou.com/short-video/3xt9wjdp3xb9gpm?cc=share_copylink&followRefer=151&shareMethod=TOKEN&docId=9&kpn=KUAISHOU&subBiz=BROWSE_SLIDE_PHOTO&photoId=3xt9wjdp3xb9gpm&shareId=18696859747094&shareToken=X-47cHeMD5AJ8134&shareResourceType=PHOTO_OTHER&userId=3xzncfss3aqb5uq&shareType=1&et=1_a%252F2009094608304373089_p0&shareMode=APP&efid=0&originShareId=18696859747094&appType=1&shareObjectId=5218546250011769629&shareUrlOpened=0&timestamp=1764523099997&utm_source=app_share&utm_medium=app_share&utm_campa"
    ]
    
    print("=== 测试单个链接提取 ===\n")
    for url in test_urls:
        video_id = extract_video_id(url)
        api_url = build_mobile_api_url(video_id)
        print(f"原始链接: {url[:80]}...")
        print(f"作品ID: {video_id}")
        print(f"移动端API: {api_url}")
        print("-" * 80)
    
    # 处理Excel文件示例
    print("\n=== 处理Excel文件 ===\n")
    
    # 请修改为你的Excel文件路径和列名
    input_file = "测试数据.xlsx"
    url_column = "链接"  # 根据实际情况修改列名
    
    try:
        df = process_excel_file(input_file, url_column=url_column)
    except FileNotFoundError:
        print(f"文件未找到: {input_file}")
        print("请修改脚本中的 input_file 变量为正确的文件路径")
    except Exception as e:
        print(f"处理出错: {str(e)}")

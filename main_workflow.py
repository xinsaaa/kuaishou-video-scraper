"""
快手视频信息完整爬取流程
1. 从Excel读取快手链接
2. 提取作品ID
3. 调用移动端API获取详细信息
4. 保存结果到Excel
"""

import time
import pandas as pd
from extract_video_id import extract_video_id, build_mobile_api_url
from parse_kuaishou_api import fetch_video_info_from_api


def process_kuaishou_links(input_file, url_columns=None, output_file=None):
    """
    处理快手链接并获取详细信息
    
    参数:
        input_file: 输入的Excel文件路径
        url_columns: 包含链接的列名列表，如 ['链接类型1', '链接类型2', '链接类型3']
        output_file: 输出的Excel文件路径（可选）
    """
    
    # 读取Excel文件
    print(f"正在读取文件: {input_file}")
    df = pd.read_excel(input_file)
    
    # 默认链接列
    if url_columns is None:
        url_columns = ['链接类型1', '链接类型2', '链接类型3']
    
    # 检查列是否存在
    available_columns = [col for col in url_columns if col in df.columns]
    if not available_columns:
        print(f"错误: 找不到任何指定的链接列")
        print(f"可用的列: {df.columns.tolist()}")
        return
    
    print(f"共找到 {len(df)} 条记录")
    print(f"使用链接列: {available_columns}\n")
    
    # 第一步：提取作品ID（从多个列中尝试）
    print("=" * 60)
    print("第一步：提取作品ID")
    print("=" * 60)
    
    # 合并所有链接列，优先使用第一个非空链接
    def get_first_valid_url(row):
        for col in available_columns:
            url = row.get(col)
            if pd.notna(url) and url:
                return url
        return None
    
    df['链接'] = df.apply(get_first_valid_url, axis=1)
    df['作品ID'] = df['链接'].apply(extract_video_id)
    df['移动端API'] = df['作品ID'].apply(build_mobile_api_url)
    
    success_count = df['作品ID'].notna().sum()
    print(f"成功提取 {success_count}/{len(df)} 个作品ID\n")
    
    # 第二步：获取详细信息
    print("=" * 60)
    print("第二步：获取视频详细信息")
    print("=" * 60)
    
    # 初始化新列 - 按照你要求的输出格式
    output_columns = {
        '昵称格式': '作者名字',
        '链接格式': '链接',
        '昵称标': '作者名字',
        '长链接': '移动端API',
        '文案': '作品文案',
        '发布时间': '发布时间',
        '点赞数': '点赞数量',
        '评论数': '评论数量',
        '收藏数': '收藏数量',
        '粉丝数': '粉丝数量',
        '作品数': '作品数量'
    }
    
    # 内部使用的列名
    info_columns = [
        '粉丝数量', '收藏数量', '作品数量', '作者ID', '作者名字',
        '点赞数量', '评论数量', '播放量', '分享数量', '作品文案',
        '视频时长', '视频宽度', '视频高度', '发布时间'
    ]
    
    for col in info_columns:
        df[col] = None
    
    # 只处理成功提取到作品ID的行
    valid_rows = df[df['作品ID'].notna()]
    
    for idx, row in valid_rows.iterrows():
        video_id = row['作品ID']
        print(f"\n处理 [{idx + 1}/{len(df)}]: {video_id}")
        
        try:
            # 获取视频信息
            info = fetch_video_info_from_api(video_id)
            
            if info:
                # 更新DataFrame
                for col in info_columns:
                    if col in info:
                        df.at[idx, col] = info[col]
                
                print(f"  ✓ 成功: {info.get('作者名字', 'N/A')} - {info.get('点赞数量', 0):,}赞 - {info.get('播放量', 0):,}播放")
            else:
                print(f"  ✗ 获取信息失败")
        
        except Exception as e:
            print(f"  ✗ 错误: {str(e)}")
        
        # 添加延迟，避免请求过快
        time.sleep(1.5)
    
    # 准备输出DataFrame - 按照要求的格式
    output_df = pd.DataFrame()
    
    # 保留序号列（如果存在）
    if '序号' in df.columns:
        output_df['序号'] = df['序号']
    
    # 按照要求的列顺序输出
    output_df['链接格式'] = df['链接']
    output_df['昵称格式'] = df['作者名字']
    output_df['链接标'] = df['链接']
    output_df['昵称标'] = df['作者名字']
    output_df['长链接'] = df['移动端API']
    output_df['文案'] = df['作品文案']
    output_df['发布时间'] = df['发布时间']
    output_df['点赞数'] = df['点赞数量']
    output_df['评论数'] = df['评论数量']
    output_df['收藏数'] = df['收藏数量']
    output_df['粉丝数'] = df['粉丝数量']
    output_df['作品数'] = df['作品数量']
    output_df['作品ID'] = df['作品ID']
    
    # 保存结果
    if output_file is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = f"快手视频详细信息_{timestamp}.xlsx"
    
    output_df.to_excel(output_file, index=False)
    
    # 统计结果
    print("\n" + "=" * 60)
    print("处理完成！")
    print("=" * 60)
    
    total = len(df)
    extracted = df['作品ID'].notna().sum()
    fetched = df['作者名字'].notna().sum()
    
    print(f"总记录数: {total}")
    print(f"成功提取作品ID: {extracted} ({extracted/total*100:.1f}%)")
    print(f"成功获取详细信息: {fetched} ({fetched/total*100:.1f}%)")
    print(f"\n结果已保存到: {output_file}")
    
    # 显示统计信息
    if fetched > 0:
        print("\n统计信息:")
        print(f"  总播放量: {df['播放量'].sum():,}")
        print(f"  总点赞数: {df['点赞数量'].sum():,}")
        print(f"  总评论数: {df['评论数量'].sum():,}")
        print(f"  平均播放量: {df['播放量'].mean():,.0f}")
        print(f"  平均点赞数: {df['点赞数量'].mean():,.0f}")
    
    return output_df


# 主程序
if __name__ == "__main__":
    # 配置参数
    input_file = "测试数据.xlsx"  # 修改为你的Excel文件名
    url_columns = ['链接类型1', '链接类型2', '链接类型3']  # 包含链接的列名列表
    
    try:
        df = process_kuaishou_links(input_file, url_columns)
    except FileNotFoundError:
        print(f"\n错误: 文件未找到 '{input_file}'")
        print("请修改脚本中的 input_file 变量为正确的文件路径")
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 AWS Bedrock Claude Haiku 4.5 翻译 Excel 文件
"""

import boto3
import json
import pandas as pd
from pathlib import Path
import time

# 配置
EXCEL_FILE = "en-jp-猫咪乐园-claude3.7--日语反馈.xlsx"
SHEET_NAME = "Sheet1"  # 可根据需要修改
SOURCE_COLUMN = "Content"  # 源文本列
TARGET_COLUMN = "Claude Haiku 4.5"  # 翻译结果列（第8列）
MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"  # Claude Haiku 4.5
REGION = "us-east-1"  # 根据您的区域修改


def translate_text(bedrock_client, text, source_lang="英语", target_lang="日语"):
    """
    使用 Bedrock Claude 翻译文本
    """
    if not text or pd.isna(text):
        return ""
    
    prompt = f"""请将以下{source_lang}文本翻译成{target_lang}。
只返回翻译结果，不要添加任何解释或额外内容。

文本：
{text}

翻译："""
    
    # 构建请求体
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3
    }
    
    try:
        # 调用 Bedrock API
        response = bedrock_client.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(request_body)
        )
        
        # 解析响应
        response_body = json.loads(response['body'].read())
        translated_text = response_body['content'][0]['text'].strip()
        
        return translated_text
    
    except Exception as e:
        print(f"翻译出错: {str(e)}")
        return f"ERROR: {str(e)}"


def main():
    """
    主函数
    """
    # 检查文件是否存在
    excel_path = Path(EXCEL_FILE)
    if not excel_path.exists():
        print(f"错误：找不到文件 {EXCEL_FILE}")
        return
    
    print(f"正在读取 Excel 文件: {EXCEL_FILE}")
    
    # 读取 Excel 文件
    try:
        df = pd.read_excel(excel_path, sheet_name=SHEET_NAME)
    except Exception as e:
        print(f"读取 Excel 文件失败: {str(e)}")
        # 尝试读取第一个 sheet
        try:
            df = pd.read_excel(excel_path)
            print("使用默认 sheet")
        except Exception as e2:
            print(f"无法读取文件: {str(e2)}")
            return
    
    print(f"读取到 {len(df)} 行数据")
    
    # 检查源列是否存在
    if SOURCE_COLUMN not in df.columns:
        print(f"错误：找不到列 '{SOURCE_COLUMN}'")
        print(f"可用的列: {list(df.columns)}")
        return
    
    # 初始化 Bedrock 客户端
    print(f"初始化 AWS Bedrock 客户端 (区域: {REGION})")
    try:
        bedrock_client = boto3.client(
            service_name='bedrock-runtime',
            region_name=REGION
        )
    except Exception as e:
        print(f"初始化 Bedrock 客户端失败: {str(e)}")
        print("请确保已配置 AWS 凭证 (aws configure)")
        return
    
    # 确保目标列存在
    if TARGET_COLUMN not in df.columns:
        df[TARGET_COLUMN] = ""
    
    # 翻译每一行
    total_rows = len(df)
    translated_count = 0
    
    print(f"\n开始翻译，使用模型: {MODEL_ID}")
    print("-" * 60)
    
    for index, row in df.iterrows():
        source_text = row[SOURCE_COLUMN]
        
        # 跳过空值
        if pd.isna(source_text) or str(source_text).strip() == "":
            continue
        
        print(f"[{index + 1}/{total_rows}] 翻译中...")
        print(f"源文本: {str(source_text)[:50]}...")
        
        # 调用翻译
        translated = translate_text(bedrock_client, source_text)
        df.at[index, TARGET_COLUMN] = translated
        
        print(f"译文: {translated[:50]}...")
        print()
        
        translated_count += 1
        
        # 添加延迟以避免速率限制
        time.sleep(0.5)
    
    # 保存结果
    output_file = excel_path.stem + "_translated.xlsx"
    output_path = excel_path.parent / output_file
    
    print("-" * 60)
    print(f"保存翻译结果到: {output_path}")
    
    try:
        df.to_excel(output_path, sheet_name=SHEET_NAME, index=False)
        print(f"✓ 成功翻译 {translated_count} 条记录")
        print(f"✓ 结果已保存到: {output_path}")
    except Exception as e:
        print(f"保存文件失败: {str(e)}")


if __name__ == "__main__":
    main()


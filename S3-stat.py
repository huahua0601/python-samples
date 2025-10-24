#!/usr/bin/env python3
"""
AWS S3 存储桶大小统计脚本
统计AWS账户下所有S3存储桶的总大小（使用CloudWatch指标）
注意：CloudWatch指标可能有24小时延迟
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from datetime import datetime


def get_bucket_region(s3_client, bucket_name):
    """
    获取存储桶所在的区域
    
    Args:
        s3_client: boto3 S3客户端
        bucket_name: 存储桶名称
        
    Returns:
        区域名称
    """
    try:
        response = s3_client.get_bucket_location(Bucket=bucket_name)
        # LocationConstraint为None表示us-east-1
        region = response['LocationConstraint']
        if region is None:
            region = 'us-east-1'
        return region
    except ClientError as e:
        print(f"  警告: 无法获取存储桶 {bucket_name} 的区域: {e}")
        return 'us-east-1'


def get_bucket_size(s3_client, bucket_name, bucket_region, cloudwatch_clients):
    """
    获取指定S3存储桶的大小（使用CloudWatch指标）
    
    Args:
        s3_client: boto3 S3客户端
        bucket_name: 存储桶名称
        bucket_region: 存储桶所在区域
        cloudwatch_clients: CloudWatch客户端字典（按区域）
        
    Returns:
        存储桶大小（字节）
    """
    try:
        from datetime import timedelta
        
        # 获取或创建该区域的CloudWatch客户端
        if bucket_region not in cloudwatch_clients:
            cloudwatch_clients[bucket_region] = boto3.client('cloudwatch', region_name=bucket_region)
        
        cloudwatch_client = cloudwatch_clients[bucket_region]
        
        # CloudWatch指标有延迟，查询过去3天的数据
        end_time = datetime.now()
        start_time = end_time - timedelta(days=3)
        
        # 所有可能的存储类型
        storage_types = [
            'StandardStorage',
            'StandardIAStorage',  # Standard-IA
            'IntelligentTieringFAStorage',  # Intelligent-Tiering
            'IntelligentTieringIAStorage',
            'IntelligentTieringAAStorage',
            'IntelligentTieringAIAStorage',
            'IntelligentTieringDAAStorage',
            'OneZoneIAStorage',  # One Zone-IA
            'ReducedRedundancyStorage',  # RRS
            'GlacierInstantRetrievalStorage',  # Glacier Instant Retrieval
            'GlacierStorage',  # Glacier Flexible Retrieval
            'DeepArchiveStorage',  # Glacier Deep Archive
            'GlacierStagingStorage',
            'GlacierObjectOverhead',
            'GlacierS3ObjectOverhead'
        ]
        
        total_size = 0
        
        for storage_type in storage_types:
            try:
                response = cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/S3',
                    MetricName='BucketSizeBytes',
                    Dimensions=[
                        {'Name': 'BucketName', 'Value': bucket_name},
                        {'Name': 'StorageType', 'Value': storage_type}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=86400,  # 24小时
                    Statistics=['Average']
                )
                
                if response['Datapoints']:
                    # 获取最新的数据点
                    datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'], reverse=True)
                    if datapoints:
                        total_size += datapoints[0]['Average']
            except ClientError:
                # 某些存储类型可能不适用，忽略错误
                continue
        
        return total_size
    except Exception as e:
        print(f"  警告: 无法通过CloudWatch获取存储桶 {bucket_name} 的大小: {e}")
        return 0


def format_size(size_bytes):
    """
    将字节大小格式化为人类可读的格式
    
    Args:
        size_bytes: 字节大小
        
    Returns:
        格式化后的字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} EB"


def main():
    """主函数"""
    print("=" * 60)
    print("AWS S3 存储桶大小统计")
    print("=" * 60)
    print()
    
    try:
        # 创建AWS客户端
        s3_client = boto3.client('s3')
        # CloudWatch客户端字典，按区域缓存
        cloudwatch_clients = {}
        
        # 获取所有存储桶列表
        print("正在获取所有S3存储桶列表...")
        response = s3_client.list_buckets()
        buckets = response['Buckets']
        
        if not buckets:
            print("未找到任何S3存储桶。")
            return
        
        print(f"找到 {len(buckets)} 个存储桶\n")
        
        total_size = 0
        bucket_sizes = []
        
        print("使用CloudWatch指标获取存储桶大小...")
        print("注意：CloudWatch指标可能有24小时延迟\n")
        
        # 统计每个存储桶的大小
        for i, bucket in enumerate(buckets, 1):
            bucket_name = bucket['Name']
            print(f"[{i}/{len(buckets)}] 正在处理: {bucket_name}")
            
            # 获取存储桶所在区域
            bucket_region = get_bucket_region(s3_client, bucket_name)
            print(f"  区域: {bucket_region}")
            
            # 使用CloudWatch方法（自动使用对应区域的客户端）
            size = get_bucket_size(s3_client, bucket_name, bucket_region, cloudwatch_clients)
            
            bucket_sizes.append({
                'name': bucket_name,
                'size': size,
                'region': bucket_region,
                'created': bucket['CreationDate']
            })
            total_size += size
            
            print(f"  大小: {format_size(size)}")
            print()
        
        # 输出结果
        print("=" * 60)
        print("统计结果")
        print("=" * 60)
        print()
        
        # 按大小排序
        bucket_sizes.sort(key=lambda x: x['size'], reverse=True)
        
        print("存储桶详情（按大小排序）:")
        print("-" * 60)
        for item in bucket_sizes:
            print(f"存储桶: {item['name']}")
            print(f"  区域: {item['region']}")
            print(f"  大小: {format_size(item['size'])}")
            print(f"  创建时间: {item['created'].strftime('%Y-%m-%d %H:%M:%S')}")
            print()
        
        # 按区域统计
        region_stats = {}
        for item in bucket_sizes:
            region = item['region']
            if region not in region_stats:
                region_stats[region] = {'count': 0, 'size': 0}
            region_stats[region]['count'] += 1
            region_stats[region]['size'] += item['size']
        
        print("=" * 60)
        print("按区域统计:")
        print("-" * 60)
        for region in sorted(region_stats.keys()):
            stats = region_stats[region]
            print(f"区域: {region}")
            print(f"  存储桶数量: {stats['count']}")
            print(f"  总大小: {format_size(stats['size'])}")
            print()
        
        print("=" * 60)
        print(f"总存储桶数量: {len(buckets)}")
        print(f"涉及区域数量: {len(region_stats)}")
        print(f"总存储大小: {format_size(total_size)}")
        print(f"总存储大小（字节）: {total_size:,}")
        print("=" * 60)
        
    except NoCredentialsError:
        print("错误: 未找到AWS凭证。")
        print("请确保已配置AWS凭证（通过 aws configure 或环境变量）。")
    except ClientError as e:
        print(f"错误: {e}")
    except Exception as e:
        print(f"发生未预期的错误: {e}")


if __name__ == "__main__":
    main()


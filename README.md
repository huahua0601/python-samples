# Excel 翻译工具 - AWS Bedrock Claude Haiku 4.5

使用 AWS Bedrock 的 Claude Haiku 4.5 模型将 Excel 文件中的内容翻译成日语。

## 功能特性

- 🚀 使用最新的 Claude Haiku 4.5 模型
- 📊 读取 Excel 文件的指定列
- 🇯🇵 自动翻译成日语
- 💾 保存翻译结果到新的 Excel 文件

## 前置要求

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 AWS 凭证

确保已配置 AWS CLI 凭证：

```bash
aws configure
```

需要提供：
- AWS Access Key ID
- AWS Secret Access Key
- Default region (建议: us-east-1)

### 3. AWS Bedrock 权限

确保您的 AWS IAM 用户/角色具有以下权限：
- `bedrock:InvokeModel`
- 访问 Claude Haiku 4.5 模型的权限

### 4. 启用 Claude Haiku 4.5 模型

在 AWS Bedrock 控制台中启用 Claude Haiku 4.5 模型：
1. 登录 AWS 控制台
2. 进入 Bedrock 服务
3. 点击 "Model access"
4. 启用 "Claude Haiku 4.5" 模型

## 使用方法

### 基本使用

```bash
python translate.py
```

### 配置说明

在 `translate.py` 文件顶部修改以下配置：

```python
EXCEL_FILE = "your-file.xlsx"     # Excel 文件名
SHEET_NAME = "Sheet1"              # 工作表名称
SOURCE_COLUMN = "content"          # 源文本列名
TARGET_COLUMN = "H"                # 翻译结果列名（第8列）
REGION = "us-east-1"               # AWS 区域
```

### 输出

脚本会生成一个新文件：`原文件名_translated.xlsx`

## 注意事项

1. **费用**: 使用 AWS Bedrock 会产生费用，请查看 [AWS Bedrock 定价](https://aws.amazon.com/bedrock/pricing/)
2. **速率限制**: 脚本包含延迟机制，避免触发 API 速率限制
3. **模型可用性**: Claude Haiku 4.5 可能不是在所有区域都可用，建议使用 `us-east-1`

## 故障排查

### 找不到列错误
检查 Excel 文件中的列名是否正确，脚本会显示所有可用的列名。

### AWS 凭证错误
运行 `aws configure` 重新配置凭证，或设置环境变量：
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### 模型访问错误
确保在 AWS Bedrock 控制台中已启用 Claude Haiku 4.5 模型访问权限。

## 示例

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 AWS
aws configure

# 3. 运行翻译
python translate.py
```

## 支持的翻译

当前配置：英语 → 日语

可以修改 `translate_text` 函数中的 `source_lang` 和 `target_lang` 参数来支持其他语言对。


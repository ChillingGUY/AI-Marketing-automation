# AI营销自动化平台 - 营销数据分析模块

基于给定架构，实现营销数据分析模块的**数据采集**与**ETL 处理**。

📖 **实战上手**：[实战使用文档](docs/实战使用文档.md) | 完整说明：[使用手册](docs/使用手册.md)

## 项目目标

- 减少重复工作
- 提升创意产出
- 自动分析内容趋势
- 构建公司知识库
- 提高营销效率

## 模块功能

### 系统自动

| 阶段 | 内容 |
|------|------|
| **抓取** | 热门视频、点赞、播放、评论、发布时间、标签 |
| **分析** | 热门内容结构、视频时长、话题趋势、BGM趋势、脚本套路 |
| **输出** | 今日热门视频榜、热门创意拆解、爆款内容模型 |
| **最终** | AI推荐内容 |

### 数据来源（非爬虫）

- **TikTok 热门视频**：通过 [TikHub](https://tikhub.io) API 获取，不使用爬虫
- **CSV / API / 手动导入**：支持从 CSV 导入补充数据

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，按需配置：

| 变量 | 说明 |
|------|------|
| TIKHUB_API_TOKEN | TikHub API（https://tikhub.io） |
| OPENAI_API_KEY | LLM 分析（可选） |
| FEISHU_APP_ID/SECRET/CHAT_ID | 飞书推送（可选） |

### 3. 按顺序执行完整流程

```bash
python run_all.py
```

将依次执行：
1. 数据采集（TikTok 热门视频 / CSV 示例）
2. ETL 处理
3. AI 分析（热门拆解、爆款结构、创意生成）
4. 提示启动看板
5. 飞书推送（若已配置）

### 4. 营销平台（看板 + 创意工具 + 爆款库）

```bash
streamlit run dashboard.py
```

- 主页：热门趋势看板
- 创意生成工具：输入主题生成 AI 创意与脚本
- 爆款内容库：按标签检索热门拆解

### 5. 定时任务（每日 09:00 自动执行）

```bash
pip install schedule
python scheduler.py
```

### 6. 单独运行数据采集

```bash
python main.py
```

## 目录结构

```
d:\yingxiao\
├── config.py              # 配置
├── main.py                # 主入口
├── requirements.txt
├── .env.example           # 环境变量示例
├── data/                  # 数据目录
│   ├── raw/               # 原始数据 CSV
│   └── processed/         # 处理后数据 CSV
└── src/
    ├── models/            # 数据模型
    │   └── video.py
    ├── data_source/       # 数据来源层
    │   ├── tiktok_fetcher.py   # TikTok 热门视频抓取
    │   └── csv_import.py       # CSV 导入
    └── data_processing/   # 数据处理层
        └── etl.py
```

## 架构对应

| 架构层 | 实现 |
|--------|------|
| 数据来源层 | TikHub API（TikTok 趋势）、CSV 导入 |
| 数据处理层 | ETL（Python + Pandas）|
| AI分析层 | 待实现 |
| AI Agent / 营销平台 / 自动化 | 待实现 |

## 配置说明

在 `config.py` 中可调整：

- `FETCH_CONFIG.period`：抓取时间范围（天）
- `FETCH_CONFIG.order_by`：排序方式（vv / like / comment / repost）
- `FETCH_CONFIG.country_code`：国家/地区
- `FETCH_CONFIG.enrich_metrics`：是否拉取每个视频的详细统计

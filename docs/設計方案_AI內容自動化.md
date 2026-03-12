# AI 營銷自動化平台 — 設計方案

> **設計目標**：把內容策劃、腳本生成、視頻製作、趨勢分析等流程自動化，並通過企業協作平台分發給員工使用。

---

## 一、總體架構

整體採用 **多 Agent + 工作流編排** 架構。

| 層級 | 技術棧 | 職責 |
|------|--------|------|
| **Frontend (Web)** | Next.js / Vue | 用戶介面 |
| **Backend API** | FastAPI | 業務邏輯、請求處理 |
| **Agent Orchestrator** | 工作流編排 | 任務調度、狀態管理 |
| **LLM Engine** | Prompt / RAG | 檢索增強生成 |
| **Tools Layer** | 視頻/數據 API | 外部工具介面 |
| **Data Layer** | PostgreSQL | 持久化存儲 |
| **Message Queue** | Redis / Celery | 異步任務、解耦 |

---

## 二、AI 流程

```
趨勢數據 → 分析 → 創意策劃 → 腳本 → 視頻生成 → 發布
```

完整流水線：**Trend → Strategy → Script → Video → Edit → Score → Publish**

---

## 三、Agent 設計（8 個核心 Agent）

### 1 趨勢分析 Agent (Trend Agent)
| 項目 | 內容 |
|------|------|
| **輸入** | 熱門視頻、播放量、點贊率、評論率 |
| **輸出** | 爆款結構、熱門主題、創意方向 |
| **數據來源** | TikTok |

### 2 內容策略 Agent (Strategy Agent)
| 項目 | 內容 |
|------|------|
| **作用** | 根據趨勢生成營銷策略 |
| **輸出** | 內容主題、視頻方向、營銷定位 |
| **示例** | 目標用戶：打工人 → 策略：辦公室喜劇短視頻 |

### 3 腳本生成 Agent (Script Agent)
| 項目 | 內容 |
|------|------|
| **輸入** | 主題、產品、用戶畫像 |
| **輸出** | 標題、分鏡、台詞、拍攝建議 |

### 4 影片生成 Agent (Video Agent)
| 項目 | 內容 |
|------|------|
| **輸入** | 腳本 |
| **輸出** | 影片 |
| **可調用模型** | Runway Gen-3、Kling AI |

### 5 剪輯 Agent (Edit Agent)
| 項目 | 內容 |
|------|------|
| **職責** | 素材拼接、字幕、BGM、節奏剪輯 |
| **技術** | ffmpeg、moviepy |

### 6 內容評分 Agent (Score Agent)
| 項目 | 內容 |
|------|------|
| **分析維度** | 創意評分、營銷價值、傳播潛力 |
| **輸出** | 綜合評分 (score) |

### 7 發布 Agent (Publish Agent)
| 項目 | 內容 |
|------|------|
| **對接** | 飛書 (Feishu) |
| **功能** | 自動推送視頻、發送運營建議 |

### 8 數據復盤 Agent (Review Agent)
| 項目 | 內容 |
|------|------|
| **職責** | 分析播放數據、優化內容 |
| **輸出** | 下一輪策略 |

---

## 四、Agent 工作流

```
Trend Agent
    ↓
Strategy Agent
    ↓
Script Agent
    ↓
Video Agent
    ↓
Edit Agent
    ↓
Score Agent
    ↓
Publish Agent
```

即：**完整 AI 內容生產流水線**。

---

## 五、Agent 編排框架

**推薦工具**：LangChain、LangGraph（以 LangGraph 為主）

**LangGraph 能力**：Agent 流程圖、狀態管理、條件分支

**示例流程**：`Trend → Strategy → Script → Video`

**Python 示例**：
```python
from langgraph.graph import StateGraph

workflow = StateGraph()
workflow.add_node("trend_agent", trend_agent)
workflow.add_node("strategy_agent", strategy_agent)
workflow.add_node("script_agent", script_agent)
workflow.add_edge("trend_agent", "strategy_agent")
workflow.add_edge("strategy_agent", "script_agent")
app = workflow.compile()
```

---

## 六、資料庫設計

### trends 表（趨勢）
| 欄位 | 說明 |
|------|------|
| id | 主鍵 |
| platform | 平台（TikTok 等）|
| video_url | 視頻 URL |
| likes | 點贊數 |
| comments | 評論數 |
| views | 播放量 |
| topic | 主題標籤 |

### scripts 表（腳本）
| 欄位 | 說明 |
|------|------|
| id | 主鍵 |
| title | 標題 |
| hook | 開頭吸引點 |
| script | 完整腳本 |
| scene | 場景 |
| industry | 行業 |

### videos 表（影片）
| 欄位 | 說明 |
|------|------|
| id | 主鍵 |
| script_id | 關聯 scripts.id |
| video_url | 影片 URL |
| score | 評分 |
| created_at | 建立時間 |

### agents_log 表（代理日誌）
| 欄位 | 說明 |
|------|------|
| agent_name | 代理名稱 |
| task | 任務內容 |
| result | 執行結果 |
| time | 執行時間 |

---

## 七、平台功能模組

平台 UI 規劃 5 個模組：

| 模組 | 子功能 |
|------|--------|
| **1 趨勢分析** | 熱門視頻、爆款結構 |
| **2 創意中心** | 生成營銷創意 |
| **3 腳本中心** | AI 腳本、腳本編輯 |
| **4 視頻生成** | 腳本 → 視頻 |
| **5 數據分析** | 內容評分、傳播預測 |

---

## 八、企業使用流程

**公司員工使用方式**：
1. 輸入產品
2. 選擇行業
3. AI 生成腳本
4. AI 生成視頻
5. 發布

**效率**：約 **10 分鐘** 完成一個視頻

---

## 九、商業價值

| 痛點 | 解決方案 |
|------|----------|
| 創意 | AI 輔助創意與內容策劃 |
| 效率 | 腳本、視頻自動化生成 |
| 內容生產 | 1 天可生成約 **100 條** 內容 |

**核心價值**：**AI 內容工廠** — 全流程自動化、企業協作分發。

---

## 與現有實現對應

| 新設計 | 現有實現 | 狀態 |
|--------|----------|------|
| 趨勢分析 Agent | tiktok_fetcher + ai_analysis | ✅ 部分實現 |
| 內容策略 / 創意 | 創意生成工具、爆款模型 | ✅ 部分實現 |
| 腳本生成 Agent | 創意生成、腳本輸出 | ✅ 部分實現 |
| 影片生成 Agent | - | ⏳ 待實現 |
| 剪輯 Agent | - | ⏳ 待實現 |
| 內容評分 Agent | - | ⏳ 待實現 |
| 發布 Agent | 飛書推送 | ✅ 部分實現 |
| 數據復盤 Agent | - | ⏳ 待實現 |
| Agent 編排 | workflow.py、marketing_agent | ✅ 基礎架構 |
| RAG / 知識庫 | ChromaDB、爆款庫 | ✅ 已實現 |

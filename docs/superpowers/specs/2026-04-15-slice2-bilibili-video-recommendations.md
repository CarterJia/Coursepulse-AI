# Slice 2 — B站视频推荐

> 报告生成后，为每个 topic 自动搜索 B站教育短视频，按 embedding 相似度过滤，只在匹配度高的 topic 下展示。

## 触发时机

Pipeline 尾部追加（方案 A）：上传 PDF → 解析 → 生成报告 → 自动搜视频 → 全部完成。用户打开报告时视频已经在了。

## 数据流

1. Pass-1 plan JSON 每个 topic 新增 `search_keywords` 字段（2-3 个关键词）
2. Pipeline 尾部对每个 topic：
   - 用 keywords + 随机教育后缀（讲解/教程/详解/入门）构造搜索 query
   - 调 B站公开搜索接口 `https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword=...`
   - 取前 5-10 条候选
3. 规则过滤：时长 <10 分钟，播放量 >1 万
4. Embedding 相似度：用 `bge-small-zh`（已有的本地模型）算 topic key_points 与视频标题+简介的余弦相似度
5. 存所有通过规则过滤的候选到 DB（含 similarity_score）
6. 前端取 top 2 展示；后续根据真实数据分布设定阈值裁剪

## 搜索策略

- 后缀轮换：每个 keyword 随机选一个后缀（讲解/教程/详解/入门），避免搜出同一批视频
- 跨 topic 去重：同一个 bvid 只保留相似度最高的那条
- B站接口不需要 API key，无配额限制

## 相似度阈值

初期不设硬阈值，所有通过规则过滤的候选都存 DB（带 similarity_score）。用户上传几份真实课件后，观察分数分布，再根据实际数据确定阈值。

## 新表 `video_recommendations`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | PK |
| document_id | UUID | FK → documents |
| topic_title | String | 关联的 topic 标题 |
| bilibili_url | String | 视频链接 |
| bvid | String | B站视频唯一 ID（去重用） |
| title | String | 视频标题 |
| description | Text | 视频简介（用于 embedding） |
| cover_url | String | 封面图 URL |
| up_name | String | UP 主名称 |
| duration_seconds | Integer | 时长（秒） |
| play_count | Integer | 播放量 |
| similarity_score | Float | embedding 余弦相似度 |

## 后端变更

| 文件 | 变更 |
|------|------|
| `services/prompts.py` | Pass-1 plan schema 加 `search_keywords` 字段 |
| `services/report_planner.py` | 校验新字段 |
| `services/bilibili.py`（新） | B站搜索 API 封装 + 规则过滤（时长/播放量） |
| `services/video_recommender.py`（新） | Embedding 相似度计算 + 排序 + 写 DB |
| `services/reporting.py` | pipeline 尾部调用视频推荐 |
| `models/video_recommendation.py`（新） | SQLAlchemy 模型 |
| `api/routes/videos.py`（新） | `GET /api/documents/{id}/videos` |
| `alembic/versions/xxxx_video_recommendations.py`（新） | 建表迁移 |

## API

### `GET /api/documents/{document_id}/videos`

返回该文档所有推荐视频，按 topic 分组：

```json
[
  {
    "topic_title": "MCTS 核心算法",
    "videos": [
      {
        "title": "蒙特卡洛树搜索 MCTS 详解",
        "bilibili_url": "https://www.bilibili.com/video/BVxxxxxxx",
        "cover_url": "https://...",
        "up_name": "某教育UP主",
        "duration_seconds": 480,
        "play_count": 52000,
        "similarity_score": 0.82
      }
    ]
  }
]
```

## 前端变更

- 报告页每个 topic 折叠卡片（Accordion）底部：如果该 topic 有推荐视频，展示视频卡片区域
- 视频卡片：封面缩略图 + 标题 + UP 主 + 时长 badge + 播放量
- 点击整张卡片跳转 B站（新标签页）
- 无视频的 topic 不显示任何视频相关 UI

## 降级策略

- B站接口超时/报错 → 该 topic 跳过视频搜索，不阻塞 pipeline，日志记录
- 搜索无结果 / 全部被规则过滤掉 → 该 topic 无视频记录，前端静默
- 单个 topic 的视频搜索失败不影响其他 topic

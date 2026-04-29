# AI短剧制作平台 Demo

本项目是一个 AI短剧制作平台 Demo，模拟从内容策划、剧本打磨、AI分镜、多语种本地化、素材上传与视频预览，到广告素材生成和增长分析的完整短剧生产链路。

当前重点是展示一个可运行、可扩展、可讲解的 AI 内容生产 SaaS 原型。

## 首页看板升级

首页看板已从旧的生成链路 ID 展示，升级为 `Project + Episode + Assets` 生产工作台。

首页现在展示短剧项目数、分集数量、AI分镜数、本地化版本数、媒体资产数和广告素材数，并提供项目生产阶段分布、分集生产状态、最近项目、最近分集和新的生产链路说明。

当前生产链路以 `projectId + episodeId` 为核心：`projectId` 负责整部短剧归属，`episodeId` 负责具体单集生产归属。生成页负责生产，列表页负责资产沉淀，项目详情页和分集管理页负责生产调度。

这更符合真实短剧系统中“项目 → 分集 → 资产沉淀 → 增长分析”的管理方式。

## 短剧项目管理

本次新增 `ShortDramaProject` 作为业务主线，用于承载短剧项目的名称、题材、目标市场、主语言、计划集数、当前阶段、负责人、优先级和状态。

后续内容策划、剧本打磨、AI分镜、本地化、广告素材和媒体资源都会逐步通过 `projectId` 绑定到短剧项目，让系统从单点 AI 生成工具升级为更接近真实业务的短剧制作管理系统。

前端新增 `/projects` 页面，支持项目列表、新建、编辑和归档。后端新增 `/api/projects` 系列接口，并在项目表为空时自动插入 3 条面试演示数据，避免首次演示页面空白。

如果本地旧数据库结构不兼容，可以删除 `backend/data/app.db` 后重启后端，系统会自动重建表。是否插入演示项目和演示分集由 `ENABLE_DEMO_SEED` 控制。

## 演示数据 Seed 开关

后端支持通过环境变量控制是否自动插入面试演示数据：

- `ENABLE_DEMO_SEED=true`：默认值。删除 `backend/data/app.db` 后重启后端，会自动建表，并在项目表、分集表为空时插入演示项目和演示分集，适合面试演示。
- `ENABLE_DEMO_SEED=false`：删除 `backend/data/app.db` 后重启后端，只执行 `create_all` 建表和轻量字段补齐，不插入任何演示数据，适合调试空数据库流程。

该开关不影响已有接口和数据库结构，只控制启动时是否执行 demo seed。

## 短剧项目详情与生产链路

`/projects` 是短剧项目列表，`/projects/:id` 是短剧项目详情页。

项目详情页展示项目基础信息、统计数据、AI生产链路、最近数据和快捷入口，相当于一个短剧项目的生产工作台。快捷入口会携带 `projectId` 跳转到内容策划、剧本打磨、AI分镜、本地化、广告素材、媒体资产和增长分析页面。

后端新增 `/api/projects/{project_id}/overview` 聚合接口。当前 overview 先兼容旧数据结构，后续会逐步把内容策划、剧本打磨、AI分镜、本地化、广告素材、媒体资产通过 `projectId` 真实绑定。

面试讲解重点：`projectId` 是串联 AI 短剧生产链路的数据主键，这一步让系统从项目列表进一步升级为完整业务管理系统。

## 生成页绑定 projectId

内容策划、剧本打磨、AI分镜、多语种本地化、广告素材和媒体资产页面已经支持选择短剧项目。

从项目详情页进入这些页面时，会通过 `?projectId=xxx` 自动选中项目。生成或上传成功后，结果会带 `project_id` 保存，项目 overview 可以优先按 `project_id` 统计真实项目数据。

当前 `project_id` 采用 nullable 弱关联，兼容旧 demo 数据，不强制外键约束。如果旧 SQLite 表缺少 `project_id` 字段导致报错，可以删除 `backend/data/app.db` 后重启自动重建；当前项目也提供了轻量字段补齐逻辑，正常情况下不需要删除数据库。

## ProjectPicker 项目选择器

生成页使用 `ProjectPicker` 弹窗选择短剧项目。相比普通下拉框，弹窗可以展示项目名称、题材、目标市场、主语言、集数、阶段和状态，更适合真实业务系统中项目数量较多的场景。

选择短剧项目后，生成结果仍然通过 `project_id` 绑定到对应项目；从项目详情页或分集管理页携带 `?projectId=xxx` 进入时，组件会自动回显项目信息。列表页筛选仍保留下拉筛选，避免普通查询场景操作过重。

## EpisodePicker 分集选择器

分集级生产页使用 `EpisodePicker` 选择具体集数。`ProjectPicker` 先选择短剧项目，`EpisodePicker` 再根据 `projectId` 加载该项目下的分集，避免分镜、本地化和媒体资产生成后无法归属到具体 Episode。

AI分镜、本地化、媒体资产必须选择分集后才能继续生产；广告素材同时支持项目级和分集级两种模式，因此 `episodeId` 可选。从分集管理页进入时，URL 会自动携带 `projectId`、`episodeId`、`episodeNo` 并在页面回显。

## 分集大纲 / 分集拆解

内容策划是项目级能力，用来确定整部短剧方向；分集大纲负责把项目级策划拆成多集 Episode，形成“内容策划 → 分集管理 → 分集级生产”的真实链路。

系统支持从内容策划结果一键生成分集大纲，生成后的标题、剧情摘要、阶段和状态会写入分集管理。AI 或规则生成的是初稿，运营或编剧可以逐集调整分集标题、剧情摘要、阶段和状态，调整完成后再进入分集级剧本打磨、AI分镜、本地化、媒体资产和广告素材生产。

当前分集大纲生成优先保证稳定演示：后端优先使用 DeepSeek 生成并写入 `short_drama_episodes`，DeepSeek 不可用或返回异常时自动使用规则 fallback，避免 AI 调用失败影响现场演示。

分集大纲是内部生产稿，`title` 和 `summary` 均统一中文输出。目标市场只影响剧情偏好、爽点设计和投放节奏，不影响大纲输出语言；目标语言版本在后续本地化阶段生成。

## 分集大纲 DeepSeek 生成

分集大纲生成支持 DeepSeek 优先。后端会根据短剧项目信息、内容策划输入和内容策划结果，请求 DeepSeek 生成多集大纲，并校验返回的 JSON 结构、集数、集号、标题和摘要字段。

如果 DeepSeek 未启用、未配置 `AI_API_KEY`、调用失败或返回格式不合法，接口会自动使用规则生成 fallback，并返回 `generation_source=rule_fallback`；DeepSeek 成功时返回 `generation_source=deepseek`。这样既能提升生成质量，也保证面试演示和本地开发稳定。

该能力复用现有 AI 配置：`AI_PROVIDER=deepseek`、`AI_API_KEY`、`AI_BASE_URL`、`AI_MODEL`、`AI_TEMPERATURE`、`AI_MAX_TOKENS`、`AI_TIMEOUT`。本地演示可保持 `AI_PROVIDER=mock`，无需真实 Key。

## 业务字典模块

系统新增 `/api/dictionaries` 字典接口，统一提供目标市场、语言、题材、项目阶段、项目状态和优先级等业务选项。

前端通过 `useDictionaries` 统一加载和缓存字典，短剧项目管理、ProjectPicker、内容策划、本地化和广告素材等页面都复用同一套字典数据。字典接口异常时会使用前端 fallback，保证本地和面试演示稳定。

当前字典先使用后端静态配置集中管理，后续可以升级为数据库字典表或配置中心。这样可以避免不同页面各自写死下拉选项，导致市场、语言、阶段等字段不一致。

## 字典管理页面

系统配置下新增字典管理页面，用于只读查看当前业务字典配置，包括市场、语言、题材、阶段、状态和优先级。

当前字典来自后端静态配置，页面通过现有 `/api/dictionaries` 接口加载；接口异常时会展示前端 fallback 字典，保证本地演示稳定。

后续可升级为数据库字典表，实现在线新增、编辑、停用字典项，或接入配置中心统一管理业务选项。

## 全链路 projectId 绑定

当前内容策划、剧本打磨、AI分镜、多语种本地化、广告素材、媒体资产都已经支持 `project_id`。从短剧项目详情页进入各生产页面时，会通过 `?projectId=xxx` 自动选中项目；用户也可以在页面顶部手动选择所属短剧项目。

生成或上传成功后，结果会归属到对应短剧项目，overview 会优先按 `project_id` 统计真实数据。本地化完成后项目阶段会推进到素材制作，广告素材生成后推进到投放阶段，媒体上传完成后保持在素材制作阶段，方便面试时说明短剧生产链路的状态流转。

内容策划中的“单集目标时长”属于 AI 策划参数，用于控制生成方案的节奏密度和单集结构；媒体资产中的视频时长才是实际上传或转码后的视频时长。

当前 `project_id` 是 nullable 弱关联，兼容旧演示数据。旧 SQLite 表如果缺少 `project_id` 字段，启动时会通过轻量迁移自动补列；如果本地数据库结构异常，也可以删除 `backend/data/app.db` 后重启自动重建。

## 生产结果列表页

`/storyboards` 是分镜任务列表，`/localizations` 是本地化版本列表，`/ad-materials/list` 是广告素材库。

这些页面用于沉淀 AI 生成结果，让系统从“生成即结束”升级为“生成、保存、查看、复用、导出、复盘”。列表页支持按 `projectId` 筛选，可以从项目详情页带 `?projectId=xxx` 进入，也可以在页面顶部手动切换短剧项目。

面试讲解时可以强调：生成页负责生产，列表页负责资产管理和复盘，这部分体现了真实业务系统的数据管理能力。

## 左侧菜单分组

左侧菜单按业务域分组：AI生产中心负责内容、剧本、分镜和本地化；素材增长中心负责广告素材和增长分析；媒体资产中心负责上传、预览和后续转码。

这种设计让生成页和列表页在导航上归属同一业务模块，但页面职责仍然分离，更接近真实 SaaS 后台的信息架构。

## 项目详情工作台

项目详情页是单个短剧项目的工作台，入口拆分为“项目级规划”和“项目级资产”。

项目级规划用于整部短剧的内容策划、整体剧本打磨、分集管理、项目级广告策略和增长分析；项目级资产用于查看整个项目下全部分集沉淀的分镜、本地化、广告素材和媒体资产。这样可以体现真实业务系统里“规划统筹”和“资产管理”的分层。

项目详情页底部的最近数据区域用于展示项目最近产生的生产资产，并可跳转到对应资产列表，形成“生产 → 沉淀 → 查看复用”的闭环。

## 项目级与分集级职责划分

系统现在明确区分项目级和分集级，避免项目层和分集层的职责混淆。

项目级负责规划、统筹、总览，包括内容策划、整体剧本、项目级广告策略和增长分析。项目级广告策略不绑定具体集数，适合推广整部短剧。

分集级负责具体生产，包括 AI分镜、本地化、媒体资产和单集广告素材。用户需要先进入分集管理，选择具体集数后再进入生产页，系统会携带 `projectId`、`episodeId`、`episodeNo`，让生成结果沉淀到对应分集。

这种设计更符合真实短剧生产流程：项目负责整体方向、统筹和复盘，分集负责单集内容资产生产。

## 项目级剧本打磨

`/script-polish` 当前作为项目级规划能力使用，主要优化整部短剧的大纲、人物关系、核心冲突、节奏和前三秒钩子。

分集级剧本处理后续可从 Episode 维度扩展，从分集管理进入具体集数后再处理单集内容。这样可以避免旧的 `contentPlanId → scriptPolishId` 单线链路和当前 `Project + Episode` 架构混淆。

## 技术栈

前端：
- Vue 3 + TypeScript + Vite
- Vue Router + Pinia
- Naive UI
- Axios
- ECharts

后端：
- Python + FastAPI + Uvicorn
- Pydantic
- SQLAlchemy + SQLite
- python-dotenv
- OpenAI SDK 兼容 DeepSeek
- boto3 接入 AWS S3

## env 说明

根目录 `.env.example` 和后端 `backend/.env.example` 提供环境变量示例。

```env
VITE_API_BASE_URL=http://localhost:8000/api

API_PREFIX=/api
SERVER_PORT=8000
DEBUG=true
DEBUG_LLM_RESPONSE=false
ENABLE_STORYBOARD_MOCK_FALLBACK=false
DATABASE_URL=sqlite:///./data/app.db

AI_PROVIDER=mock
AI_API_KEY=
AI_BASE_URL=https://api.deepseek.com
AI_MODEL=deepseek-v4-flash
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=3000
STORYBOARD_LLM_MAX_TOKENS=6000
AI_TIMEOUT=60

MEDIA_PROVIDER=mock
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=ap-southeast-1
AWS_S3_BUCKET=
AWS_S3_ENDPOINT_URL=
AWS_S3_PUBLIC_BASE_URL=
S3_UPLOAD_PREFIX=media
S3_PRESIGNED_EXPIRE_SECONDS=3600
S3_ADDRESSING_STYLE=path
S3_SIGNATURE_VERSION=s3v4
```

说明：
- `AI_PROVIDER=mock`：强制使用 mock 生成。
- `AI_PROVIDER=deepseek` 且 `AI_API_KEY` 不为空：优先调用 DeepSeek。
- `MEDIA_PROVIDER=mock`：素材上传走本地演示模式，不要求 AWS 配置。
- `MEDIA_PROVIDER=s3`：后端生成 S3 presigned URL，前端直传 S3。
- `AWS_S3_ENDPOINT_URL`：S3 兼容服务地址，例如 `https://s3.hi168.com`；官方 AWS S3 可留空。
- `S3_ADDRESSING_STYLE=path`：适配多数 S3 兼容服务，生成 `/bucket/key` 形式的签名 URL。
- 不要把真实 DeepSeek Key 或 AWS Key 提交到代码仓库。

## 查看 DeepSeek 原始返回

设置：

```env
DEBUG_LLM_RESPONSE=true
```

启动后端：

```bash
uvicorn app.main:app --reload --port 8000
```

调用 AI分镜生成后，在后端控制台查看：

- `raw_response`：DeepSeek 原始文本
- `parsed_scene`：解析后的分镜
- `normalized_scene`：最终入库/返回前的分镜

用于判断重复问题来自模型输出、后端解析还是前端展示。日志只截断展示字段摘要，不会打印 API Key。

AI分镜调试规则：

- DeepSeek JSON 解析失败时，系统不会再静默使用 mock fallback。
- 后端会返回 `STORYBOARD_LLM_JSON_PARSE_FAILED`，失败结果不会保存。
- 开启 `DEBUG_LLM_RESPONSE=true` 后，可以查看 `raw_response`，判断模型是否输出了非 JSON、截断 JSON 或非法字符串。
- AI分镜生成使用专用 `STORYBOARD_LLM_MAX_TOKENS` 控制输出长度，默认 `6000`；该配置只影响 AI分镜模块，不影响内容策划、剧本打磨、分集大纲、本地化和广告素材等其它 LLM 模块。
- AI分镜 prompt 会截断长剧本片段，并对 scene/action/dialogue/emotion/visualPrompt/motionPrompt/consistencyPrompt 设置中等长度约束，平衡内容丰富度和 JSON 稳定性。
- 当前字段长度约束为：scene 40、action 120、dialogue 80、emotion 40、visualPrompt 180、motionPrompt 150、consistencyPrompt 120 个中文字符以内。
- DeepSeek 未启用或未配置 API Key 时，仍可使用 mock 演示数据。
- 如需在演示环境允许 DeepSeek 调用异常后兜底，可设置 `ENABLE_STORYBOARD_MOCK_FALLBACK=true`；该开关不允许 JSON 解析失败兜底。
- 分镜重复检测允许多个镜头处于同一 `scene`；`action`、`dialogue` 重复只记录 warning，强拦截和重试重点是 `visualPrompt`、`motionPrompt` 重复。

## 启动方式

前端：

```bash
cd frontend
npm install
npm run dev
```

后端：

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

FastAPI 文档：

```text
http://localhost:8000/docs
```

## SQLite 持久化

数据库文件位置：

```text
backend/data/app.db
```

生成接口和素材接口会把元数据写入 SQLite。旧数据库如果结构异常，可以删除 `backend/data/app.db`，重启后自动重建。

## 全链路 ID 流

当前生产链路：

```text
contentPlanId → scriptPolishId → storyboardId → localizationId → adMaterialId
```

前端通过 Pinia store 保存当前链路 ID，并持久化到 `localStorage`。Dashboard 可以展示当前链路状态，也可以查看链路详情。

链路详情接口：

```text
GET /api/pipeline/{content_plan_id}
```

## AWS S3 素材上传

新增“素材上传与预览”模块，路径：

```text
/media-assets
```

真实上传流程：

1. 前端选择文件。
2. 前端调用 `POST /api/media/presign`。
3. 后端校验文件类型和大小，生成 S3 presigned PUT URL，并创建 `media_asset` pending 记录。
4. 前端使用 XMLHttpRequest 直传 S3，并展示上传进度。
5. 上传完成后调用 `POST /api/media/complete`。
6. 后端更新素材状态为 `uploaded`。
7. 前端刷新素材列表并预览视频或图片。

为什么前端直传 S3：
- FastAPI 不处理中转大文件，降低后端带宽和内存压力。
- presigned URL 有过期时间，权限更可控。
- 后端只负责签名、校验和保存元数据。

支持文件：
- 视频：mp4、mov、webm，最大 500MB
- 图片：jpg、png，最大 20MB
- 字幕：srt，最大 5MB

S3 Bucket CORS 示例：

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["PUT", "GET", "HEAD"],
    "AllowedOrigins": ["http://localhost:5173"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
```

如果前端直传 S3 报 CORS，需要在 S3 Bucket 配置以上 CORS。生产环境可把 `AllowedOrigins` 改为正式前端域名。

`AWS_S3_PUBLIC_BASE_URL` 可以配置为：
- `https://{bucket}.s3.{region}.amazonaws.com`
- 或 CloudFront 域名
- 或 S3 兼容服务的公开访问前缀，例如 `https://s3.hi168.com/{bucket}`

Hi168 这类 S3 兼容服务参考配置：

```env
MEDIA_PROVIDER=s3
AWS_ACCESS_KEY_ID=你的 Access Key
AWS_SECRET_ACCESS_KEY=你的 Secret Key
AWS_REGION=ap-southeast-1
AWS_S3_BUCKET=你的桶名
AWS_S3_ENDPOINT_URL=https://s3.hi168.com
AWS_S3_PUBLIC_BASE_URL=https://s3.hi168.com/你的桶名
S3_ADDRESSING_STYLE=path
S3_SIGNATURE_VERSION=s3v4
```

## Multipart Upload 预留

当前阶段先实现单文件 presigned PUT 上传。后端已预留以下接口骨架，后续可用于超大文件分片上传：

- `POST /api/media/multipart/init`
- `POST /api/media/multipart/presign-part`
- `POST /api/media/multipart/complete`
- `POST /api/media/multipart/abort`

## API 列表

生成接口：
- `POST /api/content/plan`
- `POST /api/script/polish`
- `POST /api/storyboard/generate`
- `POST /api/storyboard/stream`
- `POST /api/localization/process`
- `POST /api/ads/generate`

素材接口：
- `POST /api/media/presign`
- `POST /api/media/complete`
- `GET /api/media/assets`
- `GET /api/media/assets/{asset_id}`
- `POST /api/media/multipart/init`
- `POST /api/media/multipart/presign-part`
- `POST /api/media/multipart/complete`
- `POST /api/media/multipart/abort`

历史、状态和统计：
- `GET /api/content/plans`
- `GET /api/script/polishes`
- `GET /api/storyboard/list`
- `GET /api/localization/list`
- `GET /api/ads/list`
- `GET /api/health`
- `GET /api/dashboard/summary`
- `GET /api/analytics/overview`
- `GET /api/ai/status`
- `GET /api/pipeline/{content_plan_id}`

## 分集管理 Episode

`Project` 是短剧项目维度，`Episode` 是短剧分集维度。一个短剧项目下可以有多个分集，每个分集记录集数、标题、剧情摘要、当前阶段以及剧本、分镜、本地化、媒体等子任务状态。

新增接口包括：

- `GET /api/projects/{project_id}/episodes`
- `POST /api/projects/{project_id}/episodes`
- `POST /api/projects/{project_id}/episodes/batch-generate`
- `GET /api/episodes/{episode_id}`
- `PATCH /api/episodes/{episode_id}`
- `DELETE /api/episodes/{episode_id}`

前端新增 `/projects/:id/episodes` 分集管理页，并在项目详情页增加分集入口和分集数量统计。后续剧本、分镜、本地化、媒体资产可以继续绑定 `episodeId`，让真实短剧生产按单集推进，避免一次性处理整部剧导致上下文过长。

如果旧 SQLite 数据库没有新表，后端启动时会通过 `create_all` 自动创建；如果本地数据库结构异常，可以删除 `backend/data/app.db` 后重启自动重建。是否自动插入演示数据取决于 `ENABLE_DEMO_SEED`。

## 分集级资产聚合

分集管理页面会展示每一集下的分镜、本地化、媒体资产和广告素材数量。这些数量来自各业务表按 `projectId + episodeId` 聚合统计，不额外写入分集表。

点击数量标签可以跳转到对应资产列表，并自动携带 `projectId`、`episodeId`、`episodeNo` 完成筛选：

- 分镜：`/storyboards?projectId=1&episodeId=10&episodeNo=1`
- 本地化：`/localizations?projectId=1&episodeId=10&episodeNo=1`
- 媒体：`/media-assets?projectId=1&episodeId=10&episodeNo=1`
- 广告：`/ad-materials/list?projectId=1&episodeId=10&episodeNo=1`

这体现了真实短剧系统中“项目 → 分集 → 生产资产”的数据沉淀链路，方便面试时展示每一集的生产进度和资产复用入口。

## AI分镜绑定分集 episodeId

AI分镜现在支持 `projectId + episodeId`。从分集管理进入 AI分镜制作时，页面会携带 `projectId`、`episodeId`、`episodeNo`，并在顶部展示当前正在为哪一集生成分镜。

## 多语种本地化绑定 projectId + episodeId

多语种本地化页面支持通过 `projectId + episodeId` 绑定到具体短剧项目和分集。进入本地化页面后，会优先读取最近一次分集级剧本打磨中文结果作为本地化输入；没有剧本打磨记录时，使用分集大纲 summary 兜底；如果分集内容不可用，则使用项目简介兜底。

目标市场会优先来自项目 `target_market`，目标语言会优先来自项目 `language` / `primary_language`。页面会显示“内容来源”提示，方便演示本地化输入来自剧本打磨、分集大纲、项目简介，还是用户手动编辑。本地化结果继续用于海外字幕、配音方向、口型匹配状态和海外版本生产流程展示。

多语种本地化页面采用“左侧配置输入、右侧结果与海外版本流程”的生产布局，和分镜、剧本打磨、媒体资产页保持一致。

多语种本地化完成后，可以从结果区域跳转到当前 episode 的媒体资产页，继续管理原视频、字幕、配音文件、转码结果和海外版本素材。跳转会携带 `projectId / episodeId / episodeNo`，保证本地化结果与媒体资产按分集沉淀。

分镜生成请求会把 `project_id`、`episode_id`、`episode_no` 传给后端，生成结果会同时保存到对应短剧项目和具体分集。分镜生成成功后，后端会把该分集的 `storyboard_status` 更新为 `completed`，并将分集阶段推进到 `localization`。

分镜任务列表支持按项目和分集筛选，例如：

- `/storyboards?projectId=1`
- `/storyboards?projectId=1&episodeId=10&episodeNo=1`

这样可以按单集推进 AI 分镜生产，避免一次性处理整部短剧导致上下文过长，也让后续本地化、媒体资产和广告素材更容易继续绑定到具体分集。

## 多语种本地化绑定分集 episodeId

多语种本地化现在支持 `projectId + episodeId`。从分集管理进入本地化页面时，会携带 `projectId`、`episodeId`、`episodeNo`，页面会显示当前正在为哪一集生成本地化版本。

本地化结果会保存到对应短剧项目和具体分集。本地化成功后，后端会把该分集的 `localization_status` 更新为 `completed`，并将分集阶段推进到 `media`。

本地化版本列表支持按项目和分集筛选，例如：

- `/localizations?projectId=1`
- `/localizations?projectId=1&episodeId=10&episodeNo=1`

这样可以实现按单集推进出海本地化流程，方便海外发行团队逐集审核、复用和继续进入媒体制作。

## 媒体资产绑定分集 episodeId

媒体资产现在支持 `projectId + episodeId`。从分集管理进入媒体资产页面时，会携带 `projectId`、`episodeId`、`episodeNo`，页面会显示当前正在为哪一集上传媒体资产。

视频、图片、字幕等媒体资产会保存到对应短剧项目和具体分集。媒体上传完成后，后端会更新该分集的 `media_status`；如果上传的是视频素材，会把该分集阶段推进到 `completed`，图片和字幕则保持在 `media` 阶段，表示仍属于媒体制作资产沉淀。

媒体资产页承接本地化结果，按 `projectId / episodeId` 绑定管理原始视频、字幕文件、配音文件、口型匹配后视频和海外预览成片。当前 demo 先展示流程和上传管理，不做真实字幕解析、配音生成或口型匹配；真实生产可后续接入第三方 lip-sync 服务。

媒体资产列表支持按项目和分集筛选，例如：

- `/media-assets?projectId=1`
- `/media-assets?projectId=1&episodeId=10&episodeNo=1`

这样可以按单集管理成片、字幕、封面、角色参考图等资产，后续也便于继续接视频转码和素材版本管理。

## 广告素材可选绑定分集 episodeId

广告素材支持 `projectId`，也支持可选 `episodeId`。不选择分集时，素材属于项目级素材，适合推广整部短剧；从分集管理进入广告素材生成页时，会携带 `projectId`、`episodeId`、`episodeNo`，素材会作为分集级广告素材保存。

分集级广告素材适合围绕某一集爆点生成标题、Hook、CTA 和封面提示词，例如“第 3 集女主当众反杀渣男”。广告素材库支持按项目和分集筛选：

- `/ad-materials/list?projectId=1`
- `/ad-materials/list?projectId=1&episodeId=10&episodeNo=1`

这样既支持整部短剧投放，也支持单集爆点投放。当前 Episode 模型没有单独的 `ad_status` 字段，因此广告素材生成后只做可选分集更新时间更新，不强制推进分集阶段。

## 剧本打磨双模式

ScriptPolish 支持项目级和分集级两种模式。不传 `episodeId` 时，是项目级剧本打磨，用于整部短剧大纲、核心冲突、人物关系和整体节奏；传 `episodeId` 时，是分集级剧本打磨，用于某一集剧情、台词、转折和结尾悬念。

分集级打磨会保存 `episode_id` / `episode_no`，生成成功后推动该集 `script_status=completed`，并进入 `storyboard` 阶段。这样可以形成“内容策划 → 分集大纲 → 分集级剧本打磨 → AI分镜”的生产链路。

## 后续计划

- 素材与分镜 sceneId 精确绑定
- 生成页逐步接入 episodeId，实现单集级剧本、分镜、本地化和媒体资产绑定
- S3 multipart upload 实现真实分片上传
- 增加素材版本管理和导出能力
- 增加更严格的 AI JSON schema 校验
- 接入真实投放平台数据和预算优化策略

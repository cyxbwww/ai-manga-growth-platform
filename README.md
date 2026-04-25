# AI 漫剧出海增长平台 Demo

这是一个用于面试展示的 AI 漫剧出海增长平台 Demo，覆盖内容策划、剧本打磨、AI 分镜制作、多语种本地化、海外投放素材、素材上传与预览、增长分析等模块。

当前重点是展示一个可运行、可扩展、可讲解的 AI 内容生产 SaaS 原型。

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
DATABASE_URL=sqlite:///./data/app.db

AI_PROVIDER=mock
AI_API_KEY=
AI_BASE_URL=https://api.deepseek.com
AI_MODEL=deepseek-v4-flash
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=3000
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

## 后续计划

- 素材与分镜 sceneId 精确绑定
- S3 multipart upload 实现真实分片上传
- 增加素材版本管理和导出能力
- 增加更严格的 AI JSON schema 校验
- 接入真实投放平台数据和预算优化策略

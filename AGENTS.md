# AGENTS.md

## 1. 项目定位

本项目是一个 AI短剧制作平台 Demo，模拟从短剧项目管理、内容策划、剧本打磨、AI分镜、多语种本地化、广告素材生成、媒体资产管理到增长分析的完整链路。

当前项目用于：

- 面试展示 AI 应用落地能力
- 展示 Vue3 + FastAPI 全栈开发能力
- 展示 AI 生成能力如何嵌入真实业务流程
- 展示通过 projectId 串联 AI 生产链路的系统设计

## 2. AI Agent 协作原则

Codex / AI Agent 修改代码时必须遵守：

1. 不要一次性大改全项目。
2. 优先小步提交、分阶段实现。
3. 每次只围绕一个明确目标改造。
4. 不要删除现有可运行功能。
5. 不要破坏现有路由、接口和启动方式。
6. 新增功能优先兼容旧数据结构。
7. 如果需要修改数据库模型，要说明是否需要删除旧 SQLite 数据库。
8. 不要提交真实 API Key、Access Key、Secret Key。
9. 不要提交 node_modules、venv、.env、数据库文件。
10. 所有新增关键逻辑尽量写中文注释，方便面试讲解。

## 3. 前端修改规范

当前前端技术栈：

- Vue3
- TypeScript
- Vite
- Vue Router
- Pinia
- Naive UI
- Axios
- ECharts

要求：

1. 新页面放在 `frontend/src/views`。
2. API 请求封装放在 `frontend/src/api`。
3. 类型定义放在 `frontend/src/types`。
4. 通用状态优先放在 Pinia store。
5. 页面 UI 优先使用 Naive UI。
6. 不要引入新的 UI 框架。
7. 新增路由要同步更新 `router/index.ts`。
8. 新增侧边栏入口要同步更新 `AppLayout.vue`。
9. 所有页面要处理 loading、empty、error 状态。
10. 表格页面要具备真实后台系统质感。

## 4. 后端修改规范

当前后端技术栈：

- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- Uvicorn
- python-dotenv
- OpenAI SDK 兼容 DeepSeek
- mock fallback

要求：

1. API 路由放在 `backend/app/api` 或当前项目已有 routes 目录。
2. 数据模型放在 `backend/app/models`。
3. Pydantic schema 放在 `backend/app/schemas`。
4. 业务服务放在 `backend/app/services`。
5. 新接口必须考虑异常处理。
6. 不存在的数据返回 404。
7. 新增字段要尽量兼容旧数据。
8. mock fallback 不要删除，保证面试演示稳定。
9. 不要把 AI 调用逻辑散落到各个接口里，优先通过 service/client 封装。
10. 保持 `API_PREFIX=/api` 的约定。

## 5. AI 短剧业务规则

后续改造围绕真实短剧生产链路：

短剧项目 project
→ 内容策划 content planning
→ 剧本打磨 script polish
→ AI分镜 storyboard
→ 多语种本地化 localization
→ 广告素材 ad materials
→ 媒体资产 media assets
→ 增长分析 growth analytics

要求：

1. 后续所有生成结果尽量绑定 projectId。
2. 不要把 AI 功能做成孤立工具。
3. 生成结果要能沉淀成列表、详情、历史记录。
4. 分镜数据要考虑角色一致性。
5. 广告素材要考虑 CTR、CVR、ROI 等增长指标。
6. 媒体资产要区分 mock S3 和真实 S3。
7. 真实生产环境可扩展任务队列、视频转码、多租户和权限管理。

## 6. 面试展示要求

后续代码改造要服务于面试讲解：

1. 能说明为什么这样设计。
2. 能说明前后端怎么联动。
3. 能说明 AI 输出如何结构化。
4. 能说明 projectId 如何串联业务链路。
5. 能说明 mock 与真实服务如何切换。
6. 能说明后续如何生产化扩展。
7. 页面要能稳定演示，不要依赖必须联网才能跑通。

## 7. 每次任务完成后的输出格式

每次 Codex 完成任务后，请输出：

1. 修改了哪些文件
2. 新增了哪些文件
3. 新增了哪些接口
4. 是否影响数据库
5. 是否需要删除 `backend/data/app.db`
6. 如何启动和验证
7. 下一步建议

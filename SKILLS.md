# SKILLS.md

## 1. 项目需要的核心技能

本项目围绕 AI短剧制作平台，需要体现以下能力：

1. Vue3 + TypeScript 前端工程能力
2. Naive UI 后台系统页面开发能力
3. FastAPI 后端接口开发能力
4. SQLAlchemy + SQLite 数据持久化能力
5. AI 应用集成能力
6. Prompt 设计和结构化输出能力
7. mock fallback 和真实服务切换能力
8. 媒体上传与 S3 presigned URL 设计能力
9. 数据可视化和增长分析能力
10. 面试项目讲解和工程化表达能力

## 2. Vue3 技能规范

要求：

1. 使用 Composition API。
2. 使用 TypeScript 类型约束。
3. ref / reactive 使用要清晰。
4. 表格数据、表单数据、loading 状态分离。
5. 页面逻辑不要堆得太乱，必要时抽 api 和 types。
6. Naive UI 表单要有校验。
7. 列表页要有筛选、空状态、加载状态、错误提示。
8. 操作按钮要有确认逻辑，例如删除、归档。
9. 页面展示字段要使用中文标签，方便面试演示。
10. 样式使用 scoped CSS。

## 3. FastAPI 技能规范

要求：

1. 路由清晰，接口命名符合业务语义。
2. Pydantic schema 区分 Create / Update / Out。
3. SQLAlchemy model 字段要有默认值和时间字段。
4. 查询接口支持 skip / limit。
5. 详情接口不存在时返回 404。
6. 修改接口自动更新 updated_at。
7. 删除优先软删除，例如 `status=archived`。
8. 后端错误信息要清晰。
9. 新增接口要能在 `/docs` 里看到。
10. 启动方式保持 `uvicorn app.main:app --reload --port 8000`。

## 4. AI 应用技能规范

要求：

1. AI 生成结果尽量结构化，优先 JSON。
2. 后端要做结果解析和兜底。
3. 前端不要直接依赖大段自然语言。
4. Prompt 中要明确角色、任务、输出格式和限制条件。
5. 对分镜生成，要包含 scene、characterAction、dialogue、emotion、visualPrompt、motionPrompt、consistencyPrompt。
6. 对广告素材生成，要包含 title、hook、body、cta、coverPrompt、abTestSuggestion。
7. 对本地化，要区分中文审核稿和目标语言投放稿。
8. mock fallback 要保留，保证演示稳定。
9. `AI_PROVIDER=mock` 时必须可离线演示。
10. `AI_PROVIDER=deepseek` 时才调用真实模型。

## 5. 短剧业务技能规范

短剧平台要体现以下业务理解：

1. 短剧不是普通文章生成，而是强节奏、强冲突、强转化内容。
2. 内容策划要关注题材、人群、市场、卖点。
3. 剧本打磨要关注前三秒钩子、反转、爽点、情绪冲突。
4. 分镜要关注人物一致性、画面提示词、运镜提示词。
5. 本地化不是直译，而是适配目标市场文化表达。
6. 广告素材要服务投流，关注 CTR、CVR、ROI。
7. 媒体资产要支持上传、预览、转码状态管理。
8. 增长分析要形成内容生产反向优化。
9. projectId 是全链路数据主键。
10. 列表页和详情页体现数据沉淀和业务管理能力。

## 6. 工程化技能规范

要求：

1. 配置项放到 `.env.example`。
2. 不提交真实 `.env`。
3. 不提交 API Key。
4. 不提交数据库文件。
5. 不提交 node_modules / venv。
6. README 要同步更新。
7. 每次新增功能要说明启动和验证方式。
8. 如果引入新依赖，要说明原因。
9. 能 build / compile 后再结束任务。
10. 面试前保证 mock 模式也能完整演示。

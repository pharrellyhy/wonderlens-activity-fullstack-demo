# WonderLens Activity Demo 周报

**日期**: 2026-03-13

---

## 项目概述

WonderLens Activity Demo 是一个全栈互动演示应用，包含多智能体后端（Director、Script、Visual、Recipe Assembler）和 React 分屏前端。用户上传照片后，系统生成结构化的互动活动脚本，支持语音对话、TTS 语音合成和 ASR 语音识别。

---

## 本周完成工作

### 1. 逐轮 LLM 生成架构（核心重构）

将原有的"一次性预生成完整脚本"架构替换为**逐轮实时生成**架构：

- **之前**：启动时 Script Agent 一次性生成全部对话脚本（30-60秒），后续每轮仅做静态查找（~5ms）
- **之后**：Director Agent 填充创意参数，Script Agent 每轮基于用户输入 + 模板结构 + 对话状态实时生成下一轮对话（Gemini Flash，1-2秒/轮）

主要改动：
- 新增 Pydantic 数据模型：`CreativeSlots`、`TurnResponse`、`SessionStateModel`
- 新增状态机引擎（`state_machine.py`），支持 Cat 1（设备内语言活动）和 Cat 5（设备外收集活动）两类模板的完整状态流转
- 重写 Script Agent 为逐轮生成模式，搭配模块化 system prompt（13 个步骤指令文件）
- 重写 `/api/start` 和 `/api/turn` 端点，集成状态机 + 逐轮 LLM 调用
- 前端适配：移除 recipe 依赖，新增自动推进、错误退出、Cat 5 照片收集画廊等功能

### 2. 延迟优化（三项并行优化）

| 优化项 | 优化前 | 优化后 |
|--------|--------|--------|
| `/api/start` 延迟 | 22-43秒 | ~12秒 |
| Script Agent 每轮 | 3-8秒（频繁失败） | 1-2秒 |
| TTS 首音频延迟 | ~6秒 | ~3秒 |

具体措施：
- **禁用 Gemini 思考模式**（`thinking_budget=0`）：消除 JSON 截断问题，Script Agent 首次调用即成功
- **Vision + Director 并行化**：`/api/start` 中通过 `asyncio.gather` 并行执行，配合基于文件名的实体提取，节省 ~5秒
- **合并 `/api/turn-speak` 流式端点**：Script Agent 流式输出 + 服务端 TTS 管线化 + 二进制流式协议（JSON 头 + PCM 音频块），前端渐进式播放（Web Audio API 时间调度），首个音频块到达即开始播放

### 3. 连接稳定性修复

- TTS 和 Vision 模块从同步客户端（`run_in_executor`）迁移至**异步客户端**（`client.aio`），解决 `ConnectionResetError` 问题
- TTS 流式接口新增**重试机制**（最多 2 次重试，指数退避），Vision 新增 1 次重试
- `/api/tts` 端点切换为异步流式版本

### 4. 前端 UI 重构

- 实现毛玻璃风格（glassmorphic）暗色 UI 设计
- 新增打字指示器动画
- 新增 Cat 5 照片收集画廊组件（`PhotoGallery.jsx`）
- TTS 播放重写为渐进式无缝播放（消除块间噪音和间隙）

### 5. 接口契约加固

- 关闭步骤正确标记会话完成状态
- Cat 5 收集进度正确序列化到 `session_state`
- Script Agent 双重失败时返回显式错误退出
- 自动推进仅在活跃的非关闭展示步骤触发
- 流式早期对话与最终回退文本不一致时自动重启 TTS

---

## 当前架构

```
用户上传照片
    ↓
/api/start（~12秒）
    ├── Vision 分析（并行）
    └── Director → 创意参数 → Script Agent 首轮对话
    ↓
/api/turn-speak（1-2秒/轮）
    ├── 状态机推进
    ├── Script Agent 流式生成（Gemini Flash）
    └── TTS 管线化流式输出（PCM 音频块）
    ↓
前端渐进式播放 + 语音识别 → 下一轮
```

---

## 下周计划

- 端到端测试覆盖（合并端点 + 渐进式播放）
- 性能基准测试与进一步延迟优化
- Cat 5 收集流程完整验证

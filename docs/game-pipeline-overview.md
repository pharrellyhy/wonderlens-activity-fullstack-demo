# 游戏流程概览

本文档对比 Category 1（设备内语言互动）和 Category 5（设备外收集探索）两类游戏的完整流程，并详细说明 Cat5 独有的 Synthesis（综合创作）步骤。

---

## 流程对比

### Category 1：设备内语言互动

```
拍照 → Hook → Transition → Rounds (2-4轮) → Celebrate → Closing
                                                          ↘ Early Exit
```

| 步骤 | 说明 | 示例（Bicycle） |
|------|------|----------------|
| **Hook** | 对照片发出惊叹，提出一个情感/想象类问题 | "哇，一辆自行车！那些闪亮的轮子……如果它会说话，你觉得它会说什么？" |
| **Transition** | 介绍游戏机制，包含一个示范回合，邀请孩子参与 | "我来告诉你发生了什么，你来扮演自行车说话！比如它在车库等了一整天，它可能会说'好无聊啊！'想试试吗？" |
| **Rounds** | 每轮：AI 描绘场景 → 孩子以角色身份回应 → AI 验证并连接学习内容 | 第1轮：下坡飞驰；第2轮：轮胎漏气；第3轮：发现新路 |
| **Celebrate** | 授予角色头衔，回顾每轮精彩时刻 | "你是真正的 Bike Whisperer！你感受到了下坡的兴奋、漏气的心疼、新路的好奇！" |
| **Closing** | 自然引出 IB 概念，温暖告别 | "每个零件都有自己的工作（Function），自行车带你去新地方（Connection）" |
| **Early Exit** | 连续2次沉默时触发，温柔告别，不施压 | "你已经是自行车的好朋友了，下次再见！" |

**游戏机制类型（`game_mechanic`）：**
- `voice_acting` — 扮演物体说话（Bicycle, Dog, Playground）
- `prediction_game` — 预测会发生什么（Green Apple, Sunflower）
- `storytelling_chain` — 接龙讲故事（Cat, City Library）
- `helper_hotline` — 帮助解决问题（Stop Sign）
- `mood_guessing` / `true_or_silly` / `riddle_game` / `sound_imitation` — 其他可用机制

---

### Category 5：设备外收集探索

```
拍照 → Hook → Transition → Rounds (2-3轮) → Synthesis → Celebrate → Closing
                                                                      ↘ Early Exit
```

| 步骤 | 说明 | 示例（Ladybug / Polka Dot Patrol） |
|------|------|----------------------------------|
| **Hook** | 对照片发出惊叹，提出关于特征的想象类问题 | "哇，一只瓢虫！看那些黑色波点，你觉得它们像什么？小按钮还是小窗户？" |
| **Transition** | 介绍收集任务，用叙事框架（探险/侦察/巡逻），以邀请方式提出 | "瓢虫不是唯一有斑点的东西！想不想当 Polka-Dot Patrol Officer，去找3个有圆点的东西？" |
| **Rounds (2-phase)** | 每轮有两个阶段：**Phase A** 孩子拍照选择 → AI 验证 + 问 detail question；**Phase B** 孩子口头回答 → AI 处理细节（命名/观察）→ 进入下一轮 | Phase A：找到斑点蘑菇 → AI："这些圆点跟之前的有什么不同？"；Phase B：孩子回答"这些更大！"→ AI 记录观察 |
| **Synthesis** | Cat5 独有 — 使用收集过程中已收集的名字和观察结果进行创意综合活动（详见下节） | "你叫它们 Cloud Puff 和 Fuzzy Green！想给它们编一个小故事吗？" |
| **Celebrate** | 授予角色头衔，回顾发现过程 | "你是真正的 Polka-Dot Patrol Officer！你在到处都发现了斑点和圆圈！" |
| **Closing** | 自然引出 IB 概念，温暖告别 | "你发现了 Form（斑点的形状到处都有），还有 Connection（这些不同的东西竟然都有圆点）" |
| **Early Exit** | 连续2次沉默时触发，温柔告别 | "圆点们会等你下次再来的！" |

**观察角度类型（`observation_angle`）：**
- `pattern` — 图案/纹样（Ladybug）
- `form` — 形态/外观（Lion, Goldfish）
- `color` — 颜色（Crayons）
- `function` — 功能/用途（Firefighter, Raincoat）
- `texture` — 质感（Dandelion）
- 其他可用：`shape` / `size` / `habitat` / `movement` / `smell`

**综合创作类型（`synthesis_type`）：**
- `comparison_chart` — 比较分类
- `naming_story` — 命名故事
- `creative_narrative` — 创意叙事
- `sorting_game` — 分类游戏

**Cat5 2-Phase Collection Loop（新增）：**

每个收集轮有两个阶段：
- **Phase A (`photo`)** — 孩子选择照片，AI 验证后问 `detail_question_template`
- **Phase B (`detail`)** — 孩子口头回答，AI 处理细节（naming_story 生成角色名，comparison_chart 记录观察），然后进入下一轮

状态字段：
- `collection_phase`: `"photo"` 或 `"detail"` — 当前阶段
- `collected_details`: 每次 Phase B 的孩子回答
- `collected_names`: naming_story 活动中生成的角色名

Creative slots 新增字段：
- `detail_question_template`: 每次正确选图后问的 detail 问题（例如"这些圆点跟之前的有什么不同？"）
- `sorting_criterion`: comparison_chart/sorting_game 综合活动中的排序标准（例如"圆点大小"）

---

## Synthesis 步骤详解

Synthesis 是 Cat5 游戏的核心创意环节，在所有收集品找齐之后、正式颁发徽章之前进行。它利用收集过程中已经积累的名字和观察结果（而不是从头开始）来创造有意义的整体洞察。

### 四种综合创作类型

#### 1. Comparison Chart（比较图表）

**做什么：** 利用收集过程中已记录的观察结果，按 `sorting_criterion` 引导孩子排序/比较。

**AI 引导方式：**
- 引用收集过程中孩子已分享的观察："你说第一个有大圆点，第二个有小斑点——"
- 按 `sorting_criterion` 引导排序："你想把它们从最大到最小排列吗？"
- "我发现了一个有趣的东西——你有没有看到？"

**示例（Ladybug — pattern，sorting_criterion: "dot size"）：**
> 收集过程 Phase B 记录：蘑菇 → "大大的圆点"；石头 → "小小的斑点"；花 → "完美的圆圈"
> 综合步骤 AI："你的蘑菇有大圆点，石头有小斑点，花有完美的圆圈！你想从最大到最小排列它们吗？"

**使用该类型的游戏：** Ladybug, Lion, Eye, Firefighter, Goldfish, Piano

#### 2. Naming Story（命名故事）

**做什么：** 使用收集过程中已命名的角色，一起编一个小故事。

**AI 引导方式：**
- 角色名已在每轮 Phase B 中生成（孩子描述 → AI 创造角色名）
- 综合步骤直接引用已有角色名："Cloud Puff 和 Fuzzy Green 如果见面了，你觉得它们会做什么？"
- 不需要重新命名——直接进入故事创作

**示例（Dandelion — texture）：**
> 收集过程：苔藓 → "像云" → Cloud Puff；花瓣 → "像枕头" → Pillow Petal；毛毛虫 → "会痒" → Tickle Worm
> 综合步骤 AI："Cloud Puff、Pillow Petal 和 Tickle Worm 如果见面了，你觉得它们会做什么？"

**使用该类型的游戏：** Dandelion, Crayons, Raincoat

#### 3. Creative Narrative（创意叙事）

**做什么：** 把所有收集品串成一个连贯的故事或场景。

**与 Naming Story 的区别：** 重点在于整体叙事和因果关系，而不是单独命名。

#### 4. Sorting Game（分类游戏）

**做什么：** 按某个属性给收集品分组。

**示例（Piano — form/声音）：**
> AI："哪些东西发出的声音是高高的？哪些是低低的？哪些是响响的？"
> 孩子把金属栅栏归入"响"，把树叶归入"轻"，把空心管归入"高"。

**使用该类型的游戏：** Piano

### 设计原则

| 原则 | 说明 |
|------|------|
| **邀请式语言** | 始终用问句框架："Would you like to...?" 而不是命令式 "Let's do..." |
| **孩子主导** | 孩子驱动创意活动，AI 在孩子说的基础上扩展 |
| **灵活应对** | 孩子说"你来做"→ AI 必须真正创作内容；孩子说"帮帮我"→ AI 给提示但让孩子继续参与 |
| **简洁** | AI 每次最多1-2句话，因为孩子刚听完收集轮的庆祝 |

### 孩子回应处理

```
孩子回应                          AI 做什么                          stay_on_step
─────────────────────────────────────────────────────────────────────────────────
主动参与（取名/比较/讲故事）       热情回应，在此基础上扩展，结束综合    false
"你来做" / "好的" / "可以"        必须立即创作内容（不能跳过！）        false
"给我点灵感" / "给我看看"         给1-2个有趣的例子，邀请孩子尝试       true
"我不知道" / "帮帮我"             给具体建议或二选一选择                true
沉默                              用更简单的方式重新邀请                true
跑题但有参与                      温暖回应，轻轻引导回来                true
```

---

## 关键差异总结

| 维度 | Category 1 | Category 5 |
|------|-----------|-----------|
| **场景** | 设备内，孩子对着屏幕说话 | 设备外，孩子在真实环境中寻找物品 |
| **核心机制** | `game_mechanic`（voice_acting 等） | `observation_angle` + `collection_criterion` + `detail_question_template` |
| **互动方式** | 孩子扮演物体，用语言表达 | 2-phase loop：Phase A 拍照选择 → Phase B 口头描述细节 |
| **Synthesis 步骤** | 没有 | 有（比较/命名/叙事/分类），使用收集过程中已积累的数据 |
| **屏幕组件** | `character_display`（角色插画） | `progress_tracker`（收集进度） |
| **轮次数量** | 2-4轮（由 `round_scenarios` 决定） | 2-3轮（由 `collection_count` 决定） |
| **IB 概念教学** | 在 Closing 步骤自然引出 | 在 Closing 步骤自然引出 |
| **角色授予** | 在 Celebrate 步骤 | 在 Celebrate 步骤 |

---

## 游戏转换流程

### 文件结构

```
backend/games/
├── mood_changer_dog.md          # 可加载的游戏定义（有 YAML frontmatter）
├── polka_dot_patrol.md          # 可加载的游戏定义
├── ...                          # 其他已转换的游戏
├── cat1/                        # Cat1 设计文档（*_prod.md, *_spec.md）
│   ├── bicycle_cat1_prod.md     # 原始设计稿
│   └── bicycle_cat1_spec.md     # 规范文档
└── cat5/                        # Cat5 设计文档
    ├── dandelion_cat5_prod.md
    └── dandelion_cat5_spec.md
```

**重要：** 只有 `backend/games/*.md`（顶层目录）中以 `---` 开头的文件会被 `game_loader.py` 加载。`cat1/` 和 `cat5/` 子目录中的文件是设计参考文档，不会被运行时加载。

### 转换工具

#### 1. `scripts/generate_game_frontmatter.py` — 快速脚手架

从 `*_prod.md` 设计文档中提取基本信息，生成带 TODO 标记的 YAML frontmatter 骨架。不调用 LLM，纯正则提取。

```bash
# 从设计文档生成骨架
python scripts/generate_game_frontmatter.py backend/games/cat5/lion_cat5_prod.md

# 指定输出路径
python scripts/generate_game_frontmatter.py backend/games/cat5/lion_cat5_prod.md \
  --output backend/games/brave_things_hunt_lion.md
```

生成的文件需要手动填写 TODO 项，包括：
- `photo_features`, `feature_keywords`, `keywords`
- `creative_slots` 中的具体值
- `collection_catalog` 中的 correct/distractor 条目
- `step_instructions` 中的各步骤 goal/constraint
- Cat5 必填：`detail_question_template`（Phase B detail 问题）和 `sorting_criterion`（comparison_chart 排序标准）

#### 2. `scripts/convert_game.py` — LLM 辅助完整转换

使用 Gemini LLM 从设计文档自动提取所有字段，生成完整的可加载游戏定义。以 `polka_dot_patrol.md`（Cat5）或 `mood_changer_dog.md`（Cat1）作为 few-shot 参考。

```bash
# 转换单个游戏
uv run python scripts/convert_game.py backend/games/cat5/feather_cat5_prod.md

# 预览输出（不写文件）
uv run python scripts/convert_game.py backend/games/cat5/feather_cat5_prod.md --dry-run

# 批量转换所有顶层 *_prod.md 文件
uv run python scripts/convert_game.py --all

# 指定 Gemini 客户端模式
uv run python scripts/convert_game.py backend/games/cat5/feather_cat5_prod.md --mode vertex
```

**Cat5 游戏转换后需验证的字段：**
- `detail_question_template` — Phase B 的 detail 问题是否自然、与 `observation_angle` 相关
- `sorting_criterion` — 对于 `comparison_chart`/`sorting_game` 是否有具体的排序维度；对于 `naming_story` 应为空字符串
- `collection_catalog` — correct 和 distractor 条目是否合理

### 验证

```bash
# 验证所有游戏定义可加载
cd backend && uv run pytest ../tests/test_game_parser.py -q

# 验证 Schema 合规
cd backend && uv run pytest ../tests/test_schemas.py -q

# E2E 测试所有活动
python scripts/test_all_activities.py
```

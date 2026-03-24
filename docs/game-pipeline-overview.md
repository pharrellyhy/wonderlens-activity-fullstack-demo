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
| **Rounds** | 每轮：孩子外出寻找/拍摄一个物品 → AI 庆祝发现、鼓励比较、引导下一次寻找 | 第1轮：找到有斑点的蘑菇；第2轮：找到有斑纹的石头；第3轮：找到有圆圈的花 |
| **Synthesis** | Cat5 独有 — 把所有收集品放在一起，进行创意综合活动（详见下节） | "看看你的三个宝藏！哪个的圆点最大？哪个最小？你想给每个取个名字吗？" |
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

---

## Synthesis 步骤详解

Synthesis 是 Cat5 游戏的核心创意环节，在所有收集品找齐之后、正式颁发徽章之前进行。它把一堆零散的发现变成一个有意义的整体洞察——这是"然后呢？"的时刻。

### 四种综合创作类型

#### 1. Comparison Chart（比较图表）

**做什么：** 引导孩子按 `observation_angle` 比较收集品之间的异同。

**AI 引导方式：**
- "你愿意告诉我，它们哪里像、哪里不像吗？"
- "哪个的圆点最大？哪个最小最偷偷摸摸的？"
- "我发现了一个有趣的东西——你有没有看到？"

**示例（Ladybug — pattern）：**
> 孩子找到了：斑点蘑菇、圆点石头、有圆圈的花
> AI："你的石头有大大的圆圆的点，但叶子上是超级小的斑点——一个很大胆，一个在偷偷躲！你有没有发现？"

**使用该类型的游戏：** Ladybug, Lion, Eye, Firefighter, Goldfish, Piano

#### 2. Naming Story（命名故事）

**做什么：** 给收集品取好玩的名字，然后一起编一个小故事。

**AI 引导方式：**
- "你想给每个发现取个名字吗？这个毛茸茸的可以叫什么？"
- 如果孩子已经在收集过程中取了名字，直接使用那些名字
- "Captain Fluffball 和 Fuzzkins 如果见面了，你觉得它们会做什么？"

**示例（Dandelion — texture）：**
> 孩子找到了：毛茸茸的苔藓、蓬松的种子头、软软的花瓣
> AI："从前，蓬蓬队长和绿绿毛毛虫一起去冒险！它们发现了扭扭毛毛虫，三个一起从一座软绵绵的山上滚下来，一路笑个不停！"

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
| **核心机制** | `game_mechanic`（voice_acting 等） | `observation_angle` + `collection_criterion` |
| **互动方式** | 孩子扮演物体，用语言表达 | 孩子物理移动、拍照、描述 |
| **Synthesis 步骤** | 没有 | 有（比较/命名/叙事/分类） |
| **屏幕组件** | `character_display`（角色插画） | `progress_tracker`（收集进度） |
| **轮次数量** | 2-4轮（由 `round_scenarios` 决定） | 2-3轮（由 `collection_count` 决定） |
| **IB 概念教学** | 在 Closing 步骤自然引出 | 在 Closing 步骤自然引出 |
| **角色授予** | 在 Celebrate 步骤 | 在 Celebrate 步骤 |

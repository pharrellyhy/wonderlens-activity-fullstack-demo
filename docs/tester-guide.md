# Tester Guide / 测试者指南

Welcome. This guide is for an education expert trying the WonderLens Activity Demo for the first time. Before the step-by-step, it explains what the demo is trying to do and how the system is put together, so your feedback targets the right layer.

欢迎。本指南面向首次体验 WonderLens Activity Demo 的教育专家。在进入操作步骤之前，会先说明 demo 想要做什么、以及背后的系统是如何搭建的，这样你的反馈就能对准合适的层级。

---

## English

### What this demo is

WonderLens is an AI-guided play activity for children roughly ages 2–8. A child (or an adult playing the child) selects a photo of a toy, plush, or nature object they have on hand, and the system turns it into a short, voice-driven activity — a story, a collection game, or a "notice and describe" game — led by a friendly character. The goal is to support joyful, age-appropriate exploration, not to quiz the child.

There are two families of activities in the demo:

- **In-Device Verbal (Category 1)** — the child talks with the character about the object. Examples: *mood changer dog*, *dream whisperer cat*, *time machine dinosaur*.
- **Out-of-Device Collection (Category 5)** — the child physically looks around the room and collects/points-at things. Examples: *polka dot patrol*, *fluffy expedition dandelion*. This branch ends with a generated illustrated story + an achievement image as a keepsake.

### Age tiers you will see reflected in pacing and language

The system uses three tiers. Rounds, vocabulary complexity, and expected response length scale with the tier.

- **T0 (2–4)** — very concrete, short sentences, physical/visible anchors, 2–4 rounds.
- **T1 (4–6)** — still concrete, some imagination, 4–6 rounds.
- **T2 (6–8)** — more open-ended prompts, richer storytelling, 6–8 rounds.

The character's phrasing is deliberately **invitational**, not directive — "Would you like to…?" rather than "Go find!". This is an explicit content-design rule based on earlier edu-team feedback; flag any line that slips back into commands.

### What's under the hood (mental model)

You do not need to know the code, but these four mental pieces explain almost every behaviour you will see:

1. **Photo → Recipe.** When you pick a photo, a multi-agent pipeline (Director → Script + Visual → Recipe Assembler) produces a single structured *recipe* for the whole session: the creative arc, the rounds, the dialogue branches (correct / incorrect / silence), and the screen sequence. This happens **once**, up front.
2. **Turn lookup.** Every turn after that is just a lookup into the recipe plus a match against what the child said. That's why later turns feel consistent — the story was planned end-to-end before you started.
3. **Silence is a first-class path.** The recipe has explicit branches for "child said nothing." The character will re-invite gently rather than barrel forward; after two consecutive silences the activity exits gracefully. This is intentional scaffolding, not a timeout bug.
4. **Scene images and the achievement image are generated live.** In Category 5 activities, the final story is split into scenes; each scene's illustration and a closing achievement image are generated on the fly. They occasionally fail (rate limits, content filters) — the UI surfaces that explicitly rather than pretending success.

### 1. Before you start

- Open the demo URL your team shared (in local dev this is typically `http://localhost:5173`).
- Use Chrome or another Chromium-based browser — speech recognition is most reliable there.
- Allow **microphone access** when prompted. The character listens for the child's reply.
- Use speakers or headphones. The character speaks throughout; reading subtitles alone loses the intended experience.

### 2. Switch to Tester Mode

- At the top of the screen there is a small **Dev / Tester** pill. Click it to flip to **Tester**. Alternatively open the page with `?mode=tester` appended to the URL.
- Tester Mode changes two things deliberately:
  - A yellow **flag button** appears bottom-right at all times.
  - An inline **Continue** button replaces auto-advance at the end of each turn, so you can pause and reflect without the session racing past you.
- Your selection is remembered by the browser, so this is a one-time step.

### 3. Enter a tester alias

A small modal asks for a name the first time. Short is fine — it only labels your feedback bundles so a reviewer can see who flagged what.

### 4. Pick a photo and play

- The landing page shows a curated grid of demo photos (toys, plush, nature items).
- Selecting one triggers the recipe generation described above. You will briefly see a loading state, then the split-view opens:
  - **Left panel** — the character's dialogue, the child's transcribed speech, and a voice/text input.
  - **Right panel** — the "device screen": images, prompts, and activity-specific widgets that change turn by turn.
- The character opens with a **hook**, then guides the child through the rounds appropriate to the tier.
- Respond by speaking or typing. Silence is tolerated; the character will re-invite.

### 5. What you should expect to see

- The **right panel changes every turn** — progress indicators, photos, collected items, scene illustrations, and finally a celebration screen.
- At the end of a Category 5 session you will see a **multi-scene story**, each scene paired with a generated illustration, followed by an **achievement image** as a keepsake.
- If any image fails to generate, the UI shows a muted amber **"Couldn't create this image"** banner. That is a known, expected fallback — please flag it so we can judge whether the recovery experience is good enough.
- The session ends with a closing farewell and a **photo recall grid** summarising the highlights the child just went through.

### 6. Flag a moment

Anything that feels off for a real child — wording, pacing, a visual glitch — or a moment that worked beautifully, is worth a flag. Your educator judgment is exactly what we are trying to capture.

- Click the yellow **flag button** (bottom-right).
- A small popover opens with:
  - An auto-captured **screenshot** of the current screen.
  - Four **tags**, pick one or more:
    - **Tone** — voice/wording feels off for this age or context.
    - **Confusing** — a real child would lose the thread here.
    - **Bug** — something is visibly broken.
    - **Loved it** — a moment worth protecting.
  - A **quick note** — one sentence of context is plenty.
- Press Enter (or Save) to commit. Press Esc or click outside to cancel.
- You can reopen a flag later to edit tags, note, or add a longer review comment.
- Flagging does not pause the session.

### 7. Review and submit after the session

- When the session ends you land on a **review screen** listing every flag you made.
- For each flag you can edit tags, add a longer **review comment** (your considered reflection, versus the in-the-moment quick note), or delete.
- Two exits:
  - **Submit to backend** — sends the bundle (JSON + screenshots) to the server.
  - **Download zip** — saves the same bundle locally if you want to share it another way.

### 8. Browse past feedback (optional)

- On the landing page, click **"View feedback gallery →"** top-right of the photo picker, or visit `?view=feedback` directly.
- The gallery is **read-only** — filter by tag, tester alias, or sort newest/oldest. Click any thumbnail for a fullscreen view.

### 9. What is most useful for you specifically to flag

Because you are evaluating with an educator's eye, these are the layers where your input is most valuable:

- **Developmental fit.** Does the tier match what a real child this age would handle? Too advanced or too babyish?
- **Invitational language.** Every line should invite. Anything that slips into commanding ("Go find!", "Tell me!") should be flagged.
- **Scaffolding on silence or wrong answers.** Does the character re-invite warmly, or does it feel like correction / pressure?
- **Coherence across turns.** Does the story arc hold together, or does the character contradict earlier turns?
- **Visual alignment.** Do the scene images and achievement image reinforce the story, or distract from it?
- **Joyful moments.** Flag these too — they tell us what must not regress.

---

## 中文

### Demo 在做什么

WonderLens 是一款面向 2–8 岁儿童的 AI 引导型游戏活动。孩子（或扮演孩子的大人）选择一张自己手边的玩具、毛绒公仔或自然物的照片，系统就会把它转化为一段短小的语音驱动活动 —— 一个故事、一个收集小游戏，或一次"观察并描述"的练习 —— 由友好的角色带领。目标是支持充满乐趣、与年龄相配的探索，而不是测验孩子。

Demo 中有两大活动类别：

- **设备内语言类（Category 1）**：孩子与角色围绕手上的物件进行对话。代表活动：*mood changer dog*、*dream whisperer cat*、*time machine dinosaur*。
- **设备外收集类（Category 5）**：孩子在房间里实际寻找或指认物件。代表活动：*polka dot patrol*、*fluffy expedition dandelion*。这条分支会以一段带插图的生成式故事 + 一张成就纪念图收尾。

### 你会从节奏与措辞中感受到的年龄分层

系统设置了三档 tier，回合数、词汇难度、期望回答长度都会随 tier 调整。

- **T0（2–4 岁）**：非常具象，句子短，强调身体可见的锚点，2–4 个回合。
- **T1（4–6 岁）**：仍然具象，允许少量想象，4–6 个回合。
- **T2（6–8 岁）**：提示更开放，叙事更丰富，6–8 个回合。

角色的语气被刻意设计为**邀请式**而不是指令式 —— 使用 "Would you like to…?" 而不是 "Go find!"。这是依据此前教育团队反馈确立的明确内容设计规则；任何滑回命令语气的台词都值得打 flag。

### 引擎盖下发生了什么（心智模型）

你不需要了解代码，但以下四件事几乎可以解释你看到的所有行为：

1. **照片 → Recipe**。当你选中一张照片时，一个多 agent 流水线（Director → Script + Visual → Recipe Assembler）会为整场活动生成一份结构化的 *recipe*：创意弧线、回合、对话分支（正确 / 错误 / 沉默）、以及屏幕序列。这件事**只发生一次**，在你开始之前。
2. **回合查表**。之后每个回合其实只是对 recipe 的查表 + 匹配孩子说了什么。这就是后续回合感觉稳定连贯的原因 —— 整段故事在开始之前就已经端到端规划好了。
3. **沉默是一等路径**。Recipe 里为"孩子没说话"准备了专门的分支：角色会温和地再邀请一次，而不是硬推进；连续两次沉默后活动会优雅退出。这是刻意的支架设计，不是超时 bug。
4. **场景图与成就图是实时生成的**。在 Category 5 活动中，最终故事会拆成多个场景，每个场景的插画和收尾的成就图都是即时生成的。偶尔会失败（限流、内容审核），此时界面会明确告知而不是假装成功。

### 1. 开始之前

- 打开团队共享的 demo 地址（本地开发通常是 `http://localhost:5173`）。
- 推荐 Chrome 或其它 Chromium 内核浏览器 —— 语音识别在这类环境下最稳定。
- 浏览器弹出权限时请**允许使用麦克风**，角色要听取孩子的回答。
- 打开外放或佩戴耳机。角色全程用语音表达，仅看字幕会丢失设计意图。

### 2. 切换到 Tester 模式

- 页面顶部有一个小标签 **Dev / Tester**，点击即可切换到 **Tester**。也可以在 URL 末尾加 `?mode=tester` 进入。
- 切换后有两处有意为之的变化：
  - 右下角始终显示一枚黄色**旗帜按钮**。
  - 每个回合末尾的自动推进被替换为内联的 **Continue** 按钮，给你留出停顿与思考的空间，不会被会话抢拍。
- 选择会被浏览器记住，只需切一次。

### 3. 填写测试者昵称

首次进入会弹出一个小窗口，简短即可 —— 它只是用来标记你的反馈包，让后续评审知道谁打的 flag。

### 4. 选一张照片并开始

- 落地页展示一组精选 demo 照片（玩具、毛绒、自然物）。
- 选中后会触发前文所述的 recipe 生成。会短暂地看到一个 loading 状态，随后进入分屏界面：
  - **左侧**：角色对话、孩子语音的实时转写、语音/文字输入。
  - **右侧**：「设备屏」，根据回合变化展示图片、提示和活动专属小部件。
- 角色以一段 **hook** 开场，再按 tier 对应的回合数引导孩子完成活动。
- 用语音或文字回应均可。沉默被允许；角色会再邀请一次。

### 5. 你会看到什么

- **右侧屏幕每个回合都会变化** —— 进度指示、照片、已收集物件、场景插画，直到最终的庆祝画面。
- Category 5 会话结尾会展示**多场景故事**，每个场景配一张生成插图，随后呈现一张**成就纪念图**。
- 如果某张图生成失败，界面会出现一条柔和的琥珀色横幅 **"Couldn't create this image"**。这是已知的预期回退，请打 flag，帮助我们判断这种回退体验是否足够好。
- 会话以告别语 + **照片回顾网格**收尾，把孩子刚经历的亮点做一次回放。

### 6. 标记一个瞬间（flag）

任何让你觉得"一个真实的孩子在这里会不舒服"的地方 —— 措辞、节奏、视觉 bug —— 或者非常精彩的瞬间，都值得打 flag。你的教育判断正是我们要收集的。

- 点击右下角黄色**旗帜按钮**。
- 会弹出一个小窗口，包含：
  - 自动截取的**当前屏幕截图**。
  - 四个**标签**，可多选：
    - **Tone**（语气）— 声音/措辞不适配该年龄或情境。
    - **Confusing**（困惑）— 真实孩子会在这里跟丢主线。
    - **Bug**（缺陷）— 明显坏掉的东西。
    - **Loved it**（值得保留）— 值得守护的瞬间。
  - 一段**quick note**，一句话补充即可。
- 按 Enter（或 Save）提交；按 Esc 或点击外部取消。
- 之后可以重新打开同一条 flag，编辑标签、备注或追加更长的 review comment。
- 打 flag 不会暂停会话。

### 7. 会话结束后的回顾与提交

- 会话结束后进入**回顾界面**，列出本次所有 flag。
- 每条 flag 可编辑标签、追加一段更长的 **review comment**（沉淀下来的反思，与当时的 quick note 互补）、或删除。
- 两个出口：
  - **Submit to backend**：将反馈包（JSON + 截图）上传到服务器。
  - **Download zip**：将同一份包本地下载，便于另行分享。

### 8. 浏览历史反馈（可选）

- 在落地页照片选择器右上角点击 **"View feedback gallery →"**，或直接访问 `?view=feedback`。
- 画廊为**只读**：可按标签、测试者昵称筛选，也可按新旧排序；点击任一缩略图进入全屏查看。

### 9. 对你尤其有价值的反馈维度

因为你是以教育者的眼光评估，以下这些层面是你输入最能发挥作用的地方：

- **发展适配度**：这档 tier 的难度是否真的匹配相应年龄的孩子？偏成人化还是偏幼稚？
- **邀请式语言**：每句台词是否保持邀请感？任何滑回命令式（"Go find!"、"Tell me!"）都请标记。
- **沉默与错误回应下的支架**：角色是温暖地再邀请，还是让孩子感到被纠正 / 被施压？
- **跨回合的一致性**：叙事弧线是否自洽？角色有没有与前几个回合的设定矛盾？
- **图文一致性**：场景插图与成就图是在强化故事，还是在分散注意？
- **愉悦瞬间**：也请打上 flag —— 这些告诉我们哪些东西绝不能退化。

---

*Last updated / 最近更新：2026-04-20*

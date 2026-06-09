# 家庭考试助手 - 手机端开发文档

> 版本：1.0  
> 日期：2026-06-09  
> 目标平台：Android 6.0+ / iOS 13.0+  
> 技术栈：Flutter 3.x + Dart + sqflite

---

## 一、项目概述

### 1.1 定位

手机端是桌面端「家庭考试助手」的**纯消费端**，类似 VCE Player 的角色：

| 角色 | 功能范围 | 类比 |
|---|---|---|
| **桌面端** (现有项目) | 创建题库、编辑题目、导入导出、管理题库 | VCE Designer |
| **手机端** (本项目) | 导入题库包 → 练习/考试 → 查看结果 | VCE Player |

两者**不直接通信**，通过 ZIP 文件单向传递数据（桌面导出 → 手机导入）。

### 1.2 核心原则

- **完全离线**：导入后无需网络
- **零服务端依赖**：不连接桌面端，不连接云服务
- **只读题库**：手机端不创建/编辑题目，只消费
- **极简交互**：家庭用户友好，老人小孩都能用

---

## 二、功能清单

### 2.1 功能矩阵

| 功能 | P0（核心） | P1（增强） | P2（完善） | 说明 |
|---|:---:|:---:|:---:|---|
| 题库导入（ZIP） | ✅ | | | 从文件系统选择 ZIP 包导入 |
| 题库列表展示 | ✅ | | | 显示已导入的题库 |
| 题库删除 | ✅ | | | 删除已导入的题库 |
| 题库统计信息 | ✅ | | | 显示各题型数量 |
| 练习模式 | ✅ | | | 逐题作答，可查看答案解析 |
| 考试模式 | ✅ | | | 答完自动评分，显示得分 |
| 答案暂存 | ✅ | | | 切题后保留已选答案 |
| 结果页 | ✅ | | | 逐题显示对错 + 解析 |
| 科目/标签筛选 | ✅ | | | 练习/考试前选择范围 |
| 题数限制 | ✅ | | | 指定随机抽几题 |
| 进度条 | ✅ | | | 显示当前进度 |
| 上一题/下一题 | ✅ | | | 题间导航 |
| 题号跳转面板 | | ✅ | | 网格展示所有题号，点击跳转 |
| 标记题目 | | ✅ | | 旗帜标记，方便回顾 |
| 错题重做 | | ✅ | | 结果页"只做错题"按钮 |
| 考试倒计时 | | ✅ | | 考试模式限时提醒 |
| 历史记录 | | ✅ | | 记录每次考试结果 |
| 深色模式 | | | ✅ | 跟随系统 |
| 导出练习记录 | | | ✅ | 分享结果截图/文本 |
| 多题库搜索 | | | ✅ | 跨题库搜索题目 |

### 2.2 不做的功能

以下功能属于桌面端职责，手机端**不实现**：

- 创建/编辑/删除题目
- Excel 导入
- JSON/ZIP 导入导出（除了消费桌面端导出的包）
- 图片上传
- 科目管理（增删改）
- 题库间导出题目
- TinyMCE 富文本编辑器

---

## 三、页面设计

### 3.1 页面总览

```
App
├── 页面1: 题库列表页 (BankListPage)
│   ├── 导入题库（+ 按钮）
│   ├── 题库卡片列表
│   └── 题库删除（长按/滑动）
│
├── 页面2: 题库首页 (BankHomePage)
│   ├── 统计面板
│   ├── 筛选条件（科目/标签/题数）
│   ├── 开始练习按钮
│   └── 开始考试按钮
│
├── 页面3: 答题页 (QuestionPage)
│   ├── 进度条
│   ├── 题目内容区（支持 HTML/公式/图片）
│   ├── 答案选择区
│   ├── 导航按钮（上一题/下一题/交卷）
│   ├── 查看答案按钮（仅练习模式）
│   ├── 答案解析展开区
│   └── [P1] 题号跳转面板
│       └── [P1] 标记旗帜按钮
│
└── 页面4: 结果页 (ResultPage)
    ├── 得分展示
    ├── 用时统计
    ├── 逐题回顾列表
    │   └── 展开查看解析
    ├── [P1] 错题重做按钮
    └── 返回首页按钮
```

### 3.2 页面 1：题库列表页 (BankListPage)

**路由**：`/` (首页)

**UI 布局**：

```
┌──────────────────────────────┐
│  📚 家庭考试助手        [+]  │  ← 右上角导入按钮
├──────────────────────────────┤
│                              │
│  ┌──────────────────────┐    │
│  │ 📖 数学题库          │    │
│  │ 120 题 · 2026-06-01  │    │
│  │ 代数 | 几何 | 概率    │    │
│  └──────────────────────┘    │
│                              │
│  ┌──────────────────────┐    │
│  │ 📖 英语四级          │    │
│  │ 200 题 · 2026-05-20  │    │
│  │ 听力 | 阅读 | 写作    │    │
│  └──────────────────────┘    │
│                              │
│  （空状态）                   │
│  点击右上角 + 导入题库       │
│                              │
└──────────────────────────────┘
```

**功能**：

| 操作 | 触发方式 | 行为 |
|---|---|---|
| 导入题库 | 点击 + 按钮 | 打开文件选择器，选择 ZIP 文件 |
| 进入题库 | 点击卡片 | 跳转到该题库首页 |
| 删除题库 | 长按卡片 / 向左滑动 | 弹出确认对话框，确认后删除 |
| 空状态 | 无题库时 | 显示引导文字"点击 + 导入题库" |

**数据来源**：读取本地 SQLite 元数据表 `imported_banks`

### 3.3 页面 2：题库首页 (BankHomePage)

**路由**：`/bank/:bankId`

**UI 布局**：

```
┌──────────────────────────────┐
│  ← 数学题库                  │  ← 顶部导航栏，返回题库列表
├──────────────────────────────┤
│                              │
│  ┌──────────────────────┐    │
│  │ 单选 40  多选 30      │    │
│  │ 判断 30  填空 15      │    │  ← 统计卡片
│  │ 组题 5组  共 120 题   │    │
│  └──────────────────────┘    │
│                              │
│  筛选条件：                   │
│  ┌─────────┐ ┌─────────┐    │
│  │ 科目 ▾  │ │ 标签 ▾  │    │
│  └─────────┘ └─────────┘    │
│  ┌─────────────────────┐    │
│  │ 题数：[  0  ]（0=全部）│   │
│  └─────────────────────┘    │
│                              │
│  ┌──────────┐ ┌──────────┐  │
│  │  📝       │ │  📋       │  │
│  │  练习模式 │ │  考试模式 │  │
│  │  逐题作答 │ │  答完评分 │  │
│  └──────────┘ └──────────┘  │
│                              │
└──────────────────────────────┘
```

**功能**：

| 操作 | 行为 |
|---|---|
| 选择科目 | 下拉框，选项来自 `subjects` 表，默认"全部" |
| 选择标签 | 下拉框，选项为题库中所有去重 tag 值，默认"全部" |
| 设置题数 | 数字输入框，0 表示抽全部题 |
| 开始练习 | 根据筛选条件抽取题目，进入练习模式 |
| 开始考试 | 根据筛选条件抽取题目，进入考试模式 |
| 返回 | 回到题库列表页 |

**题目抽取逻辑**（与桌面端 `_select_question_ids` 一致）：

```sql
SELECT id FROM questions 
WHERE is_subquestion = 0
  AND (:subject_id IS NULL OR subject_id = :subject_id)
  AND (:tag IS NULL OR tag = :tag)
ORDER BY RANDOM()
LIMIT :count  -- count=0 时不加 LIMIT
```

### 3.4 页面 3：答题页 (QuestionPage)

**路由**：`/session/question`（练习和考试共用此页面，通过 mode 参数区分）

**UI 布局**：

```
┌──────────────────────────────┐
│ ████████░░░░░░  3/10        │  ← 进度条 + 题号
├──────────────────────────────┤
│                              │
│  [单选题] [简单] [代数]       │  ← 题型 + 难度 + 科目标签
│                              │
│  下列哪个是质数？             │  ← 题干（支持 HTML 渲染）
│  （此处可能有图片）           │
│                              │
│  ┌─── 选项区 ──────────────┐ │
│  │ ○ A. 4                  │ │
│  │ ● B. 7    ← 选中高亮    │ │
│  │ ○ C. 9                  │ │
│  │ ○ D. 15                 │ │
│  └─────────────────────────┘ │
│                              │
│  ── 练习模式专属 ────────── │
│  ┌─── 答案解析区 ──────────┐ │
│  │ ✅ 正确答案: B          │ │  ← 点击"查看答案"后展开
│  │ 📝 解析：7 只能被...    │ │
│  └─────────────────────────┘ │
│                              │
│  [← 上一题]  [查看答案]  [下一题 →] │  ← 练习模式
│  [← 上一题]  [交卷 📋]          │  ← 考试模式最后一题
│                              │
└──────────────────────────────┘
```

**各题型的答案交互**：

| 题型 | 交互方式 | 说明 |
|---|---|---|
| `single_choice` | 单选，点击即选中，自动取消之前的选择 | 高亮当前选中项 |
| `multi_choice` | 多选，点击切换选中/取消 | 提示"选择所有正确答案"；底部显示已选（如"A, C"） |
| `true_false` | 二选一，"A. 正确" / "B. 错误" | 同单选交互 |
| `fill_blank` | 文本输入框 | 弹出键盘，回车确认 |
| `composite` | 展开子题列表 | 每个子题按各自题型独立渲染，分别作答 |

**组合题的渲染**：

```
┌──────────────────────────────┐
│  [组合题] [中等] [几何]       │
│                              │
│  阅读以下材料，回答 3 个问题。 │  ← 大题干
│                              │
│  ┌── 第 1 小题 ───────────┐  │
│  │ [单选题]                │  │
│  │ 小题题干...             │  │
│  │ ○ A ...  ● B ...       │  │
│  └─────────────────────────┘  │
│                              │
│  ┌── 第 2 小题 ───────────┐  │
│  │ [填空题]                │  │
│  │ 小题题干...             │  │
│  │ [输入框________]        │  │
│  └─────────────────────────┘  │
│                              │
│  ...更多子题...               │
└──────────────────────────────┘
```

**练习模式 vs 考试模式差异**：

| 行为 | 练习模式 | 考试模式 |
|---|---|---|
| 查看答案按钮 | ✅ 显示，点击展开答案+解析 | ❌ 不显示 |
| 导航最后一步 | "完成练习 ✓" | "交卷 📋"（需二次确认） |
| 答案校验 | 逐题即时反馈（可选） | 全部答完后统一评分 |
| 成绩保存 | 不保存 | 保存到历史记录 |

### 3.5 页面 4：结果页 (ResultPage)

**路由**：`/session/result`

**UI 布局**：

```
┌──────────────────────────────┐
│        考试结果               │
│                              │
│          85                  │  ← 大号得分（考试模式）
│          分                  │
│                              │
│  原始得分：17.0 / 20.0       │
│  正确 17 题 / 共 20 题       │
│  用时 15 分 30 秒            │
│  正确率 85.0%                │
│                              │
│  ┌──────────────────────┐    │
│  │ [展开全部] [收起全部] │    │
│  │ [P1: 错题重做]       │    │
│  └──────────────────────┘    │
│                              │
│  ┌── ✓ 第1题 ────────────┐  │
│  │ [单选题] 2.0/2.0 分   │  │
│  │ 题干内容...           │  │
│  │ A. 4   B. 7 ✓        │  │
│  │ 你的答案: B ✓         │  │
│  └──────────────────────┘   │
│                              │
│  ┌── ✗ 第2题 ────────────┐  │
│  │ [多选题] 0/3 分       │  │
│  │ 题干内容...           │  │
│  │ A. x   B. ✓   C. x   │  │
│  │ 你的: A,B  正确: B,C  │  │
│  │ ▼ 展开解析            │  │
│  └──────────────────────┘   │
│                              │
│  ┌──────────────────────┐    │
│  │    [ 返回首页 ]       │    │
│  └──────────────────────┘    │
└──────────────────────────────┘
```

**练习模式结果差异**：

```
练习结果不显示"分"的大数字，而是：
          17 / 20
          题正确
```

**选项的视觉标记规则**（与桌面端 `result.html` 一致）：

| 情况 | 显示方式 |
|---|---|
| 正确答案选项 | 绿色加粗 + ✓ |
| 用户错选的选项 | 红色 + 删除线 |
| 用户未选但正确的 | 绿色 |
| 普通未选选项 | 默认灰色 |

---

## 四、数据格式

### 4.1 导入包格式

手机端直接使用桌面端现有的 ZIP 导出格式，**不新增任何格式**。

#### ZIP 包结构

```
数学题库.zip                    ← 桌面端 /export 路由生成
├── bank.json                  ← 题库数据（JSON）
├── manifest.json              ← 元数据 + 资源映射
└── assets/                    ← 图片资源
    ├── a1b2c3d4e5f6.png
    ├── f7e8d9c0b1a2.jpg
    └── ...
```

#### bank.json 结构

```jsonc
{
  // 包标识
  "format": "family-exam-helper",    // 固定值，用于校验
  "version": 2,                       // 格式版本号
  "bank_name": "数学题库",            // 题库显示名称
  "exported_at": "2026-06-09T10:30:00",

  // 科目列表
  "subjects": [
    {"id": 1, "name": "代数"},
    {"id": 2, "name": "几何"}
  ],

  // 题目列表
  "questions": [
    // ---- 单选题 ----
    {
      "subject": "代数",              // 科目名（字符串，非 ID）
      "tag": "第一章",                // 标签
      "type": "single_choice",        // 题型
      "difficulty": 1,                // 难度 1=简单 2=中等 3=困难
      "score": 2,                     // 分值（可为 null，null 时使用默认分值）
      "content": "<p>1+1=?</p>",      // 题干（HTML）
      "options": [                    // 选项列表
        {"label": "A", "content": "1"},
        {"label": "B", "content": "2"},
        {"label": "C", "content": "3"},
        {"label": "D", "content": "4"}
      ],
      "answer": "B",                  // 正确答案
      "explanation": "<p>1+1=2</p>"   // 解析（HTML）
    },

    // ---- 多选题 ----
    {
      "subject": "代数",
      "tag": "",
      "type": "multi_choice",
      "difficulty": 2,
      "score": 3,
      "content": "<p>下列哪些是质数？</p>",
      "options": [
        {"label": "A", "content": "4"},
        {"label": "B", "content": "7"},
        {"label": "C", "content": "9"},
        {"label": "D", "content": "11"}
      ],
      "answer": "B,D",               // 多选答案逗号分隔
      "explanation": ""
    },

    // ---- 判断题 ----
    {
      "subject": "",
      "tag": "",
      "type": "true_false",
      "difficulty": 1,
      "score": 1,
      "content": "<p>地球是平的</p>",
      "options": [],                  // 判断题 options 为空数组
      "answer": "B",                  // A=正确 B=错误
      "explanation": ""
    },

    // ---- 填空题 ----
    {
      "subject": "",
      "tag": "",
      "type": "fill_blank",
      "difficulty": 2,
      "score": 2,
      "content": "<p>中国的首都是___</p>",
      "options": [],
      "answer": "北京",               // 多个可接受答案用 | 分隔，如 "北京|BJ"
      "explanation": ""
    },

    // ---- 组合题 ----
    {
      "subject": "几何",
      "tag": "三角形",
      "type": "composite",
      "difficulty": 3,
      "score": null,                  // 组合题本身无分值
      "content": "<p>已知三角形ABC中...</p>",   // 大题干
      "options": [],
      "answer": "",                   // 组合题本身无答案
      "explanation": "<p>整体解析...</p>",
      "children": [                   // 子题列表
        {
          "type": "single_choice",
          "difficulty": 3,
          "score": 3,
          "content": "<p>角A的度数是？</p>",
          "options": [
            {"label": "A", "content": "30°"},
            {"label": "B", "content": "45°"},
            {"label": "C", "content": "60°"},
            {"label": "D", "content": "90°"}
          ],
          "answer": "C",
          "explanation": ""
        },
        {
          "type": "fill_blank",
          "difficulty": 3,
          "score": 2,
          "content": "<p>边AB的长度是___cm</p>",
          "options": [],
          "answer": "5",
          "explanation": ""
        }
      ]
    }
  ]
}
```

#### manifest.json 结构

```jsonc
{
  "format": "family-exam-helper-package",
  "version": 1,
  "assets": [
    {
      "type": "bank",                 // "bank" 或 "legacy"
      "bank_filename": "xxx.db",      // 来源题库文件名
      "filename": "original.png",     // 原始文件名
      "archive_name": "assets/uuid.png"  // ZIP 内路径
    }
  ]
}
```

#### 图片引用路径格式

题目 HTML 中的图片以如下格式引用：

```html
<img src="/bank-assets/212c7c55.db/a1b2c3d4.png">
```

手机端导入时需要将这些路径**重写为本地文件路径**。

### 4.2 题型枚举

| type 值 | 中文名 | 可作答 | 选项 | 答案格式 |
|---|---|:---:|:---:|---|
| `single_choice` | 单选题 | ✅ | 有 | 单字母如 `"B"` |
| `multi_choice` | 多选题 | ✅ | 有 | 逗号分隔如 `"B,D"` |
| `true_false` | 判断题 | ✅ | 无（固定 A=正确 B=错误） | `"A"` 或 `"B"` |
| `fill_blank` | 填空题 | ✅ | 无 | 文本，多个答案 `\|` 分隔如 `"北京\|BJ"` |
| `composite` | 组合题 | ❌ (容器) | 无 | 空，子题各自独立 |

### 4.3 难度映射

| difficulty | 显示 |
|:---:|---|
| 1 | 简单 |
| 2 | 中等 |
| 3 | 困难 |

### 4.4 默认分值

当题目的 `score` 为 `null` 时，使用以下默认值（与桌面端 `scoring_config.json` 一致）：

| 题型 | 默认分值 |
|---|:---:|
| `single_choice` | 2 |
| `multi_choice` | 3 |
| `true_false` | 1 |
| `fill_blank` | 2 |
| `composite` | 0（子题各自计分） |

---

## 五、数据层设计

### 5.1 本地存储架构

手机端将导入的 JSON 数据解析后存入本地 SQLite 数据库，结构基本复用桌面端的表结构。

```
应用沙箱目录/
├── databases/
│   └── exam_helper.db        ← 主数据库（元数据 + 所有题库数据）
├── bank_assets/
│   ├── <bank_uuid>/           ← 每个题库的图片目录
│   │   ├── a1b2c3.png
│   │   └── d4e5f6.jpg
│   └── <bank_uuid>/
│       └── ...
└── ...（Flutter 框架文件）
```

### 5.2 数据库 Schema

#### 表：imported_banks（已导入题库元数据）

```sql
CREATE TABLE imported_banks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_name       TEXT NOT NULL,               -- 题库显示名称
    import_path     TEXT NOT NULL,               -- 图片目录路径
    imported_at     TEXT NOT NULL DEFAULT (datetime('now')),
    last_used_at    TEXT,                        -- 最后使用时间
    source_version  INTEGER DEFAULT 2,           -- 导出包版本号
    -- 统计字段（导入时预计算，避免每次查询）
    total_questions     INTEGER DEFAULT 0,
    single_choice_count INTEGER DEFAULT 0,
    multi_choice_count  INTEGER DEFAULT 0,
    true_false_count    INTEGER DEFAULT 0,
    fill_blank_count    INTEGER DEFAULT 0,
    composite_count     INTEGER DEFAULT 0
);
```

#### 表：subjects（科目，按题库隔离）

```sql
CREATE TABLE subjects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_id     INTEGER NOT NULL,               -- 关联 imported_banks.id
    name        TEXT NOT NULL,
    UNIQUE(bank_id, name),
    FOREIGN KEY (bank_id) REFERENCES imported_banks(id) ON DELETE CASCADE
);
```

#### 表：questions（题目，按题库隔离）

```sql
CREATE TABLE questions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_id         INTEGER NOT NULL,               -- 关联 imported_banks.id
    subject_id      INTEGER,                         -- 关联 subjects.id（可为空）
    tag             TEXT DEFAULT '',
    type            TEXT NOT NULL,                    -- 题型枚举值
    difficulty      INTEGER DEFAULT 1 CHECK(difficulty BETWEEN 1 AND 3),
    content         TEXT NOT NULL DEFAULT '',          -- 题干 HTML
    options         TEXT DEFAULT '[]',                -- JSON 数组
    answer          TEXT NOT NULL DEFAULT '',
    explanation     TEXT DEFAULT '',                   -- 解析 HTML
    score           REAL,                              -- 分值（null=使用默认）
    parent_id       INTEGER DEFAULT NULL,             -- 组合题：父题 ID
    sort_order      INTEGER DEFAULT 0,                -- 组合题：子题顺序
    is_subquestion  INTEGER DEFAULT 0,
    FOREIGN KEY (bank_id)     REFERENCES imported_banks(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id)  REFERENCES subjects(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_id)   REFERENCES questions(id) ON DELETE CASCADE
);

CREATE INDEX idx_questions_bank    ON questions(bank_id);
CREATE INDEX idx_questions_subject ON questions(bank_id, subject_id);
CREATE INDEX idx_questions_type    ON questions(bank_id, type);
CREATE INDEX idx_questions_tag     ON questions(bank_id, tag);
CREATE INDEX idx_questions_parent  ON questions(bank_id, parent_id, sort_order);
```

#### 表：exam_sessions（考试历史记录，P1）

```sql
CREATE TABLE exam_sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_id         INTEGER NOT NULL,
    mode            TEXT NOT NULL,                 -- 'practice' 或 'exam'
    subject_id      INTEGER,
    tag             TEXT DEFAULT '',
    total_questions INTEGER DEFAULT 0,
    correct_count   INTEGER DEFAULT 0,
    score           REAL DEFAULT 0,               -- 实际得分
    total_score     REAL DEFAULT 0,               -- 满分
    duration_seconds INTEGER DEFAULT 0,
    answers         TEXT DEFAULT '{}',             -- JSON：{qid: answer}
    created_at      TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (bank_id) REFERENCES imported_banks(id) ON DELETE CASCADE
);
```

### 5.3 导入流程

```
用户选择 ZIP 文件
       │
       ▼
┌─ 校验阶段 ─────────────────┐
│ 1. 打开 ZIP                │
│ 2. 检查 bank.json 存在     │
│ 3. 检查 format ==          │
│    "family-exam-helper"    │
│ 4. 检查 version >= 2       │
│ 校验失败 → 弹出错误提示     │
└────────────────────────────┘
       │
       ▼
┌─ 导入阶段 ─────────────────┐
│ 1. 解析 bank.json          │
│ 2. 创建 imported_banks 记录│
│ 3. 导入 subjects           │
│ 4. 遍历 questions：        │
│    a. 普通题 → 直接插入     │
│    b. composite → 先插入父题│
│       再插入 children       │
│ 5. 解压 assets/ 到本地     │
│ 6. 重写 content/explanation│
│    中的图片路径为本地路径    │
└────────────────────────────┘
       │
       ▼
┌─ 完成阶段 ─────────────────┐
│ 1. 预计算统计数据           │
│ 2. 更新 imported_banks     │
│ 3. 返回题库列表页           │
└────────────────────────────┘
```

### 5.4 图片路径重写

桌面端导出的题目 HTML 中图片路径格式：

```
/bank-assets/212c7c5541964c8fb84e739865e436aa.db/a1b2c3d4.png
```

手机端导入时重写为本地路径：

```
assets/<bank_uuid>/a1b2c3d4.png
```

同时，ZIP 包内图片文件名已经是随机 UUID，导出时已去掉了 `.db` 后缀关联，所以只需：

1. 解压 `assets/*` 到 `<应用目录>/bank_assets/<bank_uuid>/`
2. 将 HTML 中的 `/bank-assets/.../*.png` 替换为 `<bank_uuid>/filename.png`（相对路径）
3. 渲染时拼接完整本地路径

### 5.5 答案校验逻辑

与桌面端 `_check_answer` 完全一致：

```dart
bool checkAnswer(String type, String correctAnswer, String userAnswer) {
  if (userAnswer.isEmpty) return false;
  userAnswer = userAnswer.trim();
  correctAnswer = correctAnswer.trim();

  switch (type) {
    case 'fill_blank':
      // 多个可接受答案用 | 分隔，不区分大小写
      final acceptable = correctAnswer
          .split('|')
          .map((a) => a.trim().toLowerCase());
      return acceptable.contains(userAnswer.toLowerCase());

    case 'multi_choice':
      // 所有正确选项必须选中，不能多选也不能少选
      final correctSet = _normalizeMultiAnswer(correctAnswer);
      final userSet = _normalizeMultiAnswer(userAnswer);
      return correctSet.length == userSet.length &&
          correctSet.containsAll(userSet);

    default:
      // single_choice, true_false: 不区分大小写
      return userAnswer.toUpperCase() == correctAnswer.toUpperCase();
  }
}

Set<String> _normalizeMultiAnswer(String answer) {
  return answer
      .split(RegExp(r'[,，\s]+'))
      .where((s) => s.isNotEmpty)
      .map((s) => s.trim().toUpperCase())
      .toSet();
}
```

### 5.6 得分计算

与桌面端逻辑一致：

```
每题得分 = 答对 ? 分值 : 0
总分   = 各题得分之和
满分   = 各题分值之和
百分制 = round(总分 / 满分 * 100)
```

分值解析优先级：
1. 题目自带的 `score` 字段（非 null 时使用）
2. 按题型查默认分值表

组合题得分 = 所有子题得分之和。

---

## 六、模块架构

### 6.1 项目结构

```
lib/
├── main.dart                          ← 入口
├── app.dart                           ← MaterialApp 配置 + 路由
│
├── models/                            ← 数据模型
│   ├── bank.dart                      ← Bank（题库元数据）
│   ├── question.dart                  ← Question（题目）
│   ├── subject.dart                   ← Subject（科目）
│   ├── exam_session.dart              ← ExamSession（考试记录）
│   └── session_state.dart             ← 练习/考试会话状态
│
├── services/                          ← 服务层
│   ├── database_service.dart          ← SQLite 数据库操作
│   ├── import_service.dart            ← ZIP 导入 + 解析
│   ├── asset_service.dart             ← 图片路径管理
│   └── scoring_service.dart           ← 答案校验 + 得分计算
│
├── pages/                             ← 页面
│   ├── bank_list_page.dart            ← 页面1：题库列表
│   ├── bank_home_page.dart            ← 页面2：题库首页
│   ├── question_page.dart             ← 页面3：答题页
│   └── result_page.dart               ← 页面4：结果页
│
├── widgets/                           ← 可复用组件
│   ├── question_content.dart          ← 题干渲染（HTML + 公式 + 图片）
│   ├── option_group.dart              ← 选项组（单选/多选/判断）
│   ├── fill_blank_input.dart          ← 填空题输入框
│   ├── composite_question.dart        ← 组合题渲染
│   ├── progress_indicator.dart        ← 进度条
│   ├── score_display.dart             ← 得分展示
│   ├── result_item.dart               ← 结果逐题项
│   ├── bank_card.dart                 ← 题库卡片
│   └── stats_card.dart               ← 统计面板
│
├── utils/                             ← 工具函数
│   ├── constants.dart                 ← 常量定义（题型、难度、默认分值）
│   ├── html_renderer.dart             ← HTML 渲染工具
│   └── time_format.dart               ← 时间格式化
│
└── theme/                             ← 主题配置
    ├── app_theme.dart                 ← 亮色主题
    └── app_theme_dark.dart            ← [P2] 暗色主题
```

### 6.2 依赖包

```yaml
dependencies:
  flutter:
    sdk: flutter

  # 数据库
  sqflite: ^2.3.0                    # SQLite 操作
  path: ^1.8.0                       # 路径处理

  # 文件操作
  path_provider: ^2.1.0              # 应用目录路径
  file_picker: ^8.0.0                # 文件选择器（选择 ZIP）
  archive: ^4.0.0                    # ZIP 解压

  # UI 组件
  flutter_widget_from_html: ^0.15.0  # HTML 渲染（含图片）
  flutter_math_fork: ^0.7.0          # 数学公式渲染（LaTeX → Widget）

  # 状态管理
  provider: ^6.1.0                   # 轻量状态管理

  # 其他
  uuid: ^4.4.0                       # UUID 生成
  share_plus: ^9.0.0                 # [P2] 分享功能
  intl: ^0.19.0                      # 国际化/日期格式
```

### 6.3 状态管理

使用 Provider 管理练习/考试会话状态：

```dart
/// 练习/考试会话状态
class SessionModel extends ChangeNotifier {
  String mode;                       // 'practice' | 'exam'
  List<Question> questions;          // 当前会话的题目列表
  int currentIndex;                  // 当前题号
  Map<int, String> answers;          // {questionId: userAnswer}
  Map<int, String> compositeAnswers; // 组合题子题答案
  DateTime startTime;                // 开始时间
  Set<int> flaggedQuestions;         // [P1] 标记的题目

  // 导航
  void nextQuestion() { ... }
  void prevQuestion() { ... }
  void jumpToQuestion(int index) { ... }

  // 答题
  void setAnswer(int questionId, String answer) { ... }
  void setCompositeAnswer(int questionId, Map<String, String> subAnswers) { ... }

  // 标记
  void toggleFlag(int questionId) { ... }  // [P1]

  // 结果
  SessionResult calculateResult() { ... }
}
```

---

## 七、关键实现细节

### 7.1 HTML 渲染

题目内容和解析是 HTML 格式，可能包含：

| 内容类型 | 示例 | 处理方式 |
|---|---|---|
| 纯文本 | `1+1=?` | 直接显示 |
| HTML 标签 | `<p>1+<strong>1</strong>=?</p>` | `flutter_widget_from_html` 渲染 |
| 行内公式 | `\(x^2\)` | `flutter_math_fork` 渲染 |
| 块级公式 | `$$E=mc^2$$` | `flutter_math_fork` 渲染 |
| 图片 | `<img src="/bank-assets/...">` | 重写路径后本地加载 |
| 代码块 | `<pre><code>...</code></pre>` | `flutter_widget_from_html` 自带代码样式 |

**推荐方案**：使用 `flutter_widget_from_html` 作为主渲染器，配合自定义的 `customWidgetBuilder` 处理 LaTeX 公式。图片通过 `customRendererBuilder` 将路径指向本地文件。

### 7.2 导入文件选择

```dart
// Android: 使用 file_picker 选择 .zip 文件
final result = await FilePicker.platform.pickFiles(
  type: FileType.custom,
  allowedExtensions: ['zip'],
);

// iOS: 同上，file_picker 也支持 iOS 的文档选择器
```

### 7.3 ZIP 导入流程（伪代码）

```dart
Future<Bank> importBank(String zipPath) async {
  // 1. 解压 ZIP 到临时目录
  final tempDir = await getTemporaryDirectory();
  final bytes = File(zipPath).readAsBytesSync();
  final archive = ZipDecoder().decodeBytes(bytes);

  // 2. 读取并校验 bank.json
  final bankJsonFile = archive.findFile('bank.json');
  final bankData = jsonDecode(utf8.decode(bankJsonFile.content));
  if (bankData['format'] != 'family-exam-helper') {
    throw FormatException('不是有效的题库包');
  }

  // 3. 创建题库记录
  final bankId = await db.insert('imported_banks', {
    'bank_name': bankData['bank_name'],
    'source_version': bankData['version'],
    // ...
  });

  // 4. 创建本地图片目录
  final assetDir = await _createBankAssetDir(bankId);

  // 5. 解压 assets/ 到本地
  for (final file in archive) {
    if (file.name.startsWith('assets/')) {
      final filename = path.basename(file.name);
      File(path.join(assetDir.path, filename))
          .writeAsBytesSync(file.content as List<int>);
    }
  }

  // 6. 导入科目
  final subjectMap = <String, int>{};
  for (final s in bankData['subjects'] ?? []) {
    final id = await db.insert('subjects', {
      'bank_id': bankId,
      'name': s['name'],
    });
    subjectMap[s['name']] = id;
  }

  // 7. 导入题目
  for (final q in bankData['questions'] ?? []) {
    // 重写图片路径
    final content = _rewriteAssetPaths(q['content'], bankId);
    final explanation = _rewriteAssetPaths(q['explanation'], bankId);

    if (q['type'] == 'composite') {
      // 插入父题
      final parentId = await db.insert('questions', {
        'bank_id': bankId,
        'subject_id': subjectMap[q['subject']],
        'tag': q['tag'] ?? '',
        'type': 'composite',
        'difficulty': q['difficulty'] ?? 1,
        'content': content,
        'options': '[]',
        'answer': '',
        'explanation': explanation,
        'score': null,
        'is_subquestion': 0,
      });
      // 插入子题
      for (var i = 0; i < (q['children'] ?? []).length; i++) {
        final child = q['children'][i];
        await db.insert('questions', {
          'bank_id': bankId,
          'subject_id': subjectMap[q['subject']],
          'tag': q['tag'] ?? '',
          'type': child['type'],
          'difficulty': child['difficulty'] ?? q['difficulty'] ?? 1,
          'content': _rewriteAssetPaths(child['content'], bankId),
          'options': jsonEncode(child['options'] ?? []),
          'answer': child['answer'] ?? '',
          'explanation': _rewriteAssetPaths(child['explanation'] ?? '', bankId),
          'score': child['score'],
          'parent_id': parentId,
          'sort_order': i + 1,
          'is_subquestion': 1,
        });
      }
    } else {
      // 插入普通题
      await db.insert('questions', {
        'bank_id': bankId,
        'subject_id': subjectMap[q['subject']],
        'tag': q['tag'] ?? '',
        'type': q['type'],
        'difficulty': q['difficulty'] ?? 1,
        'content': content,
        'options': jsonEncode(q['options'] ?? []),
        'answer': q['answer'] ?? '',
        'explanation': explanation,
        'score': q['score'],
        'is_subquestion': 0,
      });
    }
  }

  // 8. 预计算统计
  await _updateBankStats(bankId);

  return await getBank(bankId);
}
```

### 7.4 题目加载（与桌面端对齐）

```dart
/// 加载一道完整题目（含子题），等价于桌面端 _load_question_unit
Future<Question?> loadQuestion(int bankId, int questionId) async {
  final rows = await db.query(
    'questions',
    where: 'bank_id = ? AND id = ? AND is_subquestion = 0',
    whereArgs: [bankId, questionId],
  );
  if (rows.isEmpty) return null;

  final question = Question.fromRow(rows.first);

  if (question.type == 'composite') {
    final children = await db.query(
      'questions',
      where: 'bank_id = ? AND parent_id = ?',
      whereArgs: [bankId, questionId],
      orderBy: 'sort_order, id',
    );
    question.children = children.map((r) => Question.fromRow(r)).toList();
  }

  return question;
}

/// 随机抽取题目 ID 列表，等价于桌面端 _select_question_ids
Future<List<int>> selectQuestionIds(int bankId, {
  int? subjectId,
  String? tag,
  int count = 0,
}) async {
  String where = 'bank_id = ? AND is_subquestion = 0';
  List args = [bankId];

  if (subjectId != null) {
    where += ' AND subject_id = ?';
    args.add(subjectId);
  }
  if (tag != null && tag.isNotEmpty) {
    where += ' AND tag = ?';
    args.add(tag);
  }

  String sql = 'SELECT id FROM questions WHERE $where ORDER BY RANDOM()';
  if (count > 0) {
    sql += ' LIMIT ?';
    args.add(count);
  }

  final rows = await db.rawQuery(sql, args);
  return rows.map((r) => r['id'] as int).toList();
}
```

---

## 八、主题与配色

### 8.1 色彩方案（与桌面端一致）

| 用途 | 色值 | 说明 |
|---|---|---|
| Primary | `#4A6FA5` | 主色（导航栏、按钮） |
| Primary Dark | `#34507A` | 按钮按下态 |
| Success | `#28A745` | 正确、练习按钮 |
| Danger | `#DC3545` | 错误、交卷按钮 |
| Warning | `#F0AD4E` | 查看答案按钮 |
| Background | `#F5F7FA` | 页面背景 |
| Card Background | `#FFFFFF` | 卡片背景 |
| Border | `#E0E4E8` | 边框线 |
| Text | `#333333` | 主文字 |
| Text Muted | `#6C757D` | 次要文字 |

### 8.2 字体

- 中文：系统默认（PingFang SC / Noto Sans CJK）
- 代码：`Fira Code` / `Consolas`
- 数学公式：`flutter_math_fork` 内置字体

---

## 九、开发里程碑

### Phase 1：核心功能（P0，约 7-10 天）

| 序号 | 任务 | 预估工时 |
|---|---|---|
| 1 | Flutter 项目初始化 + 依赖配置 | 2h |
| 2 | 数据层搭建（models + database_service） | 1 天 |
| 3 | 导入服务（ZIP 解析 + 数据入库 + 图片路径重写） | 1 天 |
| 4 | 题库列表页 | 4h |
| 5 | 题库首页（统计 + 筛选） | 4h |
| 6 | 答题页 - 基础题型（单选/多选/判断/填空） | 1.5 天 |
| 7 | 答题页 - 组合题 | 4h |
| 8 | 结果页 | 4h |
| 9 | HTML + 数学公式渲染 | 4h |
| 10 | 集成测试 + Bug 修复 | 1 天 |

### Phase 2：增强功能（P1，约 5-7 天）

| 序号 | 任务 | 预估工时 |
|---|---|---|
| 1 | 题号跳转面板 | 4h |
| 2 | 标记题目功能 | 2h |
| 3 | 错题重做 | 3h |
| 4 | 考试倒计时 | 3h |
| 5 | 历史记录页面 | 4h |
| 6 | 会话保存/恢复 | 4h |

### Phase 3：打磨完善（P2，约 3-5 天）

| 序号 | 任务 | 预估工时 |
|---|---|---|
| 1 | 深色模式 | 4h |
| 2 | 分享练习结果 | 2h |
| 3 | 动画优化（翻页、选项反馈） | 4h |
| 4 | 性能优化（大题库加载） | 3h |
| 5 | 无障碍适配 | 3h |

---

## 附录 A：桌面端导出操作说明（给用户看）

1. 打开桌面端「家庭考试助手」
2. 选择要导出的题库
3. 点击「导出」按钮
4. 浏览器下载 ZIP 文件
5. 将 ZIP 文件通过微信/QQ/数据线传到手机
6. 手机端打开 APP → 点击 + 号 → 选择该 ZIP 文件

## 附录 B：与桌面端的功能对照表

| 功能 | 桌面端 | 手机端 |
|---|:---:|:---:|
| 创建题库 | ✅ | ❌ |
| 删除题库 | ✅ | ✅ |
| 添加/编辑/删除题目 | ✅ | ❌ |
| Excel 导入题目 | ✅ | ❌ |
| JSON/ZIP 导出题目 | ✅ | ❌ |
| 导入题库包（ZIP） | ✅ | ✅ |
| 练习模式 | ✅ | ✅ |
| 考试模式 | ✅ | ✅ |
| 查看解析 | ✅ | ✅ |
| 按科目/标签筛选 | ✅ | ✅ |
| 随机抽题 | ✅ | ✅ |
| 考试评分 | ✅ | ✅ |
| 考试历史记录 | ✅ | ✅ |
| 题号跳转 | ❌ | ✅ (P1) |
| 错题重做 | ❌ | ✅ (P1) |
| 数学公式渲染 | ✅ | ✅ |
| 代码高亮 | ✅ | ✅ |
| 图片支持 | ✅ | ✅ |
| 组合题 | ✅ | ✅ |

## 附录 C：错误码参考

| 错误码 | 含义 | 触发场景 |
|---|---|---|
| `E001` | 无效的导入包格式 | bank.json 中 format 字段不匹配 |
| `E002` | 缺少 bank.json | ZIP 中没有 bank.json 文件 |
| `E003` | 版本不兼容 | 导出包 version 低于手机端支持的最小版本 |
| `E004` | 题库为空 | bank.json 中 questions 为空数组 |
| `E005` | 解压失败 | ZIP 文件损坏 |
| `E006` | 磁盘空间不足 | 导入时存储空间不够 |
| `E007` | 题库已存在 | 同名题库已导入（提示是否覆盖） |

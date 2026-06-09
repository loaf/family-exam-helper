# 标准导入模板规范

本规范用于将第三方系统中的题目转换为家庭考试助手可导入的标准模板。

## 1. 容器格式

- 推荐使用 `ZIP` 文件，适用于包含图片资源的题目。
- 无图片场景可以直接使用单个 `JSON` 文件。

### ZIP 目录结构

```text
your-package.zip
├─ template.json
└─ assets/
   ├─ figure-1.png
   ├─ detail-1.png
   └─ ...
```

## 2. 顶层字段

`template.json` 顶层结构如下：

```json
{
  "format": "family-exam-helper-template",
  "version": 1,
  "subjects": ["数学", "物理"],
  "questions": []
}
```

字段说明：

- `format`: 必填，固定为 `family-exam-helper-template`
- `version`: 必填，当前固定为 `1`
- `subjects`: 可选，科目名称数组；也可只在每道题里写 `subject`
- `questions`: 必填，题目数组

## 3. 题目结构

普通题和组合题共用同一个数组入口。

### 3.1 普通题

```json
{
  "subject": "物理",
  "tag": "力学",
  "type": "single_choice",
  "difficulty": 1,
  "score": 2,
  "content": "<p>力的国际单位是？</p>",
  "options": [
    { "label": "A", "content": "<p>牛顿</p>" },
    { "label": "B", "content": "<p>焦耳</p>" }
  ],
  "answer": "A",
  "explanation": "<p>力的国际单位是牛顿。</p>"
}
```

### 3.2 组合题

```json
{
  "subject": "数学",
  "tag": "几何,组合题",
  "type": "composite",
  "difficulty": 2,
  "content": "<p>阅读材料：</p><p><img src=\"assets/figure-1.png\"></p>",
  "explanation": "<p>整组解析</p>",
  "children": [
    {
      "type": "single_choice",
      "difficulty": 2,
      "score": 3,
      "content": "<p>根据图形判断，正确的是：</p>",
      "options": [
        { "label": "A", "content": "<p>选项A</p>" },
        { "label": "B", "content": "<p>选项B</p>" }
      ],
      "answer": "A",
      "explanation": "<p>小题解析</p>"
    }
  ]
}
```

## 4. 字段定义

每道题支持以下字段：

- `subject`: 可选，科目名称
- `tag`: 可选，标签文本
- `type`: 必填，支持：
  - `single_choice`
  - `multi_choice`
  - `true_false`
  - `fill_blank`
  - `composite`
- `difficulty`: 可选，`1` / `2` / `3`
- `score`: 可选，正数；留空时按系统默认分值
- `content`: 必填，HTML 字符串
- `options`: 选项数组；判断题和填空题可为空数组
- `answer`: 必填
- `explanation`: 可选，HTML 字符串

### 组合题专属字段

- `children`: 必填，小题数组

### 小题字段

组合题的 `children` 中每个小题支持：

- `type`
- `difficulty`
- `score`
- `content`
- `options`
- `answer`
- `explanation`

小题不需要单独写 `subject` 和 `tag`。

## 5. 答案格式

- 单选题：`"A"`
- 多选题：`"A,B,D"`
- 判断题：
  - `"A"` 表示正确
  - `"B"` 表示错误
- 填空题：
  - 单个答案：`"牛顿"`
  - 多个可接受答案：`"牛顿|N"`

## 6. 图片引用规则

- 图片文件统一放在 ZIP 内的 `assets/` 目录
- HTML 中图片引用建议写为：
  - `assets/figure-1.png`
  - `./assets/figure-1.png`
- 导入时系统会自动：
  - 将图片复制到当前题库资源目录
  - 把 HTML 中的相对路径替换为题库内可访问地址

不建议写：

- 绝对磁盘路径
- 网络 URL
- `../assets/...`

## 7. 选项格式

选项必须使用数组，不建议使用对象。

```json
[
  { "label": "A", "content": "<p>选项A</p>" },
  { "label": "B", "content": "<p>选项B</p>" }
]
```

建议：

- `label` 使用大写字母 `A` `B` `C` `D`
- `content` 使用 HTML 字符串，便于带图和富文本

## 8. 兼容建议

- 所有富文本字段统一使用 UTF-8 编码
- 建议第三方工具输出稳定字段顺序，便于排查问题
- 建议第三方工具优先输出 ZIP，而不是 JSON
- 如无图片，也可只输出单个 `template.json`

## 9. 错误排查

导入失败时优先检查：

- `format` 是否正确
- ZIP 内是否包含 `template.json`
- `assets/` 中图片文件名是否与 HTML 引用一致
- `children` 是否只出现在 `type = composite` 的父题上
- `options` 是否为数组
- `score` 是否为正数

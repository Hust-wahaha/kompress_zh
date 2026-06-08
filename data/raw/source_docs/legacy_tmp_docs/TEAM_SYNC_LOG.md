# Team Sync Log

本文件是全组统一协作文档。所有组员都只在这个文件末尾追加，不覆盖、不改写他人内容。

## Purpose

- 降低队友之间的沟通成本
- 保证任何人都能快速接手上一位同学的工作
- 避免“只知道做了什么，不知道为什么、改了哪里、结论是什么”

## Mandatory Update Rules

- 每次完成一段可汇报工作，就追加一条记录
- 记录必须写绝对时间，格式统一：`YYYY-MM-DD HH:MM`
- 记录必须写清楚文件路径、实验目录、结果结论
- 结论和问题都要写，不能只写“已完成”
- 禁止删除他人条目；若发现错误，新增一条“勘误/修正”说明
- 新条目统一追加到文末，按时间自然接龙

## Entry Template

复制下面模板，直接接在文末：

```md
## [姓名] | [YYYY-MM-DD HH:MM]

### 本次工作
- 

### 为什么这样做
- 

### 修改/涉及文件
- 

### 实验或运行信息
- 机器：
- 命令：
- 输出目录：

### 结果与结论
- 

### 风险 / 遗留问题
- 

### 建议下一步
- 
```

## Writing Standard

- “本次工作”写动作，不写空话  
  例：`补跑 s800 全量 baseline vs finetuned 评测`

- “为什么这样做”写动机  
  例：`之前 256 token 评测存在长 think 截断，结果可能被低估`

- “修改/涉及文件”必须给相对路径  
  例：`scripts/eval_compare_full.py`、`docs/PROJECT_PROGRESS.md`

- “结果与结论”必须包含可复用信息  
  例：准确率、实验目录、异常现象、解释判断

- “建议下一步”要让下一个同学可以直接开做

## Example Entry

## Codex | 2026-05-16 15:20

### 本次工作
- 补跑 `s800` 全量 baseline vs finetuned 正式评测
- 修正文档结构并新增团队协作文档

### 为什么这样做
- 之前 `max_tokens=256` 的评测会被长 `<think>` 截断，不能作为最终判断
- 组内需要统一的接龙式进度文档，降低同步成本

### 修改/涉及文件
- `scripts/eval_compare_full.py`
- `docs/PROJECT_PROGRESS.md`
- `docs/TEAM_SYNC_LOG.md`
- `README.md`

### 实验或运行信息
- 机器：AutoDL RTX 4090 24GB
- 命令：`python scripts/eval_compare_full.py --checkpoint runs/20260515_210429/checkpoints/checkpoint-40 --max-tokens 512 --tag compare_s800_full_mt512`
- 输出目录：`runs/20260516_150218_compare_s800_full_mt512`

### 结果与结论
- baseline：`55.0%`
- finetuned：`96.25%`
- `s800` 在自有分布上已经证明方向有效，当前短板转为输出控制而非算术能力

### 风险 / 遗留问题
- 模型仍然普遍保留 `<think>` 长输出
- classical 视图仍弱于 modern 视图

### 建议下一步
- 做下一版数据集时优先增强 classical 鲁棒性
- 同时优化目标格式，降低对长 `<think>` 的依赖

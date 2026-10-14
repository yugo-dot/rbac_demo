# 交接模板 (换新窗口时用)

> 用途: 每次换新 AI 窗口时, 把本模板 + CONTEXT.md + PROGRESS.md 一起贴给新窗口.
> 本文件本身不用贴给新 AI, 是给你 (使用者) 看的操作说明.

## 操作步骤

1. 在项目根目录跑以下两条命令, 复制输出:
   cat docs/CONTEXT.md
   cat docs/PROGRESS.md

2. 打开新窗口, 粘贴下面的模板, 把两份文档内容填进对应位置.

## 模板 (复制以下内容到新窗口)

---

接手这个 Django + DRF RBAC 项目.

项目文档在 docs/ 下:
- docs/CONTEXT.md: 稳定上下文 (背景/环境/目录/约定/命令), 交接必读
- docs/PROGRESS.md: 当前进度 (已完成/下一步/卡点), 交接必读
- docs/DECISIONS.md: 设计决策归档, 交接不用读, 需要查"为什么这么做"时按需读

下面是这两份文档的内容:

[file name]: CONTEXT.md
[file content]
（把 docs/CONTEXT.md 全文粘这里）


[file name]: PROGRESS.md
[file content]
（把 docs/PROGRESS.md 全文粘这里）


要求:
1. 先通读上面两份文档, 然后按 PROGRESS.md 的"下一步"给我方案.
2. 遵守 CONTEXT.md 里的协作方式 (一次一步 / 纯文本块 / 中文注释英文标点).
3. 需要查某个设计原因时, 自己去读 docs/DECISIONS.md.

---

## 备注

- DECISIONS.md 一般不用粘. 只有当本次任务要改动某个已定的设计时,
  才额外把它也粘上, 并在要求里加一句"这次涉及设计变更, 请一并读 DECISIONS.md".
- 如果新 AI 要用命令读文档, 路径是 docs/CONTEXT.md / docs/PROGRESS.md / docs/DECISIONS.md.

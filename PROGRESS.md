# RBAC Demo 项目进度文档

> 本文件只存放**变动**的内容: 已完成 / 下一步 / 卡点.
> 稳定上下文 (背景 / 环境 / 目录 / 约定 / 命令 / 交接清单 / 设计决策) 见 CONTEXT.md.
> Git 提交记录不在这里手写, 直接 `git log --oneline -10` 看.

## 一、已完成

- [x] Docker 环境搭建
- [x] Django 项目骨架 (config/)
- [x] 自定义 User 模型 (AbstractUser + phone/email 唯一)
- [x] RBAC 四张表 (Role / Permission / UserRole / RolePermission)
- [x] 迁移成功, 数据库表已建
- [x] models / serializers / views 拆成包
- [x] 拆分 UserProfile (nickname / avatar / bio / gender / birthday / location), signal 自动创建
- [x] User.get_permission_codes() 方法
- [x] JWT 登录接口 (用户名 / 手机号 / 邮箱 三选一)
- [x] 角色 / 权限的 CRUD 接口 (ModelViewSet + DefaultRouter)
- [x] 自定义权限类 HasPerm (支持 list / dict, 超管放行)
- [x] 示例接口 + RBAC 保护验证 (app: articles, 手动 curl + 单元测试)
- [x] 当前用户信息接口 GET /api/users/me/ (返回资料 + 权限编码)
- [x] 用户-角色 / 角色-权限 分配接口 (GET / POST / DELETE)
- [x] Redis 缓存 get_permission_codes (key user:perms:{uid}, TTL 300s, 变动时主动清)
- [x] 分页 + django-filter + 搜索 + 排序 (Role / Permission 列表)
- [x] settings 拆分 base/dev/prod (通过 DJANGO_SETTINGS_MODULE 选择)
- [x] 接 shared-nginx 对外暴露 (子域名 rbac.localhost, 反代到 rbac_demo_web:8000)
- [x] API 文档 (drf-spectacular): /api/schema/ + /api/docs/ (Swagger UI, 静态文件走 sidecar 不走 CDN)
- [x] 预置权限点种子数据 (data migration: 6 个 rbac:* + 2 个 article:*)
- [x] RBAC 管理接口叠加 HasPerm 权限保护 (角色/权限点/用户角色按读/写拆分)
- [x] 测试适配 (种子数据 + 内置保护, 全绿)
- [x] 文档拆分: CONTEXT.md (稳定) + PROGRESS.md (变动), 砍掉手写 Git 记录
- [x] 内置角色/权限保护 (is_builtin, 禁止改 code / 禁止删, 8 个种子权限标内置)
- [x] 代码门禁: ruff + pre-commit (commit 前自动 lint + format)

## 二、下一步

第一阶段 (基础 RBAC 闭环) 已完成. 后续候选方向 (排序即推荐顺序):

1. [x] 内置角色/权限保护 (is_builtin 标记, 禁止删改)
2. [ ] 用户注册 / 改密 / 刷新 token 接口
3. [ ] ABAC 数据级权限 (articles 落地)
4. [x] 接 pre-commit (ruff), CI 待推 Gitee 时再加

## 三、当前卡点

- 无


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
- [x] 注册 / 改密 / 登出 / token 刷新接口 (SimpleJWT blacklist, 改密后强制重登)
- [x] ABAC 基础设施: Casbin + casbin_rule 表 + enforcer 封装 (apps/rbac/abac.py)
- [x] Article 真实 CRUD + 两层权限 (HasPerm 接口级 + HasAbacPerm 对象级)
- [x] Casbin 策略管理接口 (/api/rbac/policies/) + 5 条默认策略种子
- [x] 推送到 Gitee (含 7 个 tag, v0.1.0 ~ v0.7.0)
- [x] 修复测试跨类缓存污染 (LocMemCache -> DummyCache) + 0005 迁移改用 schema_editor 兼容 SQLite
- [x] 推送到 GitHub (yugo-dot/rbac_demo)
- [x] GitHub Actions CI 跑通 (MySQL 8.0 + Redis 7 服务, 53 测试全过, 约 1.5 分钟)
- [x] 审计日志 (AuditLog + log_action + 4 个 ViewSet 挂钩 + 查询接口)
- [x] CasbinRule 模型声明 (修幽灵迁移, Django 不再生成 DeleteModel)
- [x] Django admin 注册 (8 个模型; 内置角色/权限只读 + 审计日志全只读)
- [x] 演示数据种子命令 (seed_demo: 10 用户 / 4 角色 / 2000 文章, 幂等 + --flush)
- [x] ABAC 性能优化 (DB 粗筛 + Casbin 精筛; enforce 2000 -> 1180 次, 0.41s -> 0.27s)

## 二、下一步

第一阶段 (基础 RBAC 闭环) + 第二阶段 (ABAC + 审计 + CI + admin) 已完成.
以下候选方向 (未开始, 排序即推荐顺序):

1. [ ] 用户资料修改接口
   - 现状: GET /api/users/me/ 只读, 不能改 nickname / avatar / bio 等
   - 目标: 加 PATCH /api/users/me/, 支持改 UserProfile 字段

2. [ ] 权限点按模块分组
   - 现状: Permission 没有 module 字段, 靠命名约定 (rbac:role:read)
   - 目标: 加 module 字段, 前端可按模块折叠展示

3. [ ] 数据级权限细化 (visibility)
   - 现状: Article 有 visibility 字段 (private/team/public), 但策略没用它
   - 目标: 加策略, 让 visibility 真正影响可见性

4. [ ] CI 通知 (搁置)
   - 曾尝试 PushPlus / Server酱, 都因收费或额度放弃
   - 可选: Server酱 免费版 (每天 5 条) 或不做

## 补充说明 (给接手的 AI)

- 上一阶段刚做完: ABAC 性能优化 (DB 粗筛 + Casbin 精筛)
- 远端: origin=Gitee, github=GitHub, 两边都推
- CI: GitHub Actions 已跑通 (63 测试, ~1.5 分钟)
- 本地测试命令: docker compose exec web python manage.py test users rbac articles
- 本地数据: 10 用户 (admin/admin + user01~09) / 4 角色 / 2000 文章 / 13 权限 / 5 Casbin 策略
- 重造数据: docker compose exec web python manage.py seed_demo --flush --articles 2000

## 三、当前卡点

- 无

## 四、已知问题 / 搁置项

- **Gitee Go CI 未落地**: 账号无免费构建额度.
  - 改用 GitHub Actions 已跑通 (见上方"已完成")
  - Gitee 仅作代码镜像, 不跑 CI


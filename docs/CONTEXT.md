# RBAC Demo 项目上下文文档

> 本文件存放**稳定**的项目上下文: 背景 / 环境 / 目录 / 约定 / 命令 / 交接清单.
> 交接给新 AI 时, 本文件 + PROGRESS.md 一起贴; 需要查设计原因时再看 DECISIONS.md.
> 相关文件: 进度 (已完成 / 下一步 / 卡点) 见 docs/PROGRESS.md; 设计决策归档见 docs/DECISIONS.md.

## 零、给新 AI 的说明 (最先读这段)

你正在接手一个进行中的 Django + DRF RBAC 学习项目.

## 文档导航

- docs/CONTEXT.md (本文件): 稳定上下文 (背景 / 环境 / 目录 / 约定 / 命令)
- docs/PROGRESS.md: 当前进度 (已完成 / 下一步 / 卡点), 交接必读
- docs/DECISIONS.md: 设计决策归档, 交接时不用读, 需要查"为什么这么做"时按需查

交接时: 本文件 + PROGRESS.md 一起贴. 需要设计原因时再读 DECISIONS.md.
详细协作方式见文末"六、协作方式约定".

## 一、项目背景

- 目标: 学习并实战 Django + DRF 的 RBAC (基于角色的访问控制)
- 技术栈: Django 5.2 / DRF 3.15 / SimpleJWT 5.3 / django-filter 24.3 / drf-spectacular 0.28 / MySQL 8.0 / Redis 7 / Docker
- 权限模型: RBAC (用户-角色-权限), 后期考虑引入 ABAC 做数据级权限

## 二、环境信息

- 宿主机: Windows 11 + WSL2 (Ubuntu 26.04)
- 项目路径: /home/gaoyu/projects/python/rbac_demo
- Docker 网络: shared-services (外部网络, 已有)
- 共享容器:
  - shared-nginx  (80)
  - shared-mysql  (3306, root 密码 root123)
  - shared-redis  (6379)
- 本项目的容器: rbac_demo_web (映射 8000:8000)
- 数据库: rbac_demo (用户 rbac_user / rbac_pass_123)
- Redis 连接: host=redis, port=6379
- 对外入口: shared-nginx 反代 http://rbac.localhost -> rbac_demo_web:8000
- Swagger UI: http://rbac.localhost/api/docs/  (schema 在 /api/schema/)
  - hosts 需加: 127.0.0.1 rbac.localhost
  - nginx 配置: /home/gaoyu/docker-infra/nginx/conf.d/rbac.conf (不在本项目仓库里)

## 三、目录结构

rbac_demo/
├── apps/
│   ├── __init__.py
│   ├── users/
│   │   ├── models/
│   │   │   ├── __init__.py      (导出 User / UserProfile)
│   │   │   ├── user.py          (User 继承 AbstractUser + get_permission_codes)
│   │   │   └── profile.py       (UserProfile, OneToOne 关联 User)
│   │   ├── serializers/
│   │   │   ├── __init__.py      (导出 Login/Register/ChangePassword/Me)
│   │   │   ├── auth.py          (Login/Register/ChangePassword)
│   │   │   └── user.py          (MeSerializer)
│   │   ├── views/
│   │   │   ├── __init__.py      (导出 Login/Register/Logout/ChangePassword/Me)
│   │   │   ├── auth.py          (登录 / 注册 / 登出 / 改密)
│   │   │   └── user.py          (MeView)
│   │   ├── signals.py           (post_save -> 自动建 Profile)
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── test_api.py      (登录 / 注册 / 改密 / me)
│   │   │   └── test_admin.py    (admin 冒烟测试)
│   │   └── migrations/
│   ├── rbac/
│   │   ├── models/
│   │   │   ├── __init__.py      (导出 AuditLog / CasbinRule / Role / Permission / UserRole / RolePermission)
│   │   │   ├── audit_log.py     (审计日志)
│   │   │   ├── casbin_rule.py   (casbin_rule 表映射, managed=False)
│   │   │   ├── role.py          (含 is_builtin)
│   │   │   ├── permission.py    (含 is_builtin)
│   │   │   ├── user_role.py
│   │   │   └── role_permission.py
│   │   ├── serializers/
│   │   │   ├── __init__.py
│   │   │   ├── role.py
│   │   │   ├── permission.py
│   │   │   ├── user_role.py
│   │   │   ├── role_permission.py
│   │   │   ├── policy.py        (PolicySerializer, 策略不是 Django 模型)
│   │   │   └── audit_log.py     (AuditLogSerializer, 只读)
│   │   ├── views/
│   │   │   ├── __init__.py
│   │   │   ├── role.py          (含角色权限分配 action)
│   │   │   ├── permission.py
│   │   │   ├── user_role.py     (用户角色分配 action)
│   │   │   ├── policy.py        (PolicyViewSet: list / create / destroy)
│   │   │   └── audit_log.py     (AuditLogViewSet: 只读)
│   │   ├── permissions.py       (HasPerm 接口级 + HasAbacPerm 对象级)
│   │   ├── cache.py             (用户权限缓存失效工具)
│   │   ├── abac.py              (Casbin enforcer 封装 + Adapter + build_sub)
│   │   ├── audit.py             (审计日志工具 log_action)
│   │   ├── urls.py              (DefaultRouter 注册)
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── tests.py
│   │   └── migrations/          (0003 种子权限, 0004 is_builtin, 0005 casbin_rule,
│   │                             0006 article update/delete, 0007 策略种子,
│   │                             0008 policy 权限, 0009 audit_log, 0010 audit_log 权限,
│   │                             0011 permission module, 0012 module 回填,
│   │                             0013 visibility 策略)
│   └── articles/
│       ├── models.py            (Article: author / status / visibility)
│       ├── serializers.py       (ArticleSerializer)
│       ├── views.py             (ArticleViewSet, 两层权限保护)
│       ├── urls.py              (DefaultRouter 注册)
│       ├── tests.py             (13 个 ABAC / visibility 单元测试)
│       ├── admin.py
│       ├── apps.py
│       └── migrations/
├── config/
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py              (公共配置 + CASBIN_MODEL + SIMPLE_JWT blacklist)
│   │   ├── dev.py               (DEBUG=True, ALLOWED_HOSTS=['*'])
│   │   └── prod.py              (DEBUG=False, ALLOWED_HOSTS 从环境变量读)
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── manage.py
├── casbin_model.conf            (Casbin ABAC 模型定义)
├── pyproject.toml               (ruff 配置)
├── .pre-commit-config.yaml      (pre-commit 配置)
└── docs/
    ├── CONTEXT.md               (本文件, 稳定上下文)
    ├── DECISIONS.md             (设计决策归档)
    └── PROGRESS.md              (进度, 每次改动更新)

## 四、关键约定

- 注释风格: 中文注释, 使用英文标点
- 权限编码格式: 模块:操作 (例如 article:create, rbac:role:manage)
- models / serializers / views 统一拆成包, 每个业务模块一个文件, __init__.py 统一导出
- apps 下的业务 app 直接放在 apps/ 下, INSTALLED_APPS 里用不带 apps. 前缀的名字 (例如 'users' / 'rbac' / 'articles')
- settings 已拆 base/dev/prod, 通过 DJANGO_SETTINGS_MODULE 选择, 默认 dev
- 权限编码粒度: 读写分开 (read / manage), 资源+操作; 分配关联视为对资源的 manage

## 五、常用命令

docker compose exec web bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
docker compose exec web python manage.py shell -c "xxx"
docker compose exec web python manage.py test users rbac articles -v 2
docker compose logs web --tail 50
docker compose restart web
git add . && git commit -m "xxx"
git log --oneline -10
pre-commit run --all-files         # 手动全量跑一遍 ruff

## 六、协作方式约定

- 沟通节奏: 一次只走一步, 用户确认后再给下一步
- 代码风格: 中文注释, 英文标点
- 文件输出: 纯文本块, 不要嵌套代码块
- 每完成一个阶段: 更新 PROGRESS.md
- 每次改动后: 单独 git commit, 信息用中文

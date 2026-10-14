# RBAC Demo 项目上下文文档

> 本文件存放**稳定不变**的项目上下文: 背景 / 环境 / 目录 / 约定 / 命令 / 交接清单 / 设计决策.
> 交接给新 AI 时, 本文件 + PROGRESS.md 一起贴.
> 变动的内容 (已完成 / 下一步 / 卡点) 在 PROGRESS.md.

## 零、给新 AI 的说明 (最先读这段)

你正在接手一个进行中的 Django + DRF RBAC 学习项目.

请先通读本文件 + PROGRESS.md, 然后遵守以下协作方式:

1. 一次只走一步. 给出一条命令或一个文件后, 等用户确认再做下一步.
2. 不要一次性输出多个文件或大段代码.
3. 输出文件内容时, 用纯文本块 (不要用嵌套代码块), 方便用户直接复制到终端.
4. 用户环境是 Windows + WSL2, 命令都在 WSL 终端里跑.
5. 代码风格: 中文注释, 使用英文标点.
6. 每完成一个阶段, 提醒用户更新 PROGRESS.md 并 git commit.

## 一、项目背景

- 目标: 学习并实战 Django + DRF 的 RBAC (基于角色的访问控制)
- 技术栈: Django 5.1.4 / DRF 3.15 / SimpleJWT 5.3 / django-filter 24.3 / drf-spectacular 0.28 / MySQL 8.0 / Redis 7 / Docker
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
│   │   │   ├── user.py          (User 继承 AbstractUser)
│   │   │   └── profile.py       (UserProfile, OneToOne 关联 User)
│   │   ├── serializers/
│   │   │   ├── __init__.py      (导出 LoginSerializer / MeSerializer)
│   │   │   ├── auth.py
│   │   │   └── user.py          (MeSerializer)
│   │   ├── views/
│   │   │   ├── __init__.py      (导出 LoginView / MeView)
│   │   │   ├── auth.py
│   │   │   └── user.py          (MeView)
│   │   ├── signals.py           (post_save -> 自动建 Profile)
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── tests.py
│   │   └── migrations/
│   ├── rbac/
│   │   ├── models/
│   │   │   ├── __init__.py      (导出 Role / Permission / UserRole / RolePermission)
│   │   │   ├── role.py
│   │   │   ├── permission.py
│   │   │   ├── user_role.py
│   │   │   └── role_permission.py
│   │   ├── serializers/
│   │   │   ├── __init__.py      (统一导出)
│   │   │   ├── role.py
│   │   │   ├── permission.py
│   │   │   ├── user_role.py
│   │   │   └── role_permission.py
│   │   ├── views/
│   │   │   ├── __init__.py      (统一导出)
│   │   │   ├── role.py          (含角色权限分配 action)
│   │   │   ├── permission.py
│   │   │   └── user_role.py     (用户角色分配 action)
│   │   ├── permissions.py       (HasPerm 权限类)
│   │   ├── cache.py             (用户权限缓存失效工具)
│   │   ├── urls.py              (DefaultRouter 注册)
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── tests.py
│   │   └── migrations/          (0003_seed_permissions: 预置权限点)
│   └── articles/
│       ├── views.py             (ArticleDemoView, 用 HasPerm 保护)
│       ├── urls.py
│       ├── tests.py             (4 个 RBAC 单元测试)
│       ├── models.py            (空, 仅占位)
│       ├── admin.py
│       ├── apps.py
│       └── migrations/
├── config/
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py              (公共配置)
│   │   ├── dev.py               (DEBUG=True, ALLOWED_HOSTS=['*'])
│   │   └── prod.py              (DEBUG=False, ALLOWED_HOSTS 从环境变量读)
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── manage.py
├── CONTEXT.md                   (本文件, 稳定上下文)
└── PROGRESS.md                  (进度, 每次改动更新)

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

## 六、关键文件内容 (交接时必读)

新 AI 需要知道当前代码长什么样. 交接时请用户执行以下命令, 把输出贴给你:

# 模型
cat apps/users/models/user.py
cat apps/users/models/profile.py
cat apps/users/models/__init__.py
cat apps/rbac/models/__init__.py
cat apps/rbac/models/role.py
cat apps/rbac/models/permission.py
cat apps/rbac/models/user_role.py
cat apps/rbac/models/role_permission.py

# signals 与 app 配置
cat apps/users/signals.py
cat apps/users/apps.py

# 序列化器
cat apps/users/serializers/auth.py
cat apps/users/serializers/user.py
cat apps/rbac/serializers/role.py
cat apps/rbac/serializers/permission.py
cat apps/rbac/serializers/user_role.py
cat apps/rbac/serializers/role_permission.py

# 视图
cat apps/users/views/auth.py
cat apps/users/views/user.py
cat apps/rbac/views/role.py
cat apps/rbac/views/permission.py
cat apps/rbac/views/user_role.py
cat apps/articles/views.py

# 权限类与缓存工具
cat apps/rbac/permissions.py
cat apps/rbac/cache.py

# 种子数据
cat apps/rbac/migrations/0003_seed_permissions.py

# 路由
cat config/urls.py
cat apps/users/urls.py
cat apps/rbac/urls.py
cat apps/articles/urls.py

# 配置
cat config/settings/base.py
cat config/settings/dev.py
cat config/settings/prod.py

# 测试
cat apps/articles/tests.py
cat apps/users/tests.py
cat apps/rbac/tests.py

# git 状态
git log --oneline -10
git status

# 依赖与容器
cat requirements.txt
cat docker-compose.yml

## 七、设计决策记录

- User 继承 AbstractUser: 省事, admin 兼容, 不折腾 AbstractBaseUser
- phone/email 用 unique=True + null=True + blank=True: 允许不填, 填了必须唯一
- 关联表用独立 Model (UserRole / RolePermission): 便于以后加审计字段
- models 拆成包: 每个实体一个文件, __init__.py 统一导出, Django 通过导入发现模型
- serializers / views 也拆成包: 与 models 风格统一, 按业务模块拆文件
- 权限编码格式: 模块:操作 (article:create)
- 关联表暂不用 Django 自带 auth_group / auth_permission, 用自己的 rbac 表
- HasPerm 权限类: 支持 required_perms 为 list 或 dict; is_superuser 直接放行; 内部先判登录
- 示例接口独立成 app: articles, 仅用于演示 RBAC, 不建真实数据表
- startapp 踩坑: 直接 `python manage.py startapp xxx apps/xxx` 会和 Python 模块名冲突;
  正确姿势是先在项目根 `python manage.py startapp xxx`, 再 `mv xxx apps/xxx`;
  注意容器里 startapp 生成的目录属主是 root, mv 前需 sudo 或改属主
- 注意: User.email 是 unique, create_user 不传 email 会写 '' 导致第二个用户冲突;
  代码里创建用户时要么传真实 email, 要么显式传 None
- User / UserProfile 拆分: 登录相关 (username / password / email / phone) 留在 User;
  展示类 (nickname / avatar / bio / gender / birthday / location) 放 UserProfile
- UserProfile 用 OneToOneField(User, related_name='profile')
- 新建 User 时通过 post_save signal 自动创建 UserProfile (apps/users/signals.py)
- 用户-角色 / 角色-权限 分配接口用 ViewSet @action 实现:
  - UserRoleViewSet 挂在 /api/rbac/users/, 含 roles / remove_role
  - RoleViewSet 加 permissions / remove_permission
  - 写入用 get_or_create 保证幂等 (201 新建 / 200 已存在)
- 用户权限缓存: key = user:perms:{uid}, value = 权限码列表, TTL = 300s
  - 失效: 分配 / 移除用户角色, 或给角色增删权限时, 主动清相关用户缓存
  - 工具函数: apps/rbac/cache.py 的 invalidate_user_perms / invalidate_role_perms
  - Redis 挂了不影响业务: CACHES['default']['OPTIONS']['IGNORE_EXCEPTIONS'] = True
- 列表接口统一: 分页 (PageNumberPagination, PAGE_SIZE=20) + DjangoFilterBackend + SearchFilter + OrderingFilter
  - RoleViewSet: filterset_fields=['code','name'], search_fields=['name','code','description'], ordering_fields=['id','code','name','created_at']
  - PermissionViewSet: 同上
  - 子列表 (users/{id}/roles/, roles/{id}/permissions/) 不分页
- settings 拆分: base / dev / prod, 通过环境变量 DJANGO_SETTINGS_MODULE 选择;
  manage.py / wsgi.py / asgi.py 默认指向 config.settings.dev;
  docker-compose.yml 里通过环境变量指定, 生产改为 config.settings.prod
- 测试环境缓存隔离: base.py 里检测 sys.argv 里有没有 'test',
  有则用 LocMemCache, 否则用 Redis; 避免测试数据写脏生产 Redis
- API 文档: 用 drf-spectacular (OpenAPI 3), 不用 drf-yasg (只支持 Swagger 2 且不维护)
  - 静态文件走 drf-spectacular-sidecar 本地提供, 不走 CDN (国内网络 cdn.jsdelivr.net 会被重置)
  - SPECTACULAR_SETTINGS: SERVE_PERMISSIONS = AllowAny (文档页面匿名可访问, 接口本身该保护还是保护)
  - 非 ModelViewSet 的视图 (LoginView / ArticleDemoView / 自定义 action) 用 @extend_schema 补注解,
    否则 Swagger 里看不到请求体/响应结构
- 对外暴露方案: 走子域名 rbac.localhost (而非子路径)
  - 优点: Django 侧零改动, 不用处理路径前缀
  - nginx 里单独加一个 server_name rbac.localhost 的 server, default.conf 保持不动
  - shared-nginx 和 rbac_demo_web 都在 shared-services 网络, nginx 直接 proxy_pass http://rbac_demo_web:8000
- 权限点种子数据用 data migration (而非 fixture):
  - data migration 随 migrate 自动执行, 测试库建库时也会加载, 幂等 (get_or_create)
  - fixture 每次 loaddata 全量覆盖, 且不会自动加载, 只适合测试固定数据或手动导入
  - 迁移里用 apps.get_model('rbac', 'Permission'), 不直接 import 模型 (历史版本安全)
  - 提供 reverse_code (remove_permissions) 支持回滚
- 管理面权限编码方案 (6 个, 读写分开):
  - rbac:role:read / rbac:role:manage
  - rbac:permission:read / rbac:permission:manage
  - rbac:user_role:read / rbac:user_role:manage
  - 分配角色权限的动作 (POST/DELETE /roles/{id}/permissions/) 归入 rbac:role:manage
    (视为修改角色的子资源, 不单拆 role_permission)
  - 主流做法参考: Keycloak 的 view/manage scope 分离, Casbin 的 obj+act 模型
- 管理面接口保护: RoleViewSet / PermissionViewSet / UserRoleViewSet 都叠加 HasPerm
  - 按 request.method 映射到对应编码, 同一 action 上挂多个 method 时天然生效
  - 超管仍由 is_superuser 放行, 不加 bootstrap 特例
- 测试适配种子数据: 测试里不再硬 create 种子权限, 改用 get_or_create;
  分页/搜索类断言不写死绝对数量, 改为相对当前权限表总量 (避免受种子数据影响)
- 文档拆分 (本次): CONTEXT.md 放稳定内容, PROGRESS.md 放变动内容;
  Git 提交记录不再手写, 直接 git log 看
- 内置角色/权限保护 (is_builtin):
  - Role / Permission 各加 is_builtin 布尔字段, 默认 False
  - 8 个种子权限点在迁移 0004_add_is_builtin 里标为内置
  - 约束: 内置角色/权限不可删, code 不可改; name / description 可改
  - 校验在 ViewSet 的 perform_update / perform_destroy 里, 抛 PermissionDenied (403)
  - 超管也不放行 (系统级保护, 跟用户权限无关)
  - 主流参考: Keycloak 内置角色禁止删改, Django Guardian / 葡萄城同类设计
- 认证面补全 (注册 / 改密 / 登出 / 刷新 token):
  - 用 SimpleJWT 的 token_blacklist app 实现"登出 / 改密强制重登"
  - SIMPLE_JWT: ROTATE_REFRESH_TOKENS=True + BLACKLIST_AFTER_ROTATION=True
  - 刷新时换发新 refresh, 旧的自动拉黑
  - 改密成功后遍历 OutstandingToken 把该用户所有 refresh 拉黑, 强制重登
  - 注册即登录 (直接返回 access/refresh), 密码走 Django validate_password 强度校验
  - 注册时 email/phone 空串按 None 处理, 避免 unique 冲突
  - 接口: POST /register/, /logout/, /change-password/, /token/refresh/
- ABAC 数据级权限 (Casbin):
  - 用 casbin (pycasbin) + 自定义 Adapter, 策略存 MySQL 的 casbin_rule 表
  - 不用 casbin_adapter 的 AppConfig.ready (它在 app 初始化时访问 DB, 会引发警告和迁移问题)
  - casbin_rule 建表迁移在 rbac/0005, 不用 CreateModel 而是 RunPython + 原生 SQL + atomic=False
  - 模型定义在项目根 casbin_model.conf, ABAC 模式: (sub, obj, act) + eval(sub_rule)
  - sub / obj 都是 dict, 策略表达式用 r.sub.xxx / r.obj.xxx 引用属性
  - enforcer 用 lru_cache 缓存, 策略变更后 clear_enforcer_cache()
  - 两层权限: HasPerm (接口级, 需 article:read 等编码) + HasAbacPerm (对象级, 判具体数据)
  - 行级过滤在 ViewSet.get_queryset 里做, 对象级在 HasAbacPerm.has_object_permission 里做
  - 越权返回 404 而非 403 (查询集已过滤, DRF 找不到对象, 避免信息泄露)
  - 策略管理接口 /api/rbac/policies/ (list / create / destroy), 用 rbac:policy:read / rbac:policy:manage
  - 策略种子在 rbac/0007 (5 条: 作者全权 / 已发布公开 / 主编可读)
  - 已知取舍: get_queryset 里逐行调 enforce 是 N 次判定, 量大时会慢;
    主流优化是先用 Q 对象在 DB 层粗过滤, 只对候选行跑 Casbin
- 代码门禁: ruff + pre-commit
  - ruff 负责 lint (E/F/I/UP/B/SIM) + format, 配置在 pyproject.toml
  - 忽略规则: RUF012 (Django/DRF 类属性惯例), RUF022 (__all__ 顺序), SIM102, E501
  - 排除 migrations/ (Django 自动生成, 不查)
  - pre-commit 装在 WSL (pipx 管理), git commit 前自动跑 ruff check --fix + ruff-format
  - 选双引号 (ruff-format 默认, 与 black 一致)
  - 首次全量格式化后, 会统一改掉单引号 -> 双引号 (一次性 commit)
  - pre-commit 装在跑 git 的机器 (WSL), 不是容器; 因为 git commit 在 WSL 执行
  - CI 暂不做, 等推 Gitee 时再加 Gitee Go 配置

## 八、协作方式约定

- 沟通节奏: 一次只走一步, 用户确认后再给下一步
- 代码风格: 中文注释, 英文标点
- 文件输出: 纯文本块, 不要嵌套代码块
- 每完成一个阶段: 更新 PROGRESS.md
- 每次改动后: 单独 git commit, 信息用中文

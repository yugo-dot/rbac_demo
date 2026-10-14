# RBAC Demo 项目进度文档

> 本文档用于在切换 AI 工具 / 新会话时快速恢复上下文.
> 每次有重大进展请更新.

## 零、给新 AI 的说明 (最先读这段)

你正在接手一个进行中的 Django + DRF RBAC 学习项目.

请先通读本文档, 然后遵守以下协作方式:

1. 一次只走一步. 给出一条命令或一个文件后, 等用户确认再做下一步.
2. 不要一次性输出多个文件或大段代码.
3. 输出文件内容时, 用纯文本块 (不要用嵌套代码块), 方便用户直接复制到终端.
4. 用户环境是 Windows + WSL2, 命令都在 WSL 终端里跑.
5. 代码风格: 中文注释, 使用英文标点.
6. 每完成一个阶段, 提醒用户更新本文档并 git commit.

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
│   │   └── migrations/
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
└── PROGRESS.md

## 四、关键约定

- 注释风格: 中文注释, 使用英文标点
- 权限编码格式: 模块:操作 (例如 article:create, user:delete)
- models / serializers / views 统一拆成包, 每个业务模块一个文件, __init__.py 统一导出
- apps 下的业务 app 直接放在 apps/ 下, INSTALLED_APPS 里用不带 apps. 前缀的名字 (例如 'users' / 'rbac' / 'articles')
- settings 已拆 base/dev/prod, 通过 DJANGO_SETTINGS_MODULE 选择, 默认 dev

## 五、已完成

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

## 六、Git 提交记录

- 858c64b chore: 初始化 Django 项目骨架与 Docker 环境
- b7dfbf9 feat: 切换数据库为 MySQL 并应用初始迁移
- 7d576c9 feat: 自定义 User 模型 + RBAC 四张表 (models 拆成包)
- e4e6a86 feat: User 增加 get_permission_codes 方法
- da4a899 docs: PROGRESS.md 补充 commit 记录
- dec6c94 feat: JWT 登录接口 (用户名 / 手机号 / 邮箱 三选一)
- e6616ce docs: PROGRESS.md 补充 commit 记录
- fb950b6 feat: 角色 / 权限 CRUD 接口 (ModelViewSet + DefaultRouter)
- af8d801 docs: PROGRESS.md 补充 commit 记录
- 354815d feat: 自定义权限类 HasPerm
- 46336a1 feat: 示例文章接口 + RBAC 保护验证 (手动 + 单元测试)
- 1aa3d5e docs: PROGRESS.md 补充 commit 记录
- b3f41a3 docs: 重写 PROGRESS.md, 与实际代码对齐
- 9a990f4 feat: 拆分 UserProfile, 展示类字段从 User 移出
- e090926 feat: 当前用户信息接口 GET /api/users/me/
- cfc58b5 feat: 用户-角色 / 角色-权限 分配接口 (ViewSet @action)
- 19cfa00 feat: Redis 缓存 get_permission_codes (主动失效 + TTL 兜底)
- a97881a feat: 分页 + django-filter + 搜索 + 排序 (Role / Permission 列表)
- 41fec44 refactor: settings 拆分 base/dev/prod + 测试缓存隔离
- 8d2f52e docs: PROGRESS.md 记录 shared-nginx 对接

## 七、下一步

第一阶段 (基础 RBAC 闭环) 已完成. 后续可做方向 (排序即推荐顺序):

1. [x] 用户 - 角色 / 角色 - 权限 分配接口 (补齐管理面)
2. [x] 当前用户信息接口 GET /api/users/me/ (返回资料 + 权限编码)
3. [x] Redis 缓存 get_permission_codes()
4. [x] 接 django-filter + 分页, 完善列表接口
5. [x] 接 shared-nginx 对外暴露
6. [x] settings 拆 base/dev/prod

## 八、当前卡点

- 无

## 九、常用命令

docker compose exec web bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
docker compose exec web python manage.py shell -c "xxx"
docker compose exec web python manage.py test users rbac articles -v 2
docker compose logs web --tail 50
docker compose restart web
git add . && git commit -m "xxx"

## 十、关键文件内容 (交接时必读)

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

# git 状态
git log --oneline -10
git status

# 依赖与容器
cat requirements.txt
cat docker-compose.yml

## 十一、设计决策记录

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
- 现阶段这些接口只要求 IsAuthenticated, 未叠加 HasPerm (等权限数据稳定后再加)
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

## 十二、协作方式约定

- 沟通节奏: 一次只走一步, 用户确认后再给下一步
- 代码风格: 中文注释, 英文标点
- 文件输出: 纯文本块, 不要嵌套代码块
- 每完成一个阶段: 更新本文档的"已完成"和"下一步"
- 每次改动后: 单独 git commit, 信息用中文

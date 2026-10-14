# RBAC Demo 设计决策记录

> 本文件归档项目所有设计决策 (为什么这么做).
> 归档性质, 基本只追加, 不常改. 交接时不用读, 需要查某个设计原因时按需查.
> 相关文件: 稳定上下文见 docs/CONTEXT.md; 当前进度见 docs/PROGRESS.md.

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
  - casbin_rule 建表迁移在 rbac/0005 (细节见下方"数据库可移植性")
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
- 测试环境缓存隔离 (关键修复):
  - 测试环境用 DummyCache (不缓存), 不是 LocMemCache
  - 原因: LocMemCache 是进程级, 跨 TestCase 类不隔离; 用户 ID 在测试间会重复,
    导致 get_permission_codes() 读到上个测试类的脏缓存
  - 现象: 单跑测试类全过, 全量跑时后面的类全 403
- 数据库可移植性:
  - `0005_add_casbin_rule` 用 `schema_editor.create_model()` 建表, 不用原生 SQL
  - 原因: `BIGINT AUTO_INCREMENT` 是 MySQL 方言, SQLite 不认
  - `atomic = False` (MySQL DDL 不能在事务里跑)
  - `config.settings.base` 支持 `USE_SQLITE=true` 切 SQLite (CI 用)
- 审计日志 (AuditLog):
  - 记录 RBAC 管理面的写操作 (create / update / delete / assign / remove)
  - 读操作默认不记, settings.AUDIT_LOG_READ_OPERATIONS=True 时也记 read
  - 独立表 audit_log, operator 用 SET_NULL (用户删了日志还在)
  - target_repr 存可读描述 (即使目标对象被删, 日志还能看懂)
  - detail 用 JSONField 存 before / after (MySQL 5.7+ / SQLite 都支持)
  - 两个索引: (target_type, target_id) 查某对象历史, (operator, -created_at) 查某人操作
  - 工具函数 apps/rbac/audit.py 的 log_action()
  - 在 4 个 ViewSet 挂钩: RoleViewSet / PermissionViewSet / UserRoleViewSet / PolicyViewSet
  - 幂等操作 (get_or_create 返回 created=False) 不记日志, 避免噪声
  - 查询接口 GET /api/rbac/audit-logs/ (只读 + 分页 + 过滤), 权限 rbac:audit_log:read
- CasbinRule 模型声明 (修幽灵迁移):
  - models/casbin_rule.py: managed=False, db_table="casbin_rule"
  - 目的: 让 Django 迁移系统知道这张表还在, 不再生成 DeleteModel(CasbinRule)
  - 起因: 0005 用 CreateModel 建了它, 但 models/__init__.py 没导出, Django 以为被删了
  - 表本身由 0005 的 schema_editor.create_model() 建, 模型声明只是"占位"
- 代码门禁: ruff + pre-commit
  - ruff 负责 lint (E/F/I/UP/B/SIM) + format, 配置在 pyproject.toml
  - 忽略规则: RUF012 (Django/DRF 类属性惯例), RUF022 (__all__ 顺序), SIM102, E501
  - 排除 migrations/ (Django 自动生成, 不查)
  - pre-commit 装在 WSL (pipx 管理), git commit 前自动跑 ruff check --fix + ruff-format
  - 选双引号 (ruff-format 默认, 与 black 一致)
  - 首次全量格式化后, 会统一改掉单引号 -> 双引号 (一次性 commit)
  - pre-commit 装在跑 git 的机器 (WSL), 不是容器; 因为 git commit 在 WSL 执行
  - CI: GitHub Actions (.github/workflows/ci.yml)
    - 用 services 起 MySQL 8.0 + Redis 7, 与本地一致
    - DB_USER=root (rbac_user 无建测试库权限)
    - apt-get install default-libmysqlclient-dev (mysqlclient 编译需要)
  - 远端: origin=Gitee, github=GitHub (两边都推)
- Django admin 注册 (超管后台, 不替代 RBAC API):
  - admin 权限体系 (is_staff/is_superuser) 与项目 RBAC 是两套, 不做映射
  - admin 只给超管用, 业务 RBAC 走 API (前端 Vue3 直接调 API)
  - Role / Permission 的 code / is_builtin 只读, 内置对象 has_delete_permission 返回 False
    (防止从 admin 绕过 API 层的 is_builtin 保护)
  - AuditLog 全只读 (has_add/change/delete_permission 全 False), 审计不可篡改
  - UserProfile 既内联到 UserAdmin, 也独立注册 (方便按昵称/性别筛)
- 演示数据种子命令 (seed_demo):
  - 位置 apps/rbac/management/commands/seed_demo.py
  - 10 用户 (admin 超管 + user01~09) / 4 角色 (admin/editor/viewer/guest) / 2000 文章
  - 密码统一 admin; email 唯一 (userXX@example.com), 避免 unique 冲突
  - random.seed(42) 固定种子, 数据分布可复现, 方便性能对比
  - --flush 只清业务数据 (Article/UserRole/RolePermission/Role/UserProfile/非超管 User),
    保留 Permission (13) 和 CasbinRule (5)
  - 幂等: 用户/角色 get_or_create; 文章已有则跳过 (要重造加 --flush)
  - 用 bulk_create(batch_size=500) 批量插文章
  - seed 后遍历用户清权限缓存 (invalidate_user_perms)
- ABAC 性能优化 (get_queryset 粗筛 + 精筛):
  - 原写法: 拉全量 -> 逐行 enforce -> id__in 回查, 2000 篇约 0.41s
  - 优化后: 先用 Q 粗筛"作者本人 / 已发布"(策略上必然可见), 只对剩余行 enforce
  - 效果: enforce 2000 -> 1180 次, 0.41s -> 0.27s, 可见结果一致
  - 代价: 粗筛条件是策略的"软编码"(Q 对象写死 author/published),
    策略变更时需同步改 get_queryset, 属主流取舍 (完全动态则无法下推到 DB)
  - 未继续优化的原因: 剩余 1180 行按当前策略无法在 DB 层判定不可见,
    再压需把 Casbin 策略翻译成 SQL WHERE, 复杂度高且非主流
  - 后续真实项目应配分页 (只对当前页精筛), 而非继续抠单次 enforce 常数
- 用户资料修改接口 (PATCH /api/users/me/):
  - 读写序列化器分离: 读用 MeSerializer, 写用 MeUpdateSerializer (主流做法)
  - 可写字段: UserProfile 的 nickname / avatar / bio / gender / birthday / location
  - 不可写: username / phone / email / is_superuser / permissions
  - 写用 MeUpdateSerializer (source=profile.xxx 嵌套写, 覆盖 update 拆嵌套),
    响应统一用 MeSerializer 返回完整资源 (REST 惯例, 前端不用再 GET 一次)
  - get_serializer_class 按 request.method 分派: PUT/PATCH -> MeUpdateSerializer
  - 测试: users/tests.py 的 MeViewTests 覆盖 5 个 PATCH 用例
    (未登录 / 成功 / 部分字段 / 只读字段被忽略 / gender 非法)
- 权限点按模块分组 (Permission.module):
  - 加 module 字段, 从 code 自动推导: 取最后一个 ":" 之前的部分
    - article:read        -> article
    - rbac:role:read      -> rbac:role
    - rbac:audit_log:read -> rbac:audit_log
  - 推导逻辑在 Permission.derive_module (静态方法) + save() 兜底 (未填才推导)
  - 回填走 data migration (0012), 显式 set + save(update_fields=["module"]),
    不触发自定义 save (历史模型)
  - API 层 module 只读 (read_only_fields), 不允许手动改: module 是 code 的派生属性,
    手改会与 code 不一致 (与 Keycloak / Casbin 的处理一致)
  - 列表支持按 module 过滤 (?module=rbac:role) + 排序 (ordering=module)
  - 迁移: 0011 加字段, 0012 回填
- 数据级权限细化 (visibility 生效):
  - 策略变更 (迁移 0013): 旧策略 "status=published 即可读" 改为
    "status=published AND visibility=public 才可读"
  - 语义:
    - private 草稿/已发布: 仅作者本人 (作者全权策略覆盖)
    - public  + published: 任何人可读
    - team    + published: 暂等同 private (只作者可见)
  - team 的处理 (主流做法): 字段保留枚举, 策略先不处理, 等引入真实
    Org/Team 模型后再写 r.sub.org_id == r.obj.org_id 之类
  - get_queryset 粗筛同步改: Q(author=user) | Q(status=published, visibility=public)
    (策略改了粗筛必须同步改, 否则会出现安全漏洞: 粗筛放行了不该可见的行)
  - 验证: user01 可见数从 820 (旧策略) 降到 395 (新策略)
  - 测试: ArticleVisibilityPolicyTests 覆盖 public/private/team 三种 visibility
    + 作者本人可见自己的 private 文章
  - 迁移后需 restart web (清 enforcer lru_cache, 让新策略生效)
- Django admin 换 django-unfold 主题 (替代 simpleui):
  - 升级 Django 5.1.4 -> 5.2 (unfold 0.110 要求 django>=5.2)
  - 装 django-unfold==0.110.0, 卸 django-simpleui
  - INSTALLED_APPS 里 unfold 放 admin 之前; TEMPLATES 加 context_processors
  - UNFOLD 配置: SITE_TITLE / SITE_HEADER / SITE_SUBHEADER
  - 布尔字段渲染成开关: formfield_overrides = {models.BooleanField: {widget: UnfoldBooleanSwitchWidget}}
  - 列表页操作列: 自定义 list_display 方法 row_actions 返回 HTML (编辑/删除按钮)
  - 筛选从右侧挪顶部: list_filter_options = {字段: {"horizontal": True}}
  - 详情页分组: fieldsets 分 账号信息 / 权限状态 / 时间信息;
    exclude 掉 password / groups / user_permissions (项目走 JWT, 这三个没用)
- users 测试拆包:
  - apps/users/tests.py -> apps/users/tests/ (包)
  - test_api.py 原样搬入; test_admin.py 新增 6 个 admin 冒烟测试
  - Django test runner 自动发现 test_*.py
  - admin 冒烟测试能验证: 页面 200 / 未登录跳转 / 关键字段与按钮存在;
    但视觉样式 (开关样式 / 筛选位置) 仍靠人眼验证

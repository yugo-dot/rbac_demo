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
- 技术栈: Django 5.1.4 / DRF / SimpleJWT / MySQL 8.0 / Redis 7 / Docker
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

## 三、目录结构

rbac_demo/
├── apps/
│   ├── __init__.py
│   ├── users/
│   │   ├── models/
│   │   │   ├── __init__.py      (from .user import User)
│   │   │   └── user.py          (User 继承 AbstractUser)
│   │   └── migrations/
│   └── rbac/
│       ├── models/
│       │   ├── __init__.py      (导出 4 个模型)
│       │   ├── role.py
│       │   ├── permission.py
│       │   ├── user_role.py
│       │   └── role_permission.py
│       └── migrations/
├── config/
│   └── settings.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── PROGRESS.md

## 四、关键约定

- models 拆成包: 每个实体一个文件, __init__.py 统一导出
- 注释风格: 中文注释, 使用英文标点
- 权限编码格式: 模块:操作 (例如 article:create, user:delete)
- settings: 暂不拆分 base/dev/prod, 等部署前再拆

## 五、已完成

- [x] Docker 环境搭建
- [x] Django 项目骨架 (config/)
- [x] 自定义 User 模型 (AbstractUser + phone/email 唯一)
- [x] RBAC 四张表 (Role / Permission / UserRole / RolePermission)
- [x] 迁移成功, 数据库表已建
- [x] models 拆成包
- [x] User.get_permission_codes() 方法

## 六、Git 提交记录

- 858c64b chore: 初始化 Django 项目骨架与 Docker 环境
- b7dfbf9 feat: 切换数据库为 MySQL 并应用初始迁移
- 7d576c9 feat: 自定义 User 模型 + RBAC 四张表 (models 拆成包)
- e4e6a86 feat: User 增加 get_permission_codes 方法

## 七、下一步

1. [x] 给 User 加方法: get_permission_codes()
2. [ ] 写 JWT 登录接口 (用户名 / 手机号 / 邮箱 三选一)
3. [ ] 写角色 / 权限的 CRUD 接口
4. [ ] 写自定义权限类 HasPerm
5. [ ] 用 RBAC 保护示例接口, 写测试验证

## 八、当前卡点

- 无

## 九、常用命令

docker compose exec web bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
docker compose logs web --tail 50
docker compose restart web
git add . && git commit -m "xxx"

## 十、关键文件内容 (交接时必读)

新 AI 需要知道当前代码长什么样. 交接时请用户执行以下命令, 把输出贴给你:

cat apps/users/models/user.py
cat apps/users/models/__init__.py
cat apps/rbac/models/__init__.py
cat apps/rbac/models/role.py
cat apps/rbac/models/permission.py
cat apps/rbac/models/user_role.py
cat apps/rbac/models/role_permission.py
cat config/settings.py

## 十一、设计决策记录

- User 继承 AbstractUser: 省事, admin 兼容, 不折腾 AbstractBaseUser
- phone/email 用 unique=True + null=True + blank=True: 允许不填, 填了必须唯一
- 关联表用独立 Model (UserRole / RolePermission): 便于以后加审计字段
- models 拆成包: 每个实体一个文件, __init__.py 统一导出, Django 通过导入发现模型
- 权限编码格式: 模块:操作 (article:create)
- 关联表暂不用 Django 自带 auth_group / auth_permission, 用自己的 rbac 表

## 十二、协作方式约定

- 沟通节奏: 一次只走一步, 用户确认后再给下一步
- 代码风格: 中文注释, 英文标点
- 文件输出: 纯文本块, 不要嵌套代码块
- 每完成一个阶段: 更新本文档的"已完成"和"下一步"
- 每次改动后: 单独 git commit, 信息用中文

# RBAC Demo

[![CI](https://github.com/yugo-dot/rbac_demo/actions/workflows/ci.yml/badge.svg)](https://github.com/yugo-dot/rbac_demo/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Django](https://img.shields.io/badge/Django-5.1-green)
![License](https://img.shields.io/badge/license-MIT-blue)

一个基于 **Django + DRF** 的 **RBAC + ABAC** 权限系统学习项目。

## 功能特性

### RBAC (基于角色的访问控制)
- 用户 / 角色 / 权限三张核心表 + 两张关联表
- 角色 / 权限的完整 CRUD 接口
- 用户-角色 / 角色-权限分配接口
- 自定义权限类 HasPerm, 按 HTTP 方法细粒度控制
- 内置角色/权限保护 (is_builtin, 禁止删改)
- 用户权限 Redis 缓存 (主动失效 + TTL 兜底)

### ABAC (基于属性的访问控制)
- 集成 Casbin, 策略存 MySQL
- 对象级权限 (HasAbacPerm), 判"能不能操作这一条数据"
- 策略管理接口 (/api/rbac/policies/)
- 预置 5 条默认策略 (作者全权 / 已发布公开 / 主编可读)

### 认证
- JWT 登录 (用户名 / 手机号 / 邮箱三选一)
- 注册 / 改密 / 登出 / 刷新 token
- 基于 SimpleJWT blacklist, 改密后强制重登

### 工程实践
- 完整单元测试 (53 个, 本地 + CI 都跑)
- GitHub Actions CI (MySQL 8.0 + Redis 7)
- ruff + pre-commit (commit 前自动 lint/format)
- API 文档 (drf-spectacular, Swagger UI)
- settings 拆分 base/dev/prod

## 技术栈

- 后端: Django 5.1 + DRF 3.15
- 认证: SimpleJWT 5.3 (含 blacklist)
- 权限: 自研 RBAC + Casbin (ABAC)
- 数据库: MySQL 8.0
- 缓存: Redis 7
- API 文档: drf-spectacular
- 部署: Docker
- CI: GitHub Actions

## 快速开始

### 前置要求
- Docker + Docker Compose
- 一个外部的 MySQL / Redis 容器 (项目通过 shared-services 网络连接)

### 启动

    git clone git@github.com:yugo-dot/rbac_demo.git
    cd rbac_demo
    docker compose up -d
    docker compose exec web python manage.py migrate
    docker compose exec web python manage.py createsuperuser
    docker compose exec web python manage.py test users rbac articles

### 访问

- API 文档 (Swagger): http://localhost:8000/api/docs/
- Django admin: http://localhost:8000/admin/

## API 概览

| 模块 | 路径 | 说明 |
|---|---|---|
| 认证 | /api/users/ | 登录 / 注册 / 改密 / 登出 / me |
| RBAC 管理 | /api/rbac/ | 角色 / 权限 / 用户角色 / 策略 |
| 文章 | /api/demo/articles/ | ABAC 保护的文章 CRUD |

完整接口见 Swagger UI。

## 架构简介

### 两层权限模型

    请求 -> HasPerm (接口级, RBAC)
         -> HasAbacPerm (对象级, ABAC)
         -> 访问数据

- HasPerm: 检查用户是否有 article:read 等权限编码
- HasAbacPerm: 用 Casbin 判"这个用户能不能操作这条文章"

### 数据级权限

列表接口在 get_queryset 里按 ABAC 规则过滤, 只返回用户可见的数据。
单条接口在 has_object_permission 里逐对象判断。

越权访问返回 404 而非 403 (不泄露"数据存在"的信息)。

## 测试

    docker compose exec web python manage.py test users rbac articles
    docker compose exec web python manage.py test rbac
    docker compose exec web python manage.py test -v 2

## 项目结构

    rbac_demo/
    ├── apps/
    │   ├── users/        # 用户 + 认证
    │   ├── rbac/         # RBAC + ABAC (Casbin)
    │   └── articles/     # 示例业务 (被 ABAC 保护)
    ├── config/
    │   └── settings/     # base / dev / prod
    ├── casbin_model.conf # Casbin ABAC 模型定义
    ├── pyproject.toml    # ruff 配置
    ├── CONTEXT.md        # 项目上下文 (设计决策)
    └── PROGRESS.md       # 项目进度

## 文档

- [CONTEXT.md](CONTEXT.md) - 项目上下文、设计决策记录
- [PROGRESS.md](PROGRESS.md) - 已完成 / 下一步 / 卡点

## License

[MIT](LICENSE)

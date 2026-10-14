"""Django base settings (公共配置)."""

import os
import sys
from datetime import timedelta
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 把 apps/ 加入 Python 路径, 这样可以直接 import users / rbac
sys.path.insert(0, os.path.join(BASE_DIR, "apps"))


# 安全配置 (从环境变量读, 有默认值)
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-3xj@bd%-n=g$^p^4b6nk)hd8qhl&^94aukt4sv!vpqrrh4c7iy",
)


# 应用注册
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 第三方
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    # 业务 app
    "users",
    "rbac",
    "articles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# 数据库
# 本地开发 / 生产: MySQL (默认)
# CI: SQLite (设置环境变量 USE_SQLITE=true), 因为 Gitee Go 托管环境没有 MySQL 服务
if os.environ.get("USE_SQLITE") == "true":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("DB_NAME", "rbac_demo"),
            "USER": os.environ.get("DB_USER", "rbac_user"),
            "PASSWORD": os.environ.get("DB_PASSWORD", "rbac_pass_123"),
            "HOST": os.environ.get("DB_HOST", "mysql"),
            "PORT": os.environ.get("DB_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }


# 密码校验
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# 国际化
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True


# 静态文件
STATIC_URL = "static/"


# 默认主键类型
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# 自定义用户模型
AUTH_USER_MODEL = "users.User"


# 缓存
# 跑测试时用 locmem, 避免污染生产 Redis; 其他场景用 Redis.
if "test" in sys.argv:
    # 测试环境禁用缓存: 避免跨测试类的缓存污染 (用户 ID 重复 + LocMemCache 进程级)
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
    }
else:
    # Redis 地址从环境变量读: 本地 Docker 是 redis:6379, CI 是 127.0.0.1:6379
    redis_host = os.environ.get("REDIS_HOST", "redis")
    redis_port = os.environ.get("REDIS_PORT", "6379")
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f"redis://{redis_host}:{redis_port}/1",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "IGNORE_EXCEPTIONS": True,
            },
        }
    }


# DRF 配置
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # 分页
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # 过滤 / 搜索 / 排序
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
}


# drf-spectacular 配置
SPECTACULAR_SETTINGS = {
    "TITLE": "RBAC Demo API",
    "DESCRIPTION": "Django + DRF RBAC 学习项目的接口文档",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "COMPONENT_SPLIT_REQUEST": True,
    # 使用 sidecar 提供本地静态文件, 不走 CDN
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
}


# SimpleJWT 配置
# Casbin 策略存储 (策略存 MySQL, 通过 casbin_adapter)
CASBIN_MODEL = os.path.join(BASE_DIR, "casbin_model.conf")


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=2),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    # blacklist: 登出 / 改密后让旧 refresh 失效
    "ROTATE_REFRESH_TOKENS": True,  # 刷新时换发新 refresh
    "BLACKLIST_AFTER_ROTATION": True,  # 旧的 refresh 拉黑
}


# 审计日志: True 时也记录 read 操作 (默认只记写)
AUDIT_LOG_READ_OPERATIONS = False

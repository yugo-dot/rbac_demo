"""生产环境配置."""

import os

from .base import *  # noqa: F401, F403

DEBUG = False

# 从环境变量读, 逗号分隔. 例如 ALLOWED_HOSTS=api.example.com,www.example.com
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()]

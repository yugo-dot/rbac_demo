"""演示数据种子命令.

用法:
    python manage.py seed_demo                # 默认造 2000 篇文章 (不清旧数据)
    python manage.py seed_demo --articles 500 # 自定义文章数
    python manage.py seed_demo --flush        # 先清业务数据再造

清理范围 (--flush):
- Article / UserRole / RolePermission / Role / UserProfile / 非超管 User
- 不动 Permission (13 个种子权限) 和 CasbinRule (5 条策略)

密码统一为 admin, 超管账号 admin / admin.
"""

import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from articles.models import Article
from rbac.cache import invalidate_user_perms
from rbac.models import Permission, Role, RolePermission, UserRole
from users.models import UserProfile

User = get_user_model()

# 固定随机种子, 保证每次生成的数据分布一致, 方便性能对比
RANDOM_SEED = 42

# 角色 -> 权限编码列表
ROLE_PERMS = {
    "admin": [
        "article:read",
        "article:create",
        "article:update",
        "article:delete",
        "rbac:role:read",
        "rbac:role:manage",
        "rbac:permission:read",
        "rbac:permission:manage",
        "rbac:user_role:read",
        "rbac:user_role:manage",
        "rbac:policy:read",
        "rbac:policy:manage",
        "rbac:audit_log:read",
    ],
    "editor": ["article:read", "article:create", "article:update", "article:delete"],
    "viewer": ["article:read"],
    "guest": [],
}

# 用户名 -> 角色编码
USER_ROLES = {
    "admin": "admin",
    "user01": "editor",
    "user02": "editor",
    "user03": "editor",
    "user04": "viewer",
    "user05": "viewer",
    "user06": "viewer",
    "user07": "guest",
    "user08": "guest",
    "user09": "guest",
}

STATUS_LIST = [Article.STATUS_DRAFT, Article.STATUS_PUBLISHED, Article.STATUS_ARCHIVED]
VISIBILITY_LIST = [Article.VISIBILITY_PRIVATE, Article.VISIBILITY_TEAM, Article.VISIBILITY_PUBLIC]


class Command(BaseCommand):
    help = "造演示数据: 用户 / 角色 / 权限分配 / 文章"

    def add_arguments(self, parser):
        parser.add_argument(
            "--articles",
            type=int,
            default=2000,
            help="生成的文章数量 (默认 2000)",
        )
        parser.add_argument(
            "--flush",
            action="store_true",
            help="先清空业务数据 (保留 Permission 和 CasbinRule)",
        )

    def handle(self, *args, **options):
        random.seed(RANDOM_SEED)
        article_count = options["articles"]

        if options["flush"]:
            self._flush_business_data()

        users = self._create_users()
        roles = self._create_roles()
        self._assign_role_perms(roles)
        self._assign_user_roles(users, roles)
        self._create_profiles(users)
        self._create_articles(users, article_count)
        self._clear_caches(users)

        self.stdout.write(self.style.SUCCESS("演示数据生成完成"))
        self.stdout.write(f"  用户: {User.objects.count()}")
        self.stdout.write(f"  角色: {Role.objects.count()}")
        self.stdout.write(f"  文章: {Article.objects.count()}")

    # ---------- 内部方法 ----------

    def _flush_business_data(self):
        """清空业务数据, 保留种子权限和 Casbin 策略."""
        self.stdout.write("清空业务数据 (保留 Permission / CasbinRule)...")
        Article.objects.all().delete()
        UserRole.objects.all().delete()
        RolePermission.objects.all().delete()
        Role.objects.all().delete()
        UserProfile.objects.all().delete()
        # 只删非超管, 避免误删手工建的运维账号
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write("  完成")

    def _create_users(self):
        """创建 10 个用户, 密码统一 admin."""
        self.stdout.write("创建用户...")
        users = {}
        for username, _ in USER_ROLES.items():
            email = f"{username}@example.com"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": email},
            )
            user.set_password("admin")
            user.is_active = True
            if username == "admin":
                user.is_superuser = True
                user.is_staff = True
            user.save()
            users[username] = user
            if created:
                self.stdout.write(f"  + {username}")
        return users

    def _create_roles(self):
        """创建 4 个非内置角色."""
        self.stdout.write("创建角色...")
        roles = {}
        for code in ROLE_PERMS:
            role, created = Role.objects.get_or_create(
                code=code,
                defaults={"name": code, "description": f"{code} 角色 (演示数据)"},
            )
            roles[code] = role
            if created:
                self.stdout.write(f"  + {code}")
        return roles

    def _assign_role_perms(self, roles):
        """把权限点分配给角色."""
        self.stdout.write("分配角色权限...")
        perm_map = {p.code: p for p in Permission.objects.all()}
        for role_code, perm_codes in ROLE_PERMS.items():
            role = roles[role_code]
            for code in perm_codes:
                perm = perm_map.get(code)
                if perm is None:
                    self.stdout.write(self.style.WARNING(f"  权限点不存在: {code}"))
                    continue
                RolePermission.objects.get_or_create(role=role, permission=perm)

    def _assign_user_roles(self, users, roles):
        """把角色分配给用户."""
        self.stdout.write("分配用户角色...")
        for username, role_code in USER_ROLES.items():
            UserRole.objects.get_or_create(user=users[username], role=roles[role_code])

    def _create_profiles(self, users):
        """补 UserProfile 的昵称 (signal 已建记录, 这里补字段)."""
        self.stdout.write("补用户资料...")
        for username, user in users.items():
            profile = getattr(user, "profile", None)
            if profile is None:
                # signal 没建的话兜底
                profile = UserProfile.objects.create(user=user)
            if not profile.nickname:
                profile.nickname = f"昵称_{username}"
                profile.save(update_fields=["nickname"])

    def _create_articles(self, users, count):
        """批量创建文章, 作者从普通用户里随机 (排除超管)."""
        self.stdout.write(f"创建 {count} 篇文章...")
        author_ids = [u.id for name, u in users.items() if name != "admin"]
        if not author_ids:
            self.stdout.write(self.style.WARNING("  没有可用的普通用户, 跳过"))
            return

        # 已存在则跳过, 避免重复插
        existing = Article.objects.count()
        if existing > 0:
            self.stdout.write(f"  已有 {existing} 篇, 跳过 (要重造请加 --flush)")
            return

        articles = []
        for i in range(count):
            articles.append(
                Article(
                    title=f"演示文章 {i + 1}",
                    body=f"这是第 {i + 1} 篇演示文章的正文, 用于 ABAC 性能测试.",
                    author_id=random.choice(author_ids),
                    status=random.choice(STATUS_LIST),
                    visibility=random.choice(VISIBILITY_LIST),
                )
            )

        with transaction.atomic():
            Article.objects.bulk_create(articles, batch_size=500)
        self.stdout.write(f"  完成, 共 {len(articles)} 篇")

    def _clear_caches(self, users):
        """清所有用户的权限缓存, 避免读到旧数据."""
        self.stdout.write("清理权限缓存...")
        for user in users.values():
            invalidate_user_perms(user.id)

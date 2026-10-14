from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """用户资料, 与 User 一对一.

    存放展示类 / 可选类字段; 登录相关字段 (username / phone / email / password) 仍在 User 上.
    """

    GENDER_CHOICES = (
        (0, "未知"),
        (1, "男"),
        (2, "女"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="用户",
    )
    nickname = models.CharField(max_length=50, blank=True, verbose_name="昵称")
    avatar = models.URLField(max_length=500, blank=True, verbose_name="头像地址")
    bio = models.CharField(max_length=200, blank=True, verbose_name="个人简介")
    gender = models.SmallIntegerField(default=0, choices=GENDER_CHOICES, verbose_name="性别")
    birthday = models.DateField(null=True, blank=True, verbose_name="生日")
    location = models.CharField(max_length=100, blank=True, verbose_name="所在地")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "user_profile"
        verbose_name = "用户资料"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user.username} 的资料"

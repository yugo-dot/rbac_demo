from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """自定义用户模型, 继承 Django 自带的 AbstractUser.

    登录支持三种凭证: username / phone / email.
    phone 和 email 允许为空, 但一旦填写则必须唯一.
    """

    nickname = models.CharField(max_length=50, blank=True, verbose_name='昵称')
    phone = models.CharField(
        max_length=20, unique=True, null=True, blank=True, verbose_name='手机号'
    )
    email = models.EmailField(
        unique=True, null=True, blank=True, verbose_name='邮箱'
    )
    avatar = models.URLField(max_length=500, blank=True, verbose_name='头像地址')

    class Meta:
        db_table = 'user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username

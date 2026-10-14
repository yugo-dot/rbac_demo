from rest_framework import serializers


class PolicySerializer(serializers.Serializer):
    """策略序列化器.

    策略不是 Django 模型, 是 casbin_rule 表里的行, 所以用普通 Serializer.
    - id: 只读, 列表返回时带
    - sub_rule: 主体条件表达式, 如 'r.sub.id == r.obj.author_id'
    - obj: 资源类型字符串, 如 'article'
    - act: 动作字符串, 如 'read' / 'create' / 'update' / 'delete' / '*'
    """

    id = serializers.IntegerField(read_only=True)
    sub_rule = serializers.CharField(max_length=255)
    obj = serializers.CharField(max_length=255)
    act = serializers.CharField(max_length=255)

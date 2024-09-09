from tortoise import fields
from tortoise.models import Model

class User(Model):
    id = fields.IntField(pk=True)
    user_id = fields.BigIntField(unique=True, null=True)
    username = fields.CharField(max_length=255, null=True)
    first_name = fields.CharField(max_length=255, null=True)
    registered = fields.BooleanField(default=False)
    phone_number = fields.CharField(max_length=20, null=True)
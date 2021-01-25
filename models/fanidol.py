import peewee as pw
from models.base_model import BaseModel
from models.user import User

class Fanidol(BaseModel):
    fan = pw.ForeignKeyField(User, on_delete="CASCADE")
    idol = pw.ForeignKeyField(User)
    is_approved = pw.BooleanField(default=False)
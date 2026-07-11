# Import all the models, so that Base has them before being
# imported by Alembic
from python_example.db.base_class import Base  # noqa
from python_example.models.item import Item  # noqa
from python_example.models.user import User  # noqa

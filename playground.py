from src import model_meta
from src import properties
from src.query_builder import *
from src.model_meta import ModelMeta
from src.properties import *
from src.repository import SqlRepository
from src.connection import SqliteConnection


class BaseModel(ModelMeta):
    repository = SqlRepository(SqliteConnection("database.db"))


class Person(BaseModel):
    id = PrimaryKey()
    name = StringProperty()
    age = IntProperty()
    height = IntProperty()


Person.init_class()


class ServiceInfo(BaseModel):
    id = PrimaryKey()
    name = StringProperty()


ServiceInfo.init_class()


class Service(BaseModel):
    id = PrimaryKey()
    name = StringProperty()
    info = ListProperty(ServiceInfo)


Service.init_class()


class User(Person):
    username = StringProperty()
    password = StringProperty()
    services = ListProperty(Service)


User.init_class()


if __name__ == "__main__":

    sample_services_info = []

    for i in range(10):
        service_info = ServiceInfo(name=f"Service Info {i+1}")
        service_info.save()
        sample_services_info.append(service_info)

    import random
    sample_services = []
    for i in range(10):
        service = Service(
            name=f"Service {i+1}", info=random.sample(sample_services_info, random.randint(1, 10)))
        service.save()
        sample_services.append(service)

    sample_users = []

    for i in range(10):
        user = User(name=f"User {i+1}", age=i+1, height=i+1, username=f"username{i+1}", password=f"password{i+1}", services=random.sample(sample_services, random.randint(1, 10))
                    )
        user.save()
        sample_users.append(user)

    selected_users = User.selection.evaluate()

    users = selected_users[7:9]

    for user in users:
        print(user)

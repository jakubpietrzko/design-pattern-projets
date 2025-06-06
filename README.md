# Object-Relational Mapping

This project implements a toolset for creating object-rational mapping between a relational database structures (SQLite) and a set of object-oriented representations.

## Example usage

First, you have to create base class for your entity models that initializs repository
```python
class BaseModel(ModelMeta):
    repository = SqlRepository(SqliteConnection("database.db"))
```

Then, you can create entities, and add them to database - init_class function
```python
class StudentsClass(BaseModel):
    id = properties.PrimaryKey()
    name = properties.StringProperty()

StudentsClass.init_class()

class Person(BaseModel):
    id = properties.PrimaryKey()
    name = properties.StringProperty()
    age = properties.IntProperty()

Person.init_class()

class Student(Person):
    indexx = properties.IntProperty()
    class_ = properties.ForeignKey(StudentsClass)

Student.init_class()
```

Now you can perform operations on the database
```python
class_ = StudentsClass(name="3A")
class_.save()
student = Student(name="John", age=20, indexx=123, class_=class_)
student.save()
student.age += 1
student.save()
students = Student.selection.evaluate()
print(students)
```

Output should look like that
```
[Student(indexx=123, klass=Klass(name=3A, id=1), name=John, age=21, id=1)]
```

More examples in tests
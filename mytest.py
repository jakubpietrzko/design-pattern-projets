import unittest
from src import model_meta
from src import properties
from src.query_builder import *
from src.model_meta import ModelMeta
from src.properties import *
from src.repository import SqlRepository
from src.connection import SqliteConnection
import sqlite3


class BaseModel(ModelMeta):
    repository = SqlRepository(SqliteConnection("databases//test.db"))


class Person(BaseModel):
    id = properties.PrimaryKey()
    name = properties.StringProperty()
    age = properties.IntProperty()


class Tests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect('databases/test.db')
        self.cursor = self.conn.cursor()
        Person.init_class()

    def tearDown(self):
        self.conn.close()

    # Sti
    def test_inheritance(self):
        class Student(Person):
            indexx = properties.IntProperty()
        Student.init_class()

        # Sprawdź, czy tabela Student istnieje
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='Person';")
        self.assertIsNotNone(self.cursor.fetchone(),
                             "Tabela Student nie istnieje")

        # Sprawdź kolumny w tabeli Student
        self.cursor.execute("PRAGMA table_info(Person);")
        columns = [column[1] for column in self.cursor.fetchall()]
        expected_columns = ['id', 'name', 'age', 'indexx']
        self.assertListEqual(columns, expected_columns,
                             "Kolumny tabeli Person są nieprawidłowe")

    def test_foreign(self):
        class X(BaseModel):
            id = properties.PrimaryKey()
            name = properties.StringProperty()
            person = properties.ForeignKey(Person)
        X.init_class()
        person = Person(name="xdd", age=20)
        person.save()
        xdd = X(name="xdd", person=person)
        xdd.save()
        res = self.cursor.execute("SELECT * FROM X;")
        rows = res.fetchall()
        # print(rows)
        self.assertEqual(len(rows), 1, "Niepoprawna liczba wyników")

    def test_table_creation_with_list_properties(self):
        class Class(BaseModel):
            id = properties.PrimaryKey()
            name = properties.StringProperty()
            people = properties.ListProperty(Person)
        Class.init_class()
        # Sprawdź, czy tabela Class istnieje
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='Class';")
        result = self.cursor.fetchone()
        self.assertIsNotNone(result, "Tabela Class nie istnieje")

    def test_save(self):
        person = Person(name="xdd", age=20)
        person.save()
        res = self.cursor.execute("SELECT * FROM Person;")
        rows = res.fetchall()

        # Sprawdzanie, czy tabela Person zawiera przynajmniej jeden wiersz
        self.assertTrue(rows, "Tabela Person jest pusta")

        # Sprawdzanie, czy ostatni dodany wiersz jest poprawny
        last_row = rows[-1]
        self.assertEqual(last_row[1], "xdd", "Imię osoby nie zgadza się")
        self.assertEqual(last_row[2], 20, "Wiek osoby nie zgadza się")

    def test_save_list_property(self):
        class Class(BaseModel):
            id = properties.PrimaryKey()
            name = properties.StringProperty()
            people = properties.ListProperty(Person)
        Class.init_class()
        person = Person(name="xdd2", age=23)
        person.save()
        classs = Class(name="4d", people=[person])
        classs.save()
        res = self.cursor.execute("SELECT * FROM Class;")
        rows = res.fetchall()

        # Sprawdzanie, czy tabela Class zawiera przynajmniej jeden wiersz
        self.assertTrue(rows, "Tabela Class jest pusta")

        # Sprawdzanie, czy ostatni dodany wiersz jest poprawny
        last_row = rows[-1]
        # print(last_row)
        self.assertEqual(last_row[1], "4d", "Nazwa klasy nie zgadza się")
        res = self.cursor.execute("SELECT * FROM Class_people;")
        rows = res.fetchall()
        # Sprawdzanie, czy tabela Class zawiera przynajmniej jeden wiersz
        self.assertTrue(rows, "Tabela Class_people jest pusta")

        # Sprawdzanie, czy ostatni dodany wiersz jest poprawny
        last_row = rows[-1]
        # print(last_row)
        self.assertEqual(last_row[0], classs.id, "id klasy nie zgadza się")
        self.assertEqual(last_row[1], person.id, "id osoby nie zgadza się")

    def test_evaluate(self):
        person = Person(name="wikson", age=20)
        person.save()
        person2 = Person(name="ryszard", age=21)
        person2.save()
        person3 = Person(name="witek", age=22)
        # person3.save()
        person3.save()
        person4 = Person(name="kubson", age=23)
        person4.save()
        condition = Or(Equals(Person.age, 20), Equals(Person.age, 21))
        result = Person.selection.where(condition).evaluate()
        # print(result)
        self.assertEqual(len(result), 2, "Niepoprawna liczba wyników")

    def test_evaluate_list_prop(self):
        class Class(BaseModel):
            id = properties.PrimaryKey()
            name = properties.StringProperty()
            people = properties.ListProperty(Person)
        Class.init_class()
        person = Person(name="wikson", age=20)
        person.save()
        person2 = Person(name="ryszard", age=21)
        person2.save()
        person3 = Person(name="witek", age=22)
        person3.save()
        person4 = Person(name="kubson", age=23)
        person4.save()
        classs1 = Class(name="3a", people=[person, person2])
        classs1.save()
        classs = Class(name="4d", people=[person3, person4])
        classs.save()
        result = Class.selection.evaluate()
        self.assertEqual(len(result), 2, "Niepoprawna liczba wyników")

    def test_updating(self):
        person = Person(name="alb", age=20)
        person.save()
        res = self.cursor.execute("SELECT * FROM Person;")
        rows = res.fetchall()
        # print(rows)
        len_rows = len(rows)
        person.age = 99
        person.save()
        res = self.cursor.execute("SELECT * FROM Person;")
        rows = res.fetchall()
        # print(rows)
        len_rows_after = len(rows)
        rows = rows[-1]
        self.assertEqual(len_rows, len_rows_after,
                         "nie aktualizuje tylko dodaje nowe")
        self.assertEqual(rows[2], 99, "Imię osoby nie zgadza się")

    def test_list_updating(self):
        class Class(BaseModel):
            id = properties.PrimaryKey()
            people = properties.ListProperty(Person)
            name = properties.StringProperty()

        Class.init_class()
        person = Person(name="wikson", age=20)
        person.save()
        person2 = Person(name="ryszard", age=21)
        person2.save()
        person3 = Person(name="witek", age=22)
        person3.save()
        class_ = Class(name="3a", people=[person, person2])
        class_.save()
        class_.people = [person2, person3]
        class_.save()

        res = Class.selection.evaluate()
        self.assertNotEqual(len(res), 0, "Empty response")
        self.assertEqual(len(res[0].people), 2, "People not added to class")
        self.assertIn(res[0].people[0].name, ["ryszard",
                      "witek"], "Table not updating properly")
        self.assertIn(res[0].people[1].name, ["ryszard",
                      "witek"], "Table not updating properly")

    def test_double_save(self):
        person = Person(name="alb", age=20)
        person.save()
        person2 = Person(name="dosef", age=21)
        person2.save()
        person3 = Person(name="dfse", age=22)
        person3.save()
        person4 = Person(name="en", age=23)
        person4.save()
        person.name = "alb2"
        person.save()
        xd = Person.selection.where(LessThan(Person.age, 22)).evaluate()
        # print(xd)
        self.assertEqual(len(xd), 2, "Niepoprawna liczba wyników")

    def test_del(self):
        person = Person(name="alb", age=20)
        person.save()
        person2 = Person(name="dosef", age=21)
        person2.save()
        person3 = Person(name="dfse", age=22)
        person3.save()
        person4 = Person(name="en", age=23)
        person4.save()

        person.delete_object()
        xd = Person.selection.where(LessThan(Person.age, 22)).evaluate()
        # print(xd)
        self.assertEqual(len(xd), 1, "Niepoprawna liczba wyników ")
        xdd = Person.selection.evaluate()
        cnt = 0
        for i in xdd:
            if cnt == 2:
                break
            cnt += 1
            i.delete_object()
        # print(xdd)
        # print(Person.selection.evaluate())
        res = self.cursor.execute("SELECT * FROM Person;")
        rows = res.fetchall()
        # print(rows)
        self.assertEqual(len(rows), 1, "Niepoprawna liczba wyników")
        person5 = Person(name="alb", age=20)
        person5.save()
        person5.name = "alb2"
        person5.save()
        xd = Person.selection.evaluate()
        # print(xd)
        self.assertEqual(len(xd), 2, "Niepoprawna liczba wyników")

    def test_del_with_list_property(self):
        person = Person(name="alb", age=20)
        person.save()
        person2 = Person(name="dosef", age=21)
        person2.save()

        class Class(BaseModel):
            id = properties.PrimaryKey()
            name = properties.StringProperty()
            people = properties.ListProperty(Person)
        Class.init_class()
        classs = Class(name="4d", people=[person, person2])
        classs.save()
        res = self.cursor.execute("SELECT * FROM Class_people;")
        rows = res.fetchall()
        # print(rows)
        len_rows = len(rows)
        classs.delete_object()
        res = self.cursor.execute("SELECT * FROM Class_people;")
        rows = res.fetchall()
        # print(rows)
        len_rows_after = len(rows)
        self.assertEqual(len_rows, len_rows_after+2,
                         "Niepoprawna liczba wyników")
        classs = Class(name="5d", people=[person, person2])
        classs.save()
        classs.people = [person2]
        classs.save()
        res = self.cursor.execute("SELECT * FROM Class_people;")
        rows = res.fetchall()
        # print(rows)
        xddd = Class.selection.evaluate()
        # print(xddd)

    def test_del_model(self):
        class Grades(BaseModel):
            id = properties.PrimaryKey()
            grade = properties.IntProperty()
        Grades.init_class()

        class Student(BaseModel):
            id = properties.PrimaryKey()
            name = properties.StringProperty()
            age = properties.IntProperty()
            results = properties.ListProperty(Grades)
        Student.init_class()

        spr1 = Grades(grade=5)
        spr1.save()
        egz = Grades(grade=5)
        egz.save()
        kol = Grades(grade=5)
        kol.save()
        student = Student(name="alb", age=20, results=[spr1, egz, kol])
        student.save()
        res = self.cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='Student';")
        self.assertTrue(bool(res.fetchone()))
        res = self.cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='Student_results';")
        self.assertTrue(bool(res.fetchone()))
        Student.delete_model()
        res = self.cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='Student';")
        self.assertFalse(bool(res.fetchone()))
        res = self.cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='Student_results';")
        self.assertFalse(bool(res.fetchone()))
        res = self.cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='Grades';")
        self.assertTrue(bool(res.fetchone()))

    def test_float_property(self):
        class TestFloat(BaseModel):
            test_id = PrimaryKey()
            num = FloatProperty()

        TestFloat.init_class()
        TestFloat(num=0.4).save()
        res = TestFloat.selection.where(Equals(TestFloat.num, 0.4)).evaluate()
        self.assertNotEqual(len(res), 0)
        obj = res[0]
        self.assertAlmostEqual(obj.num, 0.4)


if __name__ == "__main__":
    unittest.main()

from src.connection import Connection
from src.properties import *
from abc import ABC, abstractmethod


class Repository(ABC):
    @abstractmethod
    def insert_object(self, obj: type['ModelMeta']):
        ...

    @abstractmethod
    def delete_model(self, model: type["ModelMeta"]):
        ...

    @abstractmethod
    def delete_object(self, obj: type['ModelMeta']):
        ...

    @abstractmethod
    def update_row(self, model, id, values):
        ...

    @abstractmethod
    def get_rows(self, query):
        ...

    @abstractmethod
    def migrate(self, model: type["ModelMeta"]):
        ...

    @abstractmethod
    def get_objects(self, model: type["ModelMeta"], ids: List[int]):
        ...

    @abstractmethod
    def row_exists(self, model, id):
        ...

    @abstractmethod
    def update_cache(self, objects: List["ModelMeta"]):
        ...


class SqlRepository(Repository):
    def __init__(self, connection: Connection) -> None:
        self._connection = connection
        self._cache = dict()

    @property
    def connection(self):
        return self._connection

    def get_objects(self, model: type["ModelMeta"], ids: List[int]):
        """Returns requested objects from cache.

        Args:
            ids: List of ids of objects to be returned.
        """

        if model not in self._cache:
            self._cache[model] = []

        return [obj for obj in self._cache[model] if getattr(obj, obj.primary_key.name) in ids]

    def update_cache(self, objects: List["ModelMeta"]):
        """Updates cache with new objects.

        Args:
            objects: List of objects to be added to cache.
        """

        for obj in objects:
            if type(obj) not in self._cache:
                self._cache[type(obj)] = []

            self._cache[type(obj)].append(obj)

    def migrate(self, model: type["ModelMeta"]):
        """
        Class method responsible for creating or updating database
        table associated with the class. It first drops the existing table (if
        it exists) and then creates a new table with the appropriate fields
        based on the class properties.

        Note:
            Running this deletes all existing data in table!
        """

        def is_child_of_another_model(model: type["ModelMeta"]):
            parent = model.__bases__[0]

            if parent.__bases__[0].__name__ == "ModelMeta":
                return False

            return True

        self._cache[model] = []

        if is_child_of_another_model(model):
            parent = model.__bases__[0]
            parent_properties = parent.properties
            child_properties = model.properties

            new_properties = {
                prop for prop in child_properties if prop not in parent_properties
            }

            for property in new_properties:
                self._add_new_property(property, model)

        # The model is the base class.
        else:
            self._execute_query(f"DROP TABLE IF EXISTS {model.table_name}")

            query = f"CREATE TABLE IF NOT EXISTS {model.table_name} ({model.primary_key.name} {model.primary_key.get_type_str()})"
            self._execute_query(query)

            for property in [
                prop for prop in model.properties if prop != model.primary_key
            ]:
                self._add_new_property(property, model)

    def row_exists(self, model, id):
        """Checks if a row with the given object's id exists in the database.

        Args:
            obj: The object whose id is to be checked.

        Returns:
            True if the row exists, False otherwise.
        """

        table_name = model.table_name
        query = f"SELECT 1 FROM {table_name} WHERE id = {id} LIMIT 1"
        result = self._execute_query(query)
        return len(result) > 0

    def _insert(self, model, values):
        """
        inserts new row to table
        """

        table_name = model.table_name

        vals = [f'"{val}"' if type(
            val) == str else val for val in values.values()]
        vals = ["NULL" if ":" in str(val) else val for val in vals]
        vals, columns = ', '.join([str(i) for i in vals]), ', '.join(
            [str(i) for i in values.keys()])

        query = f'INSERT OR REPLACE INTO {table_name} ({columns}) VALUES ({vals})'

        return self._execute_query(query)

    def delete_object(self, obj: type['ModelMeta']):
        """Deletes object from database.

        Args:
            obj: Object to be deleted.
        """

        if obj not in self._cache[type(obj)]:
            return

        model = obj.__class__
        table_name = model.table_name
        obj_id = getattr(obj, obj.primary_key.name)
        list_properties = [prop for prop in model.properties if isinstance(
            prop, ListProperty)]
        for list_prop in list_properties:
            # Create a new table for the ListProperty
            list_table_name = f"{model.table_name}_{list_prop.name}"
            # Delete old rows
            self._execute_query(
                f"DELETE FROM {list_table_name} WHERE {model.table_name}_id = {obj_id}")

        query = f'DELETE FROM {table_name} WHERE id = {obj_id}'
        self._execute_query(query)
        self._cache[model].remove(obj)

    def insert_object(self, obj: 'ModelMeta'):
        """Inserts object into database.

        Args:
            obj: Object to be inserted.
        """

        model = obj.__class__

        properties = [prop for prop in model.properties if not isinstance(
            prop, ListProperty)]

        values = dict()

        for prop in properties:
            if isinstance(prop, ForeignKey):
                values[prop.name] = getattr(
                    getattr(obj, prop.name), getattr(obj, prop.name).primary_key.name)

            elif not isinstance(prop, PrimaryKey):
                values[prop.name] = getattr(obj, prop.name)

        obj_id = getattr(obj, obj.primary_key.name)
        if str(obj_id) != f"PrimaryKey:{obj.primary_key.name}" and self.row_exists(obj, obj_id):
            self.update_row(model, obj_id, values)
            for i, cached_obj in enumerate(self._cache[model]):
                if getattr(cached_obj, cached_obj.primary_key.name) == obj_id:
                    self._cache[model][i] = obj
                    break
        else:
            _, last_id = self._insert(model, values)
            setattr(obj, obj.primary_key.name, last_id)

            self.update_cache([obj])

        # Handle ListProperty
        obj_id = getattr(obj, obj.primary_key.name)
        list_properties = [prop for prop in model.properties if isinstance(
            prop, ListProperty)]
        for list_prop in list_properties:
            # Create a new table for the ListProperty
            list_table_name = f"{model.table_name}_{list_prop.name}"
            # Delete old rows
            self._execute_query(
                f"DELETE FROM {list_table_name} WHERE {model.table_name}_id = {obj_id}")
            # Insert the primary key of the object and the primary key of each item in the list into the new table
            for item in getattr(obj, list_prop.name):
                self._execute_query(
                    f"INSERT INTO {list_table_name} ({model.table_name}_id,{list_prop.name}_id)  VALUES ({obj_id}, {getattr(item, item.primary_key.name)})")

    def update_row(self, model, id, values):
        """
        Updates row in table with given id.

        Args:
            model: The model class of the object.
            id: The id of the object.
            values: A dictionary of column names and new values.
        """

        table_name = model.table_name

        # Create a string for the SQL query
        updates = ', '.join(
            [f'{column} = {self._format_value(value)}' for column, value in values.items()])

        query = f'UPDATE {table_name} SET {updates} WHERE id = {id}'
        self._execute_query(query)

    def get_listed_objects_ids(self, object: "ModelMeta", list_property: ListProperty):

        list_table_name = f"{object.table_name}_{list_property.name}"
        query = f"SELECT {list_property.name}_id FROM {list_table_name} WHERE {object.table_name}_id = {getattr(object, object.primary_key.name)}"
        ids = self._execute_query(query)[0]

        return [id[0] for id in ids]

    def _format_value(self, value):
        """Formats a value for use in an SQL query."""
        if isinstance(value, str):
            return f'"{value}"'
        return str(value)

    def delete_model(self, model: type["ModelMeta"]):
        """Deletes model from database.

        Args:
            model: Model to be deleted.
        """
        table_name = model.table_name
        list_properties = [prop for prop in model.properties if isinstance(
            prop, ListProperty)]
        for list_prop in list_properties:
            # Create a new table for the ListProperty
            list_table_name = f"{model.table_name}_{list_prop.name}"
            # Delete table
            self._execute_query(f"DROP TABLE IF EXISTS {list_table_name}")
        self._execute_query(f"DROP TABLE IF EXISTS {table_name}")
        self._cache.pop(model, None)

    def _execute_query(self, query):
        """
        establish a connection with db, execute query and close connection.
        If query gives some results function returns them.
        """
        with self.connection as db:
            results = db.execute_query(query)

        return results

    def _add_new_property(self, property: Property, model: type["ModelMeta"]):
        """
        Adds new property to existing table
        """
        table_name = model.table_name
        property_key = property.name

        if isinstance(property, ListProperty):
            # Create a new table for the many-to-many relationship
            relation_table_name = f"{table_name}_{property_key}"
            self._execute_query(f"DROP TABLE IF EXISTS {relation_table_name}")
            relation_fields = f"\n{table_name}_id INTEGER,\n{property_key}_id INTEGER,"
            relation_query = f"CREATE TABLE IF NOT EXISTS {relation_table_name} ({relation_fields[:-1]}, FOREIGN KEY({table_name}_id) REFERENCES {table_name}(id), FOREIGN KEY({property_key}_id) REFERENCES {property.contained_type.table_name}(id))"
            self._execute_query(relation_query)

        else:
            query = (
                f"ALTER TABLE {table_name} ADD {property_key} {property.get_type_str()}"
            )
            self._execute_query(query)

    def get_rows(self, query):
        return self._execute_query(query)[0]

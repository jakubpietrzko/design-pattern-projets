from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import sqlite3
import os


class Property(ABC):
    def __init__(self, name: Optional[str] = None):
        self.name = name
        self.model = None

    @abstractmethod
    def get_default(self):
        pass

    @abstractmethod
    def get_type_str(self):
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name})"

    def __str__(self):
        return f"{self.__class__.__name__}:{self.name}"

    def assign_owning_model(self, model):
        self.model = model


class IntProperty(Property):
    def get_default(self):
        return 0

    def get_type_str(self):
        return "INTEGER"


class FloatProperty(Property):
    def get_default(self):
        return 0.0

    def get_type_str(self):
        return "REAL"


class PrimaryKey(Property):
    def get_default(self):
        return 0

    def get_type_str(self):
        return "INTEGER PRIMARY KEY AUTOINCREMENT"


class ForeignKey(Property):
    def __init__(
        self, referenced_type: type["ModelMeta"] | str, name: Optional[str] = None
    ):
        super().__init__(name)

        if isinstance(referenced_type, str):
            from src.static_storage import StaticStorage

            self._referenced_type = StaticStorage.get_model_by_name(
                referenced_type)

        else:
            self._referenced_type = referenced_type

    @property
    def referenced_type(self):
        return self._referenced_type

    def get_default(self):
        return None

    def get_type_str(self):
        return f"INTEGER REFERENCES {self._referenced_type.__name__}({self._referenced_type.primary_key.name})"


class ListProperty(Property):
    def __init__(self, contained_type: type['ModelMeta'], name: Optional[str] = None):
        super().__init__(name)
        self._contained_type = contained_type

    @property
    def contained_type(self):
        return self._contained_type

    def get_default(self):
        return []

    def get_type_str(self):
        raise NotImplementedError("ListProperty hasn't got any type string!")


class StringProperty(Property):
    def get_default(self):
        return ""

    def get_type_str(self):
        return "TEXT"

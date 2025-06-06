from typing import List, Dict, Any

import yaml

from src.repository import Repository
from src import properties as properties_m
from src import query_builder
from src import static_storage


class ModelMeta:
    def __init__(self, **kwargs):
        """Initializes model instance and validates passed properties.

        **kwargs: Properties to be assigned to model instance.
        """

        self.__class__._assign_self_to_props()

        self._assign_values(kwargs)

        all_props_names = [prop.name for prop in self.properties]

        unrecognized_props = [
            key for key in kwargs if key not in all_props_names]

        if unrecognized_props:
            raise ValueError(
                f"Invalid properties for class {self.__class__.__name__}:"
                + f" {unrecognized_props}! Available only: {all_props_names}"
            )

    def __repr__(self):

        return yaml.dump(self._get_as_yaml())

    def _get_as_yaml(self):
        props = [prop for prop in self.properties]
        props_defaults = {prop.name: prop.get_default() for prop in props}

        stringified_values = {}

        for prop in props:
            if prop.name in self.__dict__:

                value = self.__dict__[prop.name]

                if isinstance(value, ModelMeta):
                    stringified_values[prop.name] = value.__repr__()

                elif isinstance(value, list):
                    stringified_values[prop.name] = [
                        val._get_as_yaml() if isinstance(val, ModelMeta) else val for val in value
                    ]

                else:
                    stringified_values[prop.name] = value

            else:
                stringified_values[prop.name] = props_defaults[prop.name]

        return {self.__class__.__name__: stringified_values}

    @classmethod
    @property
    def properties(cls) -> List[properties_m.Property]:
        """Returns list of properties of the model."""

        props = {
            name: cls_prop
            for name, cls_prop in cls.__dict__.items()
            if isinstance(cls_prop, properties_m.Property)
        }

        for name, prop in props.items():
            if prop.name is None:
                prop.name = name

        props_list = list(props.values())

        cls_parent = cls.__bases__[0]
        assert len(cls_parent.__bases__) != 0, "You have to create base class for your entity models, that derives from ModelMeta and initializes repository"

        if cls_parent.__bases__[0] != ModelMeta:
            props_list += cls_parent.properties

        for prop in props_list:
            prop.assign_owning_model(cls)

        return props_list

    @classmethod
    @property
    def primary_key(cls) -> properties_m.PrimaryKey:
        """Returns primary key of the model."""

        for prop in cls.properties:
            if isinstance(prop, properties_m.PrimaryKey):
                return prop

    @classmethod
    @property
    def foreign_keys(cls) -> List[properties_m.ForeignKey]:
        """Returns list of foreign keys of the model."""

        return [
            prop for prop in cls.properties if isinstance(prop, properties_m.ForeignKey)
        ]

    @classmethod
    @property
    def list_properties(cls) -> List[properties_m.ListProperty]:
        """Returns list of list properties of the model."""

        return [
            prop for prop in cls.properties if isinstance(prop, properties_m.ListProperty)
        ]

    @classmethod
    @property
    def name(cls) -> str:
        return cls.__name__

    @classmethod
    @property
    def repository(cls) -> Repository:
        def get_base_model(model: type["ModelMeta"]):
            if model.__bases__[0] == ModelMeta:
                return model
            else:
                return get_base_model(model.__bases__[0])

        base_model = get_base_model(cls)

        proxies = {
            getattr(base_model, attr)
            for attr in base_model.__dict__
            if isinstance(getattr(base_model, attr), Repository)
        }

        assert (
            len(proxies) == 1
        ), f"Class '{cls.__name__}' has no repository or has more than one repository!"

        return proxies.pop()

    @classmethod
    def init_class(cls):
        """Initializes class and adds it to static storage."""

        assert\
            len(
                [
                    prop
                    for prop in cls.properties
                    if isinstance(prop, properties_m.PrimaryKey)
                ]
            ) == 1, f"Class '{cls.__name__}' has no primary key or has more than one primary key!"

        static_storage.StaticStorage.add_model(cls)

        cls._assign_self_to_props()

        cls.repository.migrate(cls)

    @classmethod
    def as_table(cls):
        """Returns string representation of the model as table."""

        listed_properties = [
            f"{prop.name} {prop.get_type_str()}" for prop in cls.properties
        ]

        stringified_properties = ",\n  ".join(listed_properties)

        return f"{cls.__name__}\n(\n  {stringified_properties}\n)"

    @classmethod
    @property
    def selection(cls) -> query_builder.QueryBuilder:
        """Returns query builder for selecting objects of the model."""

        return query_builder.QueryBuilder(cls)

    @classmethod
    def _assign_self_to_props(cls):
        for prop in cls.properties:
            prop.assign_owning_model(cls)

    def _assign_values(self, named_props: Dict[str, Any]):
        for prop in self.properties:
            if prop.name in named_props:
                self.__dict__[prop.name] = named_props[prop.name]

    @classmethod
    @property
    def table_name(cls):
        parent = cls.__bases__[0]

        if parent.__bases__[0] == ModelMeta:
            return cls.__name__

        return parent.table_name

    def save(self):
        """Saves model instance to database."""
        self.repository.insert_object(self)

    def delete_object(self):
        """Deletes model instance from database."""
        self.repository.delete_object(self)

    @classmethod
    def delete_model(cls):
        """Deletes model from database."""
        cls.repository.delete_model(cls)

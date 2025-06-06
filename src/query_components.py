from abc import ABC, abstractmethod
from typing import List, Dict

from src import properties


class QueryComponent(ABC):
    """Represents a part of an SQL query."""

    @abstractmethod
    def serialize() -> str:
        """Returns a string representation of the query component."""
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}({self.serialize()})"


class Scalar(QueryComponent):
    """Represents a scalar value in an SQL query."""

    def __init__(
        self, value: properties.Property | int | str | float | bool | List["Scalar"]
    ):
        """Initializes a Scalar instance."""

        self._value = value

    def serialize(self) -> str:
        """Returns a string representation of the scalar."""

        if isinstance(self._value, str):
            return f"'{self._value}'"

        elif isinstance(self._value, properties.Property):
            return f"{self._value.model.table_name}.{self._value.name}"

        elif isinstance(self._value, list):
            return f"({', '.join([v.serialize() for v in self._value])})"

        return str(self._value)


class LogicalOperation(QueryComponent):
    """Represents a logical operation in an SQL query."""

    def __init__(self, left: QueryComponent, right: QueryComponent, operator: str):
        """Initializes a LogicalOperation instance."""

        self._left = left
        self._right = right
        self._operator = operator

    def serialize(self) -> str:
        """Returns a string representation of the logical operation."""

        return (
            f"({self._left.serialize()}) {self._operator} ({self._right.serialize()})"
        )


class ArithmeticOperation(QueryComponent):
    """Represents an arithmetic operation in an SQL query."""

    def __init__(self, left: QueryComponent, right: QueryComponent, operator: str):
        """Initializes an ArithmeticOperation instance."""

        self._left = left
        self._right = right
        self._operator = operator

    def serialize(self) -> str:
        """Returns a string representation of the arithmetic operation."""

        return (
            f"({self._left.serialize()}) {self._operator} ({self._right.serialize()})"
        )


class Limit(QueryComponent):
    """Represents a limit in an SQL query."""

    def __init__(self, limit: int):
        """Initializes a Limit instance."""

        self._limit = limit

    def serialize(self) -> str:
        """Returns a string representation of the limit."""

        return f"LIMIT {self._limit}"


class Comparison(QueryComponent):
    """Represents a comparison between two values."""

    def __init__(self, left: QueryComponent, right: QueryComponent, operator: str):
        """Initializes a Comparison instance."""

        self.left = left
        self.right = right
        self.operator = operator

    def serialize(self) -> str:
        """Returns a string representation of the comparison."""
        return f"{self.left.serialize()} {self.operator} {self.right.serialize()}"


class Query(QueryComponent):
    """Represents an SQL query."""

    def __init__(
        self,
        properties: List[properties.Property],
        condition: QueryComponent | None = None,
        limit: Limit | None = None,
        model: type['ModelMeta'] = None
    ):
        """Initializes a Query instance."""

        unique_props_models = set([prop.model for prop in properties])

        if len(unique_props_models) > 1:
            raise ValueError("All properties must belong to the same model!")

        elif len(unique_props_models) == 0:

            if model is None:
                raise ValueError(
                    "Query must be provided with either a model or a positive number of properties!")

            self._model = model

        else:
            self._model = unique_props_models.pop()

        self._properties = properties

        self._condition = condition
        self._limit = limit

    @property
    def model(self) -> type["ModelMeta"]:
        """Returns the model of the query."""

        return self._model

    @property
    def properties(self) -> List[properties.Property]:
        """Returns the properties of the query."""

        return self._properties

    @property
    def condition(self) -> QueryComponent | None:
        """Returns the condition of the query."""

        return self._condition

    @property
    def limit(self) -> Limit | None:
        """Returns the limit of the query."""

        return self._limit

    def _make_fields_list(self):
        """Creates a list of fields to be selected."""

        listed_fields: List[str] = []

        for prop in self._properties:
            if not isinstance(prop, properties.ForeignKey) and not isinstance(
                prop, properties.ListProperty
            ):
                listed_fields.append(f"{prop.model.table_name}.{prop.name}")

        return listed_fields

    def serialize(self) -> str:
        """Returns a string representation of the query."""

        listed_fields = ", ".join(self._make_fields_list())

        cond = "" if self._condition is None else f"WHERE {self._condition.serialize()}"

        limit = "" if self._limit is None else f"{self._limit.serialize()}"

        from_table = f"FROM {self._model.table_name}"

        return f"SELECT {listed_fields} {from_table} {cond} {limit}"

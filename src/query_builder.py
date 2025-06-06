from typing import List

from src import query_components
from src import properties


class QueryBuilder:
    def __init__(self, model: type["ModelMeta"]):
        self._model = model
        self._condition: query_components.QueryComponent = None
        self._limit: query_components.Limit = None

    def where(self, condition: query_components.QueryComponent):
        if self._condition is not None:
            raise ValueError("Only one WHERE clause is allowed!")

        self._condition = condition

        return self

    def limit(self, limit: int):
        if self._limit is not None:
            raise ValueError("Only one LIMIT clause is allowed!")

        self._limit = query_components.Limit(limit)

        return self

    def evaluate(self):
        primary_objects = self._collect_objects(self._make_query())
        if len(primary_objects):
            self._assign_related_objects(primary_objects)
            return primary_objects

        return []

    def _assign_related_objects(self, primary_objects: List["ModelMeta"]):

        model = primary_objects[0].__class__

        for prop in model.foreign_keys:

            related_model = prop.referenced_type

            related_ids = [
                getattr(getattr(obj, prop.name), getattr(obj, prop.name).primary_key.name) for obj in primary_objects]

            query = query_components.Query([p for p in related_model.properties if not isinstance(
                p, properties.ListProperty)], IsIn(related_model.primary_key, related_ids))

            related_objects = self._collect_objects(query)

            self._assign_related_objects(related_objects)

            for primary_obj, related_obj in zip(primary_objects, related_objects):
                setattr(primary_obj, prop.name, related_obj)

        for prop in model.list_properties:

            for obj in primary_objects:
                related_ids = self._model.repository.get_listed_objects_ids(
                    obj, prop)

                related_model = prop.contained_type

                query = query_components.Query([p for p in related_model.properties if not isinstance(
                    p, properties.ListProperty)], IsIn(related_model.primary_key, related_ids))

                related_objects = self._collect_objects(query)

                self._assign_related_objects(related_objects)

                setattr(obj, prop.name, related_objects)

    def _collect_objects(self, query: query_components.Query):

        ids_collecting_query = query_components.Query(
            [query.model.primary_key], query.condition, query.limit
        )

        ids = query.model.repository.get_rows(
            ids_collecting_query.serialize())
        ids = [id[0] for id in ids]

        objects = query.model.repository.get_objects(query.model, ids)

        ids = [getattr(obj, obj.primary_key.name) for obj in objects]

        modified_condition = NotIn(query.model.primary_key, ids)

        if query.condition is not None:
            modified_condition = And(query.condition, modified_condition)

        props = [prop for prop in query.model.properties if not isinstance(
            prop, properties.ListProperty)]

        remainder_query = query_components.Query(
            props, modified_condition, query.limit
        )

        remainder_rows = query.model.repository.get_rows(
            remainder_query.serialize()
        )

        remainder_objects = [
            query.model(**dict(zip([prop.name for prop in props], row))) for row in remainder_rows
        ]

        query.model.repository.update_cache(remainder_objects)

        return objects + remainder_objects

    def _make_query(self):

        props = [prop for prop in self._model.properties if not isinstance(
            prop, properties.ListProperty)]

        return query_components.Query(
            props, self._condition, self._limit, self._model if not props else None
        )

    def serialize(self):
        return self._make_query().serialize()


def Or(left, right):
    return _logical(left, right, "OR")


def And(left, right):
    return _logical(left, right, "AND")


def Add(left, right):
    return _arithmetic(left, right, "+")


def Subtract(left, right):
    return _arithmetic(left, right, "-")


def Multiply(left, right):
    return _arithmetic(left, right, "*")


def Divide(left, right):
    return _arithmetic(left, right, "/")


def Equals(left, right):
    return _comparison(left, right, "=")


def NotEquals(left, right):
    return _comparison(left, right, "!=")


def GreaterThan(left, right):
    return _comparison(left, right, ">")


def LessThan(left, right):
    return _comparison(left, right, "<")


def IsIn(left, right):
    right = [query_components.Scalar(value) for value in right]
    return _comparison(left, query_components.Scalar(right), "IN")


def NotIn(left, right):
    right = [query_components.Scalar(value) for value in right]
    return _comparison(left, query_components.Scalar(right), "NOT IN")


def _logical(left, right, operator):
    if not isinstance(left, query_components.QueryComponent) or not isinstance(
        right, query_components.QueryComponent
    ):
        raise TypeError(f"Arguments of '{operator}' must be query components!")

    if not isinstance(left, query_components.QueryComponent):
        left = query_components.Scalar(left)

    if not isinstance(right, query_components.QueryComponent):
        right = query_components.Scalar(right)

    return query_components.LogicalOperation(left, right, operator)


def _arithmetic(left, right, operator):
    for arg in (left, right):
        if (
            not isinstance(arg, query_components.QueryComponent)
            and not isinstance(arg, properties.Property)
            and not type(arg) in [int, float]
        ):
            raise TypeError(
                f"Arguments of '{operator}' must be query either query components, properties or numbers!"
            )

    if not isinstance(left, query_components.QueryComponent):
        left = query_components.Scalar(left)

    if not isinstance(right, query_components.QueryComponent):
        right = query_components.Scalar(right)

    return query_components.ArithmeticOperation(left, right, operator)


def _comparison(left, right, operator):
    for arg in (left, right):
        if (
            not isinstance(arg, query_components.QueryComponent)
            and not isinstance(arg, properties.Property)
            and type(arg) not in [int, float, str]
        ):
            raise TypeError(
                f"Arguments of '{operator}' must be query either query components, properties, strings or numbers!"
            )

    if not isinstance(left, query_components.QueryComponent):
        left = query_components.Scalar(left)

    if not isinstance(right, query_components.QueryComponent):
        right = query_components.Scalar(right)

    return query_components.Comparison(left, right, operator)

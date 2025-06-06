from typing import List, Type


class StaticStorage:
    """Class for storing static data."""

    _declared_models: List[Type['ModelMeta']] = []

    @classmethod
    def add_model(cls, model: Type['ModelMeta']):
        """Adds a model to the storage."""

        cls._declared_models.append(model)

    @classmethod
    def get_model_by_name(cls, name: str) -> Type['ModelMeta']:
        """Returns a model by its name."""

        for model in cls._declared_models:
            if model.__name__ == name:
                return model
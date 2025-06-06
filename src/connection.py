import sqlite3
from typing import List, Tuple
from abc import ABC, abstractmethod


class Connection(ABC):
    is_connected: bool
    db_path: str

    def __init__(self, db_path: str) -> None:
        super().__init__()
        self.is_connected = False
        self.db_path = db_path

    @abstractmethod
    def set_connection(self, db_path) -> None:
        self.is_connected = True
        self.db_path = db_path
        ...

    @abstractmethod
    def execute_query(self, query):
        assert self.is_connected, "Database not connected"
        ...

    @abstractmethod
    def close_connection(self) -> None:
        self.is_connected = False
        ...

    def __enter__(self):
        self.set_connection(self.db_path)
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.close_connection()


class SqliteConnection(Connection):
    _connection_adaptee: sqlite3.Connection

    def __init__(self, db_path: str) -> None:
        super().__init__(db_path)

    def set_connection(self, db_path) -> None:
        super().set_connection(db_path)
        self._connection_adaptee = sqlite3.connect(db_path)

    def execute_query(self, query: str) -> Tuple[List, int]:
        super().execute_query(query)
        cursor = self._connection_adaptee.cursor()
        cursor.execute(query)
        results = cursor.fetchall()

        if cursor.lastrowid is None:
            return results

        return results, cursor.lastrowid

    def close_connection(self) -> None:
        super().close_connection()
        self._connection_adaptee.commit()
        self._connection_adaptee.close()

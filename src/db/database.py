from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker


class DataBaseConnector:
    """
    A flexible database connector class to manage connections to different types of databases using SQLAlchemy.

    This class supports connections to PostgreSQL, MySQL, and SQLite databases. It handles the creation of
    the SQLAlchemy engine, session management, and provides utilities for creating database tables.

    Attributes:
        db_type (str): The type of database (e.g., 'postgresql', 'mysql', 'sqlite').
        host (str): The hostname of the database server.
        port (int): The port number on which the database server is listening.
        database (str): The name of the database to connect to.
        user (str): The username for the database connection.
        password (str): The password for the database connection.
        engine (sqlalchemy.engine.base.Engine): The SQLAlchemy engine object.
        Session (sqlalchemy.orm.session.Session): A configured session class for database interactions.
    """

    def __init__(
        self,
        db_type=None,
        host=None,
        port=None,
        database=None,
        user=None,
        password=None,
    ) -> None:
        """
        Initializes the DataBaseConnector with the specified database connection parameters.

        Args:
            db_type (str): The type of database (e.g., 'postgresql', 'mysql', 'sqlite').
            host (str, optional): The hostname of the database server. Required for PostgreSQL and MySQL.
            port (int, optional): The port number on which the database server is listening. Required for PostgreSQL and MySQL.
            database (str, optional): The name of the database to connect to or the path to the SQLite file.
            user (str, optional): The username for the database connection. Required for PostgreSQL and MySQL.
            password (str, optional): The password for the database connection. Required for PostgreSQL and MySQL.

        Raises:
            ValueError: If an unsupported `db_type` is provided.
        """
        self.db_type = db_type
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.engine = self.create_engine()
        self.Session = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

    def create_engine(self):
        """
        Creates and returns a SQLAlchemy engine based on the specified database type and connection parameters.

        Returns:
            sqlalchemy.engine.base.Engine: The SQLAlchemy engine object.

        Raises:
            SQLAlchemyError: If there is an error in creating the engine.
            ValueError: If an unsupported `db_type` is provided.
        """
        try:
            url = self.construct_url()
            engine = create_engine(url, echo=False)
            return engine
        except SQLAlchemyError as error:
            print(f"Failed to create engine: {error}")
            raise error

    def construct_url(self):
        """
        Constructs the database connection URL based on the specified `db_type` and connection parameters.

        Returns:
            str: The constructed database connection URL.

        Raises:
            ValueError: If an unsupported `db_type` is provided.
        """
        if self.db_type == 'postgresql':
            return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type == 'mysql':
            return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type == 'sqlite':
            return f"sqlite:///{self.database}"
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

    def create_session(self):
        """
        Creates and returns a new SQLAlchemy session.

        Returns:
            sqlalchemy.orm.session.Session: A new session object for interacting with the database.
        """
        return self.Session()

    @contextmanager
    def session_scope(self):
        """
        Provides a transactional scope around a series of database operations, ensuring proper session management.

        Yields:
            sqlalchemy.orm.session.Session: A session object for performing database operations.

        Raises:
            SQLAlchemyError: If an error occurs during the transaction, causing a rollback.
        """
        session = self.create_session()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as error:
            session.rollback()
            print(f"Session rollback due to error: {error}")
            raise
        finally:
            session.close()

    def create_tables(self, base):
        """
        Creates all tables defined in the models using the connected database engine.

        Args:
            base (sqlalchemy.ext.declarative.api.DeclarativeMeta): The base class containing the ORM models.

        Raises:
            SQLAlchemyError: If there is an error in creating the tables.
        """
        try:
            base.metadata.create_all(self.engine)
            print("Tables created successfully.")
        except SQLAlchemyError as error:
            print(f"Failed to create tables: {error}")
            raise

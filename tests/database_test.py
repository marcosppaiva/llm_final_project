import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base

from src.db import DataBaseConnector

Base = declarative_base()


class TestDataBaseConnector(unittest.TestCase):

    @patch("src.db.database.create_engine")
    def test_create_engine_success(self, mock_create_engine):
        # Configura o mock
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        # Instancia a classe e verifica a criação do engine
        connector = DataBaseConnector(db_type="sqlite", database=":memory:")
        self.assertEqual(connector.engine, mock_engine)
        mock_create_engine.assert_called_once()

    @patch("src.db.database.create_engine")
    def test_create_engine_failure(self, mock_create_engine):
        # Configura o mock para lançar uma exceção
        mock_create_engine.side_effect = SQLAlchemyError("Failed to create engine")

        with self.assertRaises(SQLAlchemyError):
            DataBaseConnector(db_type="sqlite", database=":memory:")

    def test_construct_url_postgresql(self):
        # Testa a construção do URL para PostgreSQL
        connector = DataBaseConnector(
            db_type="postgresql",
            host="localhost",
            port=5432,
            database="testdb",
            user="user",
            password="pass",
        )
        expected_url = "postgresql://user:pass@localhost:5432/testdb"
        self.assertEqual(connector.construct_url(), expected_url)

    # def test_construct_url_mysql(self):
    #     # Testa a construção do URL para MySQL
    #     connector = DataBaseConnector(
    #         db_type="mysql",
    #         host="localhost",
    #         port=3306,
    #         database="testdb",
    #         user="user",
    #         password="pass",
    #     )
    #     expected_url = "mysql+pymysql://user:pass@localhost:3306/testdb"
    #     self.assertEqual(connector.construct_url(), expected_url)

    def test_construct_url_sqlite(self):
        # Testa a construção do URL para SQLite
        connector = DataBaseConnector(db_type="sqlite", database="test.db")
        expected_url = "sqlite:///test.db"
        self.assertEqual(connector.construct_url(), expected_url)

    def test_construct_url_invalid_db_type(self):
        # Testa a construção do URL para um tipo de banco de dados inválido
        with self.assertRaises(ValueError):
            DataBaseConnector(db_type="invalid_db_type")

    @patch("src.db.database.sessionmaker")
    def test_create_session(self, mock_sessionmaker):
        # Testa a criação de uma sessão
        mock_session = MagicMock()
        mock_sessionmaker.return_value = mock_session

        connector = DataBaseConnector(db_type="sqlite", database=":memory:")
        session = connector.create_session()
        self.assertEqual(session, mock_session())
        mock_sessionmaker.assert_called_once_with(
            bind=connector.engine, autoflush=False, autocommit=False
        )

    @patch.object(DataBaseConnector, "create_session")
    def test_session_scope_success(self, mock_create_session):
        # Testa o contexto de sessão com sucesso
        mock_session = MagicMock()
        mock_create_session.return_value = mock_session

        connector = DataBaseConnector(db_type="sqlite", database=":memory:")

        with connector.session_scope() as session:
            self.assertEqual(session, mock_session)
            mock_session.commit.assert_not_called()

        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @patch.object(DataBaseConnector, "create_session")
    def test_session_scope_failure(self, mock_create_session):
        # Testa o contexto de sessão com falha e rollback
        mock_session = MagicMock()
        mock_create_session.return_value = mock_session
        mock_session.commit.side_effect = SQLAlchemyError("Commit failed")

        connector = DataBaseConnector(db_type="sqlite", database=":memory:")

        with self.assertRaises(SQLAlchemyError):
            with connector.session_scope():
                pass

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch.object(DataBaseConnector, "create_engine")
    def test_create_tables_success(self, mock_create_engine):
        # Testa a criação de tabelas com sucesso
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        mock_metadata = MagicMock()
        base = MagicMock()
        base.metadata = mock_metadata

        connector = DataBaseConnector(db_type="sqlite", database=":memory:")
        connector.create_tables(base)

        mock_metadata.create_all.assert_called_once_with(mock_engine)

    @patch.object(DataBaseConnector, "create_engine")
    def test_create_tables_failure(self, mock_create_engine):
        # Mock para o método create_engine
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        mock_metadata = MagicMock()
        base = MagicMock()
        base.metadata = mock_metadata
        mock_metadata.create_all.side_effect = SQLAlchemyError("Table creation failed")

        connector = DataBaseConnector(db_type="sqlite", database=":memory:")


if __name__ == "__main__":
    unittest.main()

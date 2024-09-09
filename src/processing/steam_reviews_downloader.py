import os
import sys
from typing import Any, Dict, List, Optional
from datetime import timedelta

import requests
from prefect import flow, task
from prefect.tasks import task_input_hash
from sqlalchemy.dialects.postgresql import insert

sys.path.append('src/')

from db import DataBaseConnector
from models import Review


class SteamReviewsDownloader:
    """
    A class to download, filter, and save reviews for games from Steam using Prefect orchestration.

    Attributes:
        app_ids (Dict[str, int]): Mapping of game names to their Steam IDs.
        keys_to_filter (List[str]): Keys to retain in the filtered reviews.
        base_url (str): Base URL for the Steam API, defined by the environment variable `STEAM_API_URL`.
        headers (Dict[str, str]): HTTP request headers.
        db_connector (DataBaseConnector): Database connector for managing database connections.
    """

    def __init__(
        self,
        app_ids: Dict[str, int],
        db_config: Dict[str, Any],
        language: Optional[str] = 'english',
    ) -> None:
        """Initializes an instance of the class.

        Args:
            app_ids (Dict[str, int]): Mapping of game names to their Steam IDs.
            db_config (Dict[str, Any]): Database configuration parameters.

        Raises:
            ValueError: If the environment variable 'STEAM_API_URL' is not set or does not contain '{appid}'.
        """
        self.app_ids = app_ids
        self.language = language
        self.base_url = os.getenv("STEAM_API_URL")
        if self.base_url is None or "{appid}" not in self.base_url:
            raise ValueError(
                "The environment variable 'STEAM_API_URL' must be defined and contain the placeholder '{appid}'"
            )
        self.headers = {"Content-Type": "application/json"}
        self.db_connector = DataBaseConnector(**db_config)

    @task(cache_key_fn=task_input_hash, cache_expiration=timedelta(hours=1))
    def download_reviews(self, app_id: int, language: str) -> List[Any]:
        """Downloads reviews for a given app_id from Steam.

        Args:
            app_id (int): Application ID on Steam.

        Raises:
            ValueError: If the API response is not in the expected format or lacks the 'reviews' key.

        Returns:
            List[Dict[str, Any]]: List of reviews.
        """
        url = self.base_url.format(appid=app_id, language=language)
        response = requests.get(url, headers=self.headers, timeout=20)
        response.raise_for_status()

        data = response.json()
        if not isinstance(data, dict) or "reviews" not in data:
            raise ValueError("API response is in an unexpected format")

        return data.get("reviews", [])

    @task
    def filter_reviews(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filters reviews based on the keys specified in keys_to_filter.

        Args:
            reviews (List[Dict[str, Any]]): List of reviews to be filtered.

        Returns:
            List[Dict[str, Any]]: List of filtered reviews.
        """
        filtered_reviews = []
        for review in reviews:
            if 'author' in review:
                del review['author']
            filtered_reviews.append(review)
        return filtered_reviews

    @task
    def add_game_name(
        self, reviews: List[Dict[str, Any]], game_name: str
    ) -> List[Dict[str, Any]]:
        """Adds the game name to each review.

        Args:
            reviews (List[Dict[str, Any]]): List of reviews.
            game_name (str): Name of the game.

        Returns:
            List[Dict[str, Any]]: List of reviews with game name added.
        """
        for review in reviews:
            review["game"] = game_name
        return reviews

    @task
    def save_reviews_to_db(self, reviews: List[Dict[str, Any]]) -> int:
        """Saves reviews to the database using an efficient PostgreSQL upsert operation.

        Args:
            reviews (List[Dict[str, Any]]): List of reviews to be saved or updated.

        Returns:
            int: Number of reviews successfully saved or updated.
        """
        with self.db_connector.session_scope() as session:
            try:
                stmt = insert(Review).values(reviews)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['recommendationid'],
                    set_={
                        c.key: c for c in stmt.excluded if c.key != 'recommendationid'
                    },
                )
                result = session.execute(stmt)
                saved_count = result.rowcount
                return saved_count
            except Exception as err:
                print(f"Error during bulk upsert: {str(err)}")
                session.rollback()
                return 0

    @flow
    def get_and_save_reviews(self) -> int:
        """Downloads, filters, adds the game name to reviews, and saves them to the database.

        Returns:
            int: Total number of reviews saved to the database.
        """
        total_saved = 0
        for game_name, app_id in self.app_ids.items():
            reviews = self.download_reviews(app_id, self.language)
            filtered_reviews = self.filter_reviews(reviews)
            reviews_with_game = self.add_game_name(filtered_reviews, game_name)
            saved_count = self.save_reviews_to_db(reviews_with_game)
            total_saved += saved_count

        return total_saved


if __name__ == "__main__":
    import json

    from dotenv import load_dotenv

    load_dotenv()
    app_ids = json.loads(os.getenv("APP_IDS"))

    db_config = {
        'db_type': os.getenv("DB_TYPE", "sqlite"),
        'host': os.getenv("DB_HOST", "localhost"),
        'port': os.getenv("DB_PORT"),
        'database': os.getenv("DB_NAME"),
        'user': os.getenv("DB_USER"),
        'password': os.getenv("DB_PASSWORD"),
    }

    downloader = SteamReviewsDownloader(app_ids, db_config)
    total_saved = downloader.get_and_save_reviews()
    print(f"Total reviews saved to the database: {total_saved}")
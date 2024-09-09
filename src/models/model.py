from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import (
    Text,
    Float,
    Column,
    String,
    Boolean,
    Integer,
    DateTime,
    BigInteger,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

tz = ZoneInfo("Europe/Lisbon")

Base = declarative_base()


class Review(Base):
    """_summary_

    Args:
        Base (_type_): _description_

    Returns:
        _type_: _description_
    """

    __tablename__ = 'review'

    recommendationid = Column(String, primary_key=True, index=True)
    game = Column(String, nullable=False)
    playtime_forever = Column(Integer)
    playtime_last_two_weeks = Column(Integer)
    playtime_at_review = Column(Integer)
    last_played = Column(TIMESTAMP)
    language = Column(String, nullable=False)
    review = Column(Text, nullable=False)
    timestamp_created = Column(BigInteger, nullable=False)
    timestamp_updated = Column(BigInteger, nullable=False)
    voted_up = Column(Boolean)
    votes_up = Column(Integer)
    votes_funny = Column(Integer)
    weighted_vote_score = Column(Float)
    comment_count = Column(Integer)
    steam_purchase = Column(Boolean)
    received_for_free = Column(Boolean)
    written_during_early_access = Column(Boolean)
    developer_response = Column(Text)
    timestamp_dev_responded = Column(BigInteger)
    hidden_in_steam_china = Column(Boolean)
    steam_china_location = Column(String)

    created = Column(DateTime, default=datetime.now(tz))
    updated = Column(DateTime, default=datetime.now(tz))

    def __repr__(self):
        return f"<Review(recommendationid={self.recommendationid}, voted_up={self.review})>"


class Conversation(Base):
    """_summary_

    Args:
        Base (_type_): _description_
    """

    __tablename__ = 'conversation'

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Text, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    game = Column(String, nullable=False)
    model = Column(String, nullable=False)
    response_time = Column(Float)
    relevance = Column(Text, nullable=False)
    relevance_explanation = Column(Text, nullable=False)
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)
    eval_prompt_tokens = Column(Integer, nullable=False)
    eval_completion_tokens = Column(Integer, nullable=False)
    eval_total_tokens = Column(Integer, nullable=False)
    model_cost = Column(Float, nullable=False)
    request_time = Column(DateTime, default=datetime.now(tz))

    feedbacks = relationship("FeedBack", back_populates="conversation")


class FeedBack(Base):
    """_summary_

    Args:
        Base (_type_): _description_
    """

    __tablename__ = 'feedback'

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversation.id"))
    feedback_score = Column(Integer)
    feedback_comment = Column(Text)
    feedback_date = Column(DateTime, default=datetime.now(tz))

    conversation = relationship("Conversation", back_populates="feedbacks")

import os
import json
import time
import uuid
import logging
import warnings
from typing import Any, Dict, Union

import streamlit as st
from groq import Groq
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy.exc import SQLAlchemyError, OperationalError, ProgrammingError
from streamlit_feedback import streamlit_feedback

from db import DataBaseConnector, LangChainChromaRAG
from utils import calculate_cost
from models import FeedBack, ModelEnum, Conversation
from processing import QuestionAnswering

warnings.filterwarnings('ignore')
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
COLLECTION_NAME = 'game_reviews'
PROMPT_ASSISTANT_PATH = "prompts/prompt_assistant.j2"
RELEVANCE_EVAL_PATH = "prompts/relevance_eval.j2"


class ChatbotApp:
    def __init__(self):
        self.db_connector = self._get_db_connection()
        self.vector_store = self._load_vector_store()

    @staticmethod
    @st.cache_resource
    def _load_vector_store() -> LangChainChromaRAG:
        """Load and cache the vector store."""
        logger.info("Loading vector store...")
        return LangChainChromaRAG(collection_name=COLLECTION_NAME)

    @staticmethod
    def _get_db_connection() -> DataBaseConnector:
        """Create and return a database connection."""
        logger.info("Establishing database connection...")
        return DataBaseConnector(
            db_type=os.getenv("DB_TYPE", "sqlite"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )

    def _get_model(self, model_name: str) -> Any:
        """Get the appropriate model based on the selected name."""
        models_dict = {
            "ollama": OpenAI(base_url="http://localhost:11434/v1", api_key="ollama"),
            "groq": Groq(),
            "openai": OpenAI(),
        }
        return models_dict.get(model_name.split("/")[0])

    def _submit_feedback(self, user_response: Dict[str, Any], conversation_id: str):
        """Submit user feedback to the database."""
        score = 0 if user_response["score"] == "👎" else 1
        try:
            with self.db_connector.create_session() as session:
                feedback = FeedBack(
                    conversation_id=conversation_id,
                    feedback_score=score,
                    feedback_comment=user_response["text"],
                )
                session.add(feedback)
                session.commit()
            logger.info(f"Feedback submitted for conversation {conversation_id}")
        except SQLAlchemyError as err:
            logger.error(f"Database error while submitting feedback: {str(err)}")
            st.error(
                "An error occurred while submitting your feedback. Please try again later."
            )

    def _process_llm_response(
        self, qa: QuestionAnswering, prompt: str, game: str
    ) -> Union[Conversation, None]:
        """Process the LLM response and store the conversation."""
        start_time = time.time()
        try:
            context = self.vector_store.search(prompt, filter={'game': game})
            logger.info(f"Vector store search results: {context}")
        except Exception as err:
            logger.error(f"Error during vector store search: {str(err)}")
            st.error(
                "An error occurred while searching for relevant information. Please try again."
            )
            return None

        try:
            response = qa.generate_answer(prompt, context)
            answer = response.choices[0].message.content
            evaluating = qa.evaluate_relevance(prompt, answer)

            try:
                relevance = json.loads(evaluating.choices[0].message.content)
            except json.JSONDecodeError:
                relevance = json.loads(
                    evaluating.choices[0]
                    .message.content.replace('```json', '')
                    .replace('```', '')
                )

            model_cost = calculate_cost(
                tokens={
                    'completion_tokens': response.usage.completion_tokens,
                    'prompt_tokens': response.usage.prompt_tokens,
                },
                model=None,
            )

            response_time = time.time() - start_time

            conversation = Conversation(
                conversation_id=st.session_state.conversation_id,
                question=prompt,
                answer=answer,
                game=game,
                model=qa.model_name,
                response_time=response_time,
                relevance=relevance['Relevance'],
                relevance_explanation=relevance['Explanation'],
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                eval_prompt_tokens=evaluating.usage.prompt_tokens,
                eval_completion_tokens=evaluating.usage.completion_tokens,
                eval_total_tokens=evaluating.usage.total_tokens,
                model_cost=model_cost,
            )

            self._save_conversation(conversation)
            return conversation
        except Exception as err:
            logger.error(f"Error during LLM processing: {str(err)}")
            st.error(
                "An error occurred while processing your question. Please try again."
            )
            return None

    def _save_conversation(self, conversation: Conversation):
        """Save the conversation to the database."""
        try:
            with self.db_connector.create_session() as session:
                session.add(conversation)
                session.commit()
                session.refresh(conversation)
            logger.info(f"Conversation saved with ID: {conversation.id}")
        except ProgrammingError as err:
            logger.error(f"Database schema error: {str(err)}")
            st.error(
                "There's an issue with the database schema. Please contact support."
            )
        except OperationalError as err:
            logger.error(f"Database connection error: {str(err)}")
            st.error("Unable to connect to the database. Please try again later.")
        except SQLAlchemyError as err:
            logger.error(f"Database error: {str(err)}")
            st.error(
                "An error occurred while saving your conversation. Please try again."
            )
        except Exception as err:
            logger.error(f"Unexpected error: {str(err)}")
            st.error(
                "An unexpected error occurred. Please try again or contact support."
            )

    def run(self):
        """Run the chatbot application."""
        st.title("🎮 Game Assistant Chatbot")

        model_selected, game_selected = self._setup_sidebar()

        qa = self._setup_qa(model_selected)

        if "conversation_id" not in st.session_state:
            st.session_state.conversation_id = str(uuid.uuid4())
        if "messages" not in st.session_state:
            st.session_state.messages = []

        self._display_chat_history()

        if prompt := st.chat_input("What is up?"):
            self._process_user_input(prompt, qa, game_selected)

    def _setup_expander(self):
        with st.expander("Demo Overviewer", expanded=False):
            st.write(
                """
                This demo aims to use Retrieval-Augmented Generation (RAG) to provide answers based on user reviews from Steam, helping new players clarify doubts about specific games. The chatbot can answer questions such as:

                - What do players say about the gameplay of?
                - Does this game have good reviews for cooperative players?
                - What are the most commonly mentioned negative points about?
                - Is this game recommended for those who enjoy long storylines?"""
            )

    def _setup_sidebar(self) -> tuple[str, str]:
        """Setup the sidebar for model and game selection."""

        with st.sidebar:

            st.subheader(
                "RAG in Steam reviews \n Developed by: [Marcos Paulo](%s)"
                % 'https://www.linkedin.com/in/marcospaulop/'
            )
            self._setup_expander()
            st.divider()

            model_selected = st.selectbox(
                "Select a Model ↓",
                [model_name.value for model_name in ModelEnum],
                disabled=False,
            )
            game_selected = st.selectbox(
                label='Select a Game', options=['cs2', 'dota2', 'black_myth']
            )
        return model_selected, game_selected  # type: ignore

    def _setup_qa(self, model_selected: str) -> QuestionAnswering:
        """Setup the QuestionAnswering object."""
        model_name = model_selected.split("/")[1]
        model = self._get_model(model_selected)
        return QuestionAnswering(
            model,
            PROMPT_ASSISTANT_PATH,
            RELEVANCE_EVAL_PATH,
            model_name,
        )

    def _display_chat_history(self):
        """Display the chat history and feedback buttons."""
        for n, msg in enumerate(st.session_state.messages):
            st.chat_message(msg["role"]).write(msg["content"])
            if msg["role"] == "assistant":
                feedback_key = f"feedback_{n//2}"
                if feedback_key not in st.session_state:
                    st.session_state[feedback_key] = None
                streamlit_feedback(
                    feedback_type="thumbs",
                    optional_text_label="Please provide extra information",
                    on_submit=self._submit_feedback,
                    key=feedback_key,
                    kwargs={"conversation_id": msg["conversation_id"]},
                )

    def _process_user_input(
        self, prompt: str, qa: QuestionAnswering, game_selected: str
    ):
        """Process user input and generate a response."""
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                message_placeholder = st.empty()
                q = self._process_llm_response(qa, prompt, game_selected)
                if q:
                    message_placeholder.markdown(q.answer)
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": q.answer,
                            "conversation_id": q.id,
                        }
                    )
                    streamlit_feedback(
                        feedback_type="thumbs",
                        key=f"feedback_{len(st.session_state.messages)//2}",
                    )
                else:
                    message_placeholder.markdown(
                        "I'm sorry, but I couldn't process your request at this time. Please try again."
                    )


if __name__ == "__main__":
    try:
        app = ChatbotApp()
        app.run()
    except Exception as err:
        logger.critical(f"Critical error in main application: {str(err)}")
        st.error(
            "A critical error occurred. Please try restarting the application or contact support."
        )

from typing import Literal

from pydantic import Field, field_validator

from app.config import settings
from app.schemas import CamelModel
from app.schemas_orders import StrictModel


class TurnIn(StrictModel):
    role: Literal["user", "assistant"]
    text: str

    @field_validator("text")
    @classmethod
    def _text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Write a message.")
        if len(value) > settings.chat_max_message_chars:
            raise ValueError(
                f"Keep each message under {settings.chat_max_message_chars} characters."
            )
        return value


class ChatIn(StrictModel):
    messages: list[TurnIn] = Field(min_length=1)

    @field_validator("messages")
    @classmethod
    def _conversation(cls, turns: list[TurnIn]) -> list[TurnIn]:
        if len(turns) > settings.chat_max_messages:
            raise ValueError("This conversation is too long. Please start a new one.")
        # The widget's greeting comes first, and a conversation must start with the customer.
        while turns and turns[0].role == "assistant":
            turns = turns[1:]
        if not turns or turns[-1].role != "user":
            raise ValueError("The conversation must end with a message from the customer.")
        if sum(len(turn.text) for turn in turns) > settings.chat_max_total_chars:
            raise ValueError("This conversation is too long. Please start a new one.")
        return turns


class ReplyOut(CamelModel):
    text: str
    product_ids: list[str]


class ChatOut(CamelModel):
    reply: ReplyOut

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from src.tools.contacts import get_chat_info_impl
from src.tools.messages import _send_message_or_files, edit_message_impl
from src.utils.message_format import build_message_result


class Channel:
    def __init__(self, *, chat_id: int, title: str, forum: bool):
        self.id = chat_id
        self.title = title
        self.forum = forum
        self.broadcast = True
        self.megagroup = False


@pytest.mark.asyncio
async def test_build_message_result_includes_topic_fields_for_forum_chat():
    entity = Channel(chat_id=123, title="Forum Chat", forum=True)
    message = SimpleNamespace(
        id=10,
        date=datetime.now(UTC),
        text="hello",
        message="hello",
        caption=None,
        reply_to_msg_id=51,
        reply_to=SimpleNamespace(reply_to_top_id=51, forum_topic=True),
        media=None,
    )

    with (
        patch(
            "src.utils.message_format.get_sender_info",
            new=AsyncMock(return_value={"id": 1}),
        ),
        patch(
            "src.utils.message_format._extract_forward_info",
            new=AsyncMock(return_value=None),
        ),
    ):
        result = await build_message_result(None, message, entity, None)

    assert result["topic_id"] == 51


@pytest.mark.asyncio
async def test_build_message_result_topic_fallback_to_message_reply_to_msg_id():
    entity = Channel(chat_id=123, title="Forum Chat", forum=True)
    message = SimpleNamespace(
        id=12,
        date=datetime.now(UTC),
        text="hello",
        message="hello",
        caption=None,
        reply_to_msg_id=42,
        reply_to=SimpleNamespace(
            reply_to_top_id=None, forum_topic=True, reply_to_msg_id=None
        ),
        media=None,
    )

    with (
        patch(
            "src.utils.message_format.get_sender_info",
            new=AsyncMock(return_value={"id": 1}),
        ),
        patch(
            "src.utils.message_format._extract_forward_info",
            new=AsyncMock(return_value=None),
        ),
    ):
        result = await build_message_result(None, message, entity, None)

    assert result["topic_id"] == 42


@pytest.mark.asyncio
async def test_build_message_result_topic_fallback_to_reply_object_reply_to_msg_id():
    entity = Channel(chat_id=123, title="Forum Chat", forum=True)
    message = SimpleNamespace(
        id=13,
        date=datetime.now(UTC),
        text="hello",
        message="hello",
        caption=None,
        reply_to_msg_id=None,
        reply_to=SimpleNamespace(
            reply_to_top_id=None, forum_topic=True, reply_to_msg_id=99
        ),
        media=None,
    )

    with (
        patch(
            "src.utils.message_format.get_sender_info",
            new=AsyncMock(return_value={"id": 1}),
        ),
        patch(
            "src.utils.message_format._extract_forward_info",
            new=AsyncMock(return_value=None),
        ),
    ):
        result = await build_message_result(None, message, entity, None)

    assert result["topic_id"] == 99


@pytest.mark.asyncio
async def test_build_message_result_omits_topic_fields_when_forum_topic_has_no_ids():
    entity = Channel(chat_id=123, title="Forum Chat", forum=True)
    message = SimpleNamespace(
        id=14,
        date=datetime.now(UTC),
        text="hello",
        message="hello",
        caption=None,
        reply_to_msg_id=None,
        reply_to=SimpleNamespace(
            reply_to_top_id=None, forum_topic=True, reply_to_msg_id=None
        ),
        media=None,
    )

    with (
        patch(
            "src.utils.message_format.get_sender_info",
            new=AsyncMock(return_value={"id": 1}),
        ),
        patch(
            "src.utils.message_format._extract_forward_info",
            new=AsyncMock(return_value=None),
        ),
    ):
        result = await build_message_result(None, message, entity, None)

    assert "topic_id" not in result


@pytest.mark.asyncio
async def test_build_message_result_omits_topic_fields_for_non_forum_chat():
    entity = Channel(chat_id=124, title="Regular Channel", forum=False)
    message = SimpleNamespace(
        id=11,
        date=datetime.now(UTC),
        text="hello",
        message="hello",
        caption=None,
        reply_to_msg_id=51,
        reply_to=SimpleNamespace(reply_to_top_id=None, forum_topic=False),
        media=None,
    )

    with (
        patch(
            "src.utils.message_format.get_sender_info",
            new=AsyncMock(return_value={"id": 1}),
        ),
        patch(
            "src.utils.message_format._extract_forward_info",
            new=AsyncMock(return_value=None),
        ),
    ):
        result = await build_message_result(None, message, entity, None)

    assert "topic_id" not in result


@pytest.mark.asyncio
async def test_get_chat_info_returns_topics_for_forum_chat():
    entity = Channel(chat_id=999, title="Forum Chat", forum=True)

    with (
        patch(
            "src.tools.contacts.get_entity_by_id", new=AsyncMock(return_value=entity)
        ),
        patch(
            "src.tools.contacts.build_entity_dict_enriched",
            new=AsyncMock(
                return_value={
                    "id": 999,
                    "title": "Forum Chat",
                    "type": "group",
                    "is_forum": True,
                }
            ),
        ),
        patch(
            "src.tools.contacts._list_forum_topics",
            new=AsyncMock(return_value=[{"topic_id": 7, "title": "Topic 7"}]),
        ) as topics_mock,
    ):
        result = await get_chat_info_impl("999", topics_limit=5)

    assert result["topics"] == [{"topic_id": 7, "title": "Topic 7"}]
    topics_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_chat_info_skips_topics_for_non_forum_chat():
    entity = Channel(chat_id=1000, title="Regular", forum=False)

    with (
        patch(
            "src.tools.contacts.get_entity_by_id", new=AsyncMock(return_value=entity)
        ),
        patch(
            "src.tools.contacts.build_entity_dict_enriched",
            new=AsyncMock(
                return_value={"id": 1000, "title": "Regular", "type": "group"}
            ),
        ),
        patch(
            "src.tools.contacts._list_forum_topics",
            new=AsyncMock(side_effect=RuntimeError("must not call")),
        ),
    ):
        result = await get_chat_info_impl("1000", topics_limit=5)

    assert "topics" not in result


@pytest.mark.asyncio
async def test_send_message_or_files_uses_topic_id_as_reply_target():
    client = AsyncMock()
    client.send_message = AsyncMock(return_value=SimpleNamespace(id=1))
    entity = SimpleNamespace(id=1)

    error, _ = await _send_message_or_files(
        client=client,
        entity=entity,
        message="hello",
        files=None,
        reply_to_msg_id=None,
        topic_id=77,
        parse_mode=None,
        operation="send_message",
        params={},
    )

    assert error is None
    assert client.send_message.await_args.kwargs["reply_to"] == 77


@pytest.mark.asyncio
async def test_send_message_or_files_prefers_reply_to_over_topic_id():
    client = AsyncMock()
    client.send_message = AsyncMock(return_value=SimpleNamespace(id=1))
    entity = SimpleNamespace(id=1)

    error, _ = await _send_message_or_files(
        client=client,
        entity=entity,
        message="hello",
        files=None,
        reply_to_msg_id=123,
        topic_id=77,
        parse_mode=None,
        operation="send_message",
        params={},
    )

    assert error is None
    assert client.send_message.await_args.kwargs["reply_to"] == 123


@pytest.mark.asyncio
async def test_edit_message_in_forum_includes_topic_id_only():
    client = AsyncMock()
    chat = SimpleNamespace(
        id=1, title="Forum Chat", forum=True, broadcast=True, megagroup=False
    )

    edited_message = SimpleNamespace(
        id=123,
        date=datetime.now(UTC),
        edit_date=datetime.now(UTC),
        text="updated",
        sender=None,
        reply_to_msg_id=51,
        reply_to=SimpleNamespace(reply_to_top_id=51, forum_topic=True),
    )

    client.edit_message = AsyncMock(return_value=edited_message)

    with (
        patch(
            "src.tools.messages.get_connected_client",
            new=AsyncMock(return_value=client),
        ),
        patch("src.tools.messages.get_entity_by_id", new=AsyncMock(return_value=chat)),
    ):
        result = await edit_message_impl(
            chat_id="-1001",
            message_id=123,
            new_text="updated",
            parse_mode=None,
        )

    assert result["status"] == "edited"
    assert result["topic_id"] == 51
    assert "top_msg_id" not in result
    client.edit_message.assert_awaited_once()

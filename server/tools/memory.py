import json
from typing import Any

from agents import function_tool
from agents.run_context import RunContextWrapper

from server.auth.tenant_context import set_tenant_id
from server.db.session import get_async_session
from server.repositories.settings import SettingRepository
from server.utils.custom_logger import get_logger

logger = get_logger(__name__)

INSTRUCTIONS_WORD_LIMIT = 2000
WORKSPACE_INSTRUCTIONS_KEY = "workspace_instructions"


def _count_words(text: str) -> int:
    return len(text.split())


async def _read_existing_instructions(tenant_id: str) -> str | None:
    async for session in get_async_session():
        set_tenant_id(tenant_id)
        repo = SettingRepository(session)
        setting = await repo.get_by_key(WORKSPACE_INSTRUCTIONS_KEY)
        return setting.setting_value if setting and setting.setting_value else None
    return None


async def _save_instructions(tenant_id: str, content: str) -> None:
    async for session in get_async_session():
        set_tenant_id(tenant_id)
        repo = SettingRepository(session)
        await repo.upsert_setting(WORKSPACE_INSTRUCTIONS_KEY, content)


@function_tool
async def add_instruction(
    ctx: RunContextWrapper[Any],
    instruction: str,
) -> str:
    """
    Append a new instruction to the workspace instructions. The instruction is added
    as a bullet point — existing content is automatically preserved.

    Use this to save user preferences and standing instructions:
    - Preferences about data, chart styles, naming conventions
    - Recurring corrections the team requested
    - Standing instructions about how to present data

    Do NOT use this for data patterns, schema notes, or query fixes — use add_learning for those.

    Keep each instruction concise. The total must stay under 2000 words.

    Args:
        ctx: Run context wrapper
        instruction: The instruction to append (will be saved as a bullet point)

    Returns:
        JSON confirmation with current word count.
    """
    tenant_id = ctx.context.get("tenant_id")
    if not tenant_id:
        return json.dumps({"success": False, "error": "No tenant_id in context"})

    instruction = instruction.strip()
    if not instruction:
        return json.dumps({"success": False, "error": "Instruction cannot be empty"})

    try:
        existing = await _read_existing_instructions(tenant_id)
        new_line = f"- {instruction}"
        combined = f"{existing}\n{new_line}" if existing else new_line

        word_count = _count_words(combined)
        if word_count > INSTRUCTIONS_WORD_LIMIT:
            current_count = _count_words(existing) if existing else 0
            return json.dumps(
                {
                    "success": False,
                    "error": f"Adding this instruction would exceed the {INSTRUCTIONS_WORD_LIMIT} word limit. "
                    f"Current: {current_count} words, remaining capacity: {INSTRUCTIONS_WORD_LIMIT - current_count} words. "
                    "Remove old instructions first or shorten the new one.",
                }
            )

        await _save_instructions(tenant_id, combined)
        logger.info(f"Appended instruction for tenant {tenant_id} ({word_count} words total)")
        return json.dumps(
            {
                "success": True,
                "message": "Instruction added successfully",
                "word_count": word_count,
                "capacity_remaining": INSTRUCTIONS_WORD_LIMIT - word_count,
            }
        )
    except Exception as e:
        logger.error(f"Error adding instruction: {e}")
        return json.dumps({"success": False, "error": str(e)})


@function_tool
async def remove_instruction(
    ctx: RunContextWrapper[Any],
    instruction_to_remove: str,
) -> str:
    """
    Remove an instruction from the workspace instructions. Finds and removes lines
    containing the given text (case-insensitive substring match).

    Use this when the user asks to forget, undo, or remove a previously saved preference
    or instruction.

    Args:
        ctx: Run context wrapper
        instruction_to_remove: Text to search for in existing instructions (case-insensitive)

    Returns:
        JSON confirmation with what was removed, or available instructions if no match found.
    """
    tenant_id = ctx.context.get("tenant_id")
    if not tenant_id:
        return json.dumps({"success": False, "error": "No tenant_id in context"})

    instruction_to_remove = instruction_to_remove.strip()
    if not instruction_to_remove:
        return json.dumps({"success": False, "error": "instruction_to_remove cannot be empty"})

    try:
        existing = await _read_existing_instructions(tenant_id)
        if not existing:
            return json.dumps({"success": False, "error": "No instructions found"})

        lines = existing.split("\n")
        search_lower = instruction_to_remove.lower()
        removed = []
        kept = []

        for line in lines:
            if search_lower in line.lower() and line.strip():
                removed.append(line.strip())
            else:
                kept.append(line)

        if not removed:
            available = [line.strip() for line in lines if line.strip()]
            return json.dumps(
                {
                    "success": False,
                    "error": f'No instruction matching "{instruction_to_remove}" found',
                    "available_instructions": available,
                }
            )

        updated = "\n".join(kept).strip()
        await _save_instructions(tenant_id, updated)
        logger.info(f"Removed {len(removed)} instruction(s) for tenant {tenant_id}")
        return json.dumps(
            {
                "success": True,
                "message": f"Removed {len(removed)} instruction(s)",
                "removed": removed,
                "word_count": _count_words(updated) if updated else 0,
            }
        )
    except Exception as e:
        logger.error(f"Error removing instruction: {e}")
        return json.dumps({"success": False, "error": str(e)})


@function_tool
async def search_instructions(
    ctx: RunContextWrapper[Any],
    query: str,
) -> str:
    """
    Search workspace instructions for sections matching a keyword query.
    Use this in long conversations where context may have been compacted and you need
    to retrieve specific preferences or instructions you previously saved.

    Returns trimmed context snippets around each match, not the full content.

    Args:
        ctx: Run context wrapper
        query: Space-separated keywords to search for in the instructions

    Returns:
        JSON with matching snippets from the workspace instructions.
    """
    tenant_id = ctx.context.get("tenant_id")

    if not tenant_id:
        return json.dumps({"success": False, "error": "No tenant_id in context"})

    if not query or not query.strip():
        return json.dumps({"success": False, "error": "Query cannot be empty"})

    try:
        async for session in get_async_session():
            set_tenant_id(tenant_id)
            repo = SettingRepository(session)
            result = await repo.search_by_key_content(WORKSPACE_INSTRUCTIONS_KEY, query)

            if result is None:
                return json.dumps(
                    {"success": True, "snippets": [], "match_count": 0, "message": "No matching instructions found"}
                )

            return json.dumps(
                {
                    "success": True,
                    "snippets": result["snippets"],
                    "match_count": len(result["snippets"]),
                    "content_length": result["content_length"],
                }
            )

        return json.dumps({"success": False, "error": "Failed to obtain database session"})
    except Exception as e:
        logger.error(f"Error searching instructions: {e}")
        return json.dumps({"success": False, "error": str(e)})


def get_instruction_tools():
    return [add_instruction, remove_instruction, search_instructions]

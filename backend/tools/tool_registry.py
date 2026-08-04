"""
Claude tool_use API definitions and dispatcher for the MAX EV Analyst agent.

Usage:
    from tools.tool_registry import TOOLS, execute_tool

    # Pass TOOLS to client.messages.create(tools=TOOLS)
    # On tool_use response, call execute_tool(name, input_dict)
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── Tool definitions for Claude tool_use API ────────────────────────────────

TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_injury_report",
        "description": (
            "Fetch current player injury designations for a team. "
            "Returns player names, injury statuses (Out/Doubtful/Questionable/Probable), "
            "and injury types. Call this when the user asks about injuries, availability, "
            "or lineup health for a specific team."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "team_name": {
                    "type": "string",
                    "description": "Full or partial team name, e.g. 'Boston Celtics' or 'Celtics'.",
                },
                "sport": {
                    "type": "string",
                    "enum": ["nba", "nfl", "mlb", "nhl", "ncaaf", "ncaab", "wnba"],
                    "description": "Platform sport key.",
                },
            },
            "required": ["team_name", "sport"],
        },
    },
    {
        "name": "get_starting_lineup",
        "description": (
            "Get confirmed starters for a team. "
            "Critical for NBA (load management decisions) and MLB (starting pitcher). "
            "Call this when the user asks who is starting, who is sitting out, "
            "or whether key players are confirmed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "team_name": {
                    "type": "string",
                    "description": "Full or partial team name.",
                },
                "sport": {
                    "type": "string",
                    "enum": ["nba", "nfl", "mlb", "nhl", "ncaaf", "ncaab", "wnba"],
                    "description": "Platform sport key.",
                },
                "game_date": {
                    "type": "string",
                    "description": "Optional ISO date (YYYY-MM-DD) to scope to a specific day.",
                },
            },
            "required": ["team_name", "sport"],
        },
    },
    {
        "name": "get_weather",
        "description": (
            "Fetch game-day weather forecast for an outdoor stadium. "
            "Relevant for NFL and MLB outdoor venues — wind, temperature, and rain "
            "all affect totals. Call this when analyzing outdoor NFL or MLB games "
            "or when the user asks about weather impact. "
            "Returns is_dome=true for indoor/dome stadiums (weather irrelevant)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "home_team": {
                    "type": "string",
                    "description": "Home team name (used to look up stadium location).",
                },
                "game_date": {
                    "type": "string",
                    "description": "ISO date string (YYYY-MM-DD).",
                },
            },
            "required": ["home_team", "game_date"],
        },
    },
    {
        "name": "get_news",
        "description": (
            "Fetch recent news headlines and beat reporter updates for one or both teams "
            "in a matchup. Returns articles from the last 24 hours by default. "
            "Use this when the user asks about breaking news, recent developments, "
            "or when context suggests something important may have happened recently."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "teams": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of team names to filter headlines for.",
                },
                "sport": {
                    "type": "string",
                    "enum": ["nba", "nfl", "mlb", "nhl", "ncaaf", "ncaab", "wnba", "mma", "tennis"],
                    "description": "Platform sport key.",
                },
                "hours": {
                    "type": "integer",
                    "default": 24,
                    "description": "Only return articles from the last N hours.",
                },
            },
            "required": ["teams", "sport"],
        },
    },
    {
        "name": "get_game_script",
        "description": (
            "Generate a full handicapper-style game analysis for a specific matchup. "
            "Returns a 400-700 word write-up covering line movement, power ratings, "
            "ATS trends, head-to-head history, key injuries, and injury cascade "
            "opportunities (when books overreact to player news). "
            "Call this when the user asks you to 'break down', 'analyze', 'give me a "
            "write-up on', or 'handicap' a specific game. Always prefer this tool over "
            "a generic response when a matchup is mentioned."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sport": {
                    "type": "string",
                    "enum": ["nba", "nfl", "mlb", "nhl", "ncaaf", "ncaab", "wnba"],
                    "description": "Platform sport key.",
                },
                "home_team": {
                    "type": "string",
                    "description": "Home team name or partial name, e.g. 'Chiefs' or 'Kansas City Chiefs'.",
                },
                "away_team": {
                    "type": "string",
                    "description": "Away team name or partial name, e.g. 'Eagles' or 'Philadelphia Eagles'.",
                },
                "game_id": {
                    "type": "string",
                    "description": "Optional platform game_id for exact match lookup.",
                },
            },
            "required": ["sport", "home_team", "away_team"],
        },
    },
]


def execute_tool(name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    """
    Dispatch a tool call by name and return the result.

    Args:
        name: Tool name matching one of the TOOLS definitions.
        tool_input: Arguments dict as provided by the Claude tool_use response.

    Returns:
        Tool result dict. Returns an error dict on any dispatch or execution error.
    """
    try:
        if name == "get_injury_report":
            from tools.injury_tool import get_injury_report
            return get_injury_report(
                team_name=tool_input["team_name"],
                sport=tool_input["sport"],
            )

        if name == "get_starting_lineup":
            from tools.lineup_tool import get_starting_lineup
            return get_starting_lineup(
                team_name=tool_input["team_name"],
                sport=tool_input["sport"],
                game_date=tool_input.get("game_date"),
            )

        if name == "get_weather":
            from tools.weather_tool import get_weather
            return get_weather(
                home_team=tool_input["home_team"],
                game_date=tool_input["game_date"],
            )

        if name == "get_news":
            from tools.news_tool import get_news
            return get_news(
                teams=tool_input["teams"],
                sport=tool_input["sport"],
                hours=tool_input.get("hours", 24),
            )

        if name == "get_game_script":
            from tools.game_script_tool import build_game_script
            return build_game_script(
                sport=tool_input["sport"],
                home_team=tool_input["home_team"],
                away_team=tool_input["away_team"],
                game_id=tool_input.get("game_id"),
            )

        logger.warning("execute_tool: unknown tool %r", name)
        return {"error": f"Unknown tool: {name}"}

    except KeyError as exc:
        logger.error("execute_tool missing required param for %r: %s", name, exc)
        return {"error": f"Missing required parameter: {exc}"}
    except Exception as exc:
        logger.error("execute_tool error executing %r: %s", name, exc)
        return {"error": str(exc)}

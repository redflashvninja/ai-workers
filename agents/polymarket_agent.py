import anthropic
from agents.base import BaseAgent
import integrations.polymarket as pm


SYSTEM = """You are a Polymarket prediction-markets analyst with real-time access to market data.

Your capabilities:
- Search and browse active prediction markets
- Show current Yes/No prices (which equal implied probabilities)
- Track trending markets by volume
- Read order books for liquidity analysis
- Monitor price history

Guidelines:
- A Yes price of 0.72 means the market implies a 72% probability of YES.
- Highlight unusual price movements or high-volume markets.
- Always cite the market URL so the user can trade.
- Be objective — report what the market says, not your own opinion.
- Format prices as percentages (0.72 → 72%).
- Today's date is 2026-05-14."""


class PolymarketAgent(BaseAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(client, SYSTEM)
        self._register_all()

    def _register_all(self):
        self._register_tool(
            "search_markets",
            "Search Polymarket prediction markets by keyword. Returns active markets matching the query.",
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keywords, e.g. 'election', 'bitcoin', 'AI'"},
                    "limit": {"type": "integer", "default": 20},
                    "active": {"type": "boolean", "default": True},
                },
                "required": ["query"],
            },
            lambda query, limit=20, active=True: pm.search_markets(query, limit, active),
        )

        self._register_tool(
            "get_market",
            "Get full details of a specific Polymarket market by its condition ID.",
            {
                "type": "object",
                "properties": {
                    "condition_id": {"type": "string", "description": "The market's condition ID"},
                },
                "required": ["condition_id"],
            },
            lambda condition_id: pm.get_market(condition_id),
        )

        self._register_tool(
            "get_trending_markets",
            "Get the top trending Polymarket markets ranked by 24-hour trading volume.",
            {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10, "description": "How many markets to return"},
                },
            },
            lambda limit=10: pm.get_trending_markets(limit),
        )

        self._register_tool(
            "get_market_orderbook",
            "Get the live order book (bids and asks) for a market token to assess liquidity.",
            {
                "type": "object",
                "properties": {
                    "token_id": {"type": "string", "description": "The token ID (Yes or No side)"},
                },
                "required": ["token_id"],
            },
            lambda token_id: pm.get_market_orderbook(token_id),
        )

        self._register_tool(
            "get_price_history",
            "Get the price history for a market to see how sentiment has moved over time.",
            {
                "type": "object",
                "properties": {
                    "condition_id": {"type": "string"},
                    "interval": {
                        "type": "string",
                        "enum": ["1h", "6h", "1d", "1w", "1m", "all"],
                        "default": "1d",
                    },
                },
                "required": ["condition_id"],
            },
            lambda condition_id, interval="1d": pm.get_market_price_history(condition_id, interval),
        )

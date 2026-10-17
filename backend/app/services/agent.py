import json

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.llm import client
from app.services.orders import get_order_status
from app.services.shop import search_products
from app.services.tickets import create_ticket

MAX_TOOL_ROUNDS = 4

SYSTEM_PROMPT = (
    "You are a friendly customer support assistant for an online electronics store "
    "that sells TVs, refrigerators and air conditioners. Prices are in BDT (taka). "
    "Reply briefly and clearly in the same language as the customer. "
    "If the customer writes in Bangla, including Bangla typed in English letters, reply in Bangla script. "
    "Write in plain text only. Do not use markdown, tables, bold or headings. "
    "Use the search_products tool for any question about products, prices, brands or stock. "
    "When listing products, use one line per product: the product name, then the price in taka, "
    "then whether it is in stock. Write the words around the product names in the customer's language. "
    "Use the get_order_status tool only when the customer has given BOTH an order number "
    "and the email used for the order; otherwise ask for the missing detail. "
    "When reporting an order, always include the order status, the product names with quantities, "
    "the tracking number if there is one, and the total price in taka. "
    "For questions about policies such as returns, shipping or warranty, use the provided "
    "document context. State only what the context says. "
    "Never invent products, prices, order details or policies. "
    "Do not add conditions, reasons, exceptions, time limits or promises that are not written in the context. "
    "Call the request_human_handoff tool when the customer asks for a human agent, "
    "when the customer reports a damaged or faulty product or a complaint, "
    "or when you cannot answer from the tools or the context. "
    "Give a short English reason that summarises the problem, then tell the customer "
    "that a human support agent will contact them. "
    "Do not call it for questions you can answer yourself."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search the product catalog. Use for questions about products, prices, brands and availability.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Free-text keywords, e.g. 'inverter' or 'smart'"},
                    "category": {"type": "string", "enum": ["TV", "Refrigerator", "AC"]},
                    "brand": {"type": "string"},
                    "min_price": {"type": "number", "description": "Minimum price in BDT"},
                    "max_price": {"type": "number", "description": "Maximum price in BDT"},
                    "in_stock_only": {"type": "boolean"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Look up an order. Requires both the order number and the customer's email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer", "description": "The order number"},
                    "email": {"type": "string", "description": "Email used when placing the order"},
                },
                "required": ["order_id", "email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "request_human_handoff",
            "description": (
                "Create a support ticket so a human agent contacts the customer. "
                "Use when the customer asks for a human, reports a complaint or damaged product, "
                "or when the question cannot be answered."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "A short English summary of the customer's problem",
                    },
                },
                "required": ["reason"],
            },
        },
    },
]


def run_tool(db: Session, user_id: int, name: str, arguments: dict) -> dict:
    try:
        if name == "search_products":
            return {"products": search_products(db, **arguments)}
        if name == "get_order_status":
            return get_order_status(db, **arguments)
        if name == "request_human_handoff":
            return create_ticket(db, user_id, **arguments)
        return {"error": f"Unknown tool: {name}"}
    except Exception as e:
        print(f"Tool error in {name}: {e}")
        return {"error": "The tool failed. Please try again."}


def generate_reply_with_tools(
    db: Session, user_id: int, history: list[dict], user_turn: str
) -> str:
    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + history
        + [{"role": "user", "content": user_turn}]
    )

    for _ in range(MAX_TOOL_ROUNDS):
        completion = client.chat.completions.create(
            messages=messages,
            model=settings.llm_model,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.3,
            max_tokens=1024,
        )
        message = completion.choices[0].message

        # No tool requested: this is the final answer
        if not message.tool_calls:
            return message.content or ""

        # Keep the assistant's tool request in the conversation
        messages.append(
            {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in message.tool_calls
                ],
            }
        )

        # Run each requested tool and send the result back
        for call in message.tool_calls:
            try:
                arguments = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}
            result = run_tool(db, user_id, call.function.name, arguments)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    return "Sorry, I could not complete that request. Please try again or ask for a human agent."
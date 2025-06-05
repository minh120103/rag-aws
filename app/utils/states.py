from typing_extensions import TypedDict, Annotated
from typing import Literal, Sequence, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# Type Definitions
class State(TypedDict):
    # Message history with proper accumulation
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Thread identification for caching
    thread_id: Optional[str]
    
    # Current processing state
    route: Optional[Literal["sql", "vector", "general"]]
    query: Optional[str]
    result: Optional[str]
    answer: Optional[str]

class QueryOutput(TypedDict):
    """Generated SQL query."""
    query: Annotated[str, ..., "Syntactically valid SQL query."]



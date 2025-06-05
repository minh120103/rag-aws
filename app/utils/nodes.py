from .states import QueryOutput, State
from ..factories.models import llm, db, vectorstore
from .prompts import router_prompt, sql_prompt, vectordb_prompt
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage 
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langgraph.graph import START, StateGraph, END
from ..services.memory_service import memory_service
import logging

logger = logging.getLogger(__name__)



def router(state: State):
    """Route the conversation based on the latest user message."""
    print("Routing decision...")
    messages = state["messages"]
    
    # Get the latest user message
    latest_message = messages[-1].content if messages else ""
    
    recent_messages = messages[-8:] if len(messages) > 8 else messages

    response = llm.invoke(router_prompt.format(question=latest_message, context=recent_messages))
    answer = response.content.strip().lower()
    print(f"Router Decision (LLM): {answer}")

    if "sql" in answer:
        return {"route": "sql"}
    elif "vector" in answer:
        return {"route": "vector"}
    else:
        return {"route": "general"}

def write_query(state: State):
    """Generate SQL query to fetch information with context awareness."""
    messages = state["messages"]
    
    # Get the latest user message for the query
    latest_message = messages[-1].content if messages else ""
    
    # Build context from recent conversation
    context_messages = []
    for msg in messages[-8:]:  # Last 3 exchanges (6 messages)
        if isinstance(msg, (HumanMessage, AIMessage)):
            context_messages.append(f"{msg.__class__.__name__}: {msg.content}")
    
    context_str = "\n".join(context_messages) if context_messages else latest_message
        
    prompt = sql_prompt.format(
        dialect=db.dialect,
        top_k=10,
        table_info=db.get_context(),
        input=context_str,
    )    
    structured_llm = llm.with_structured_output(QueryOutput)
    result = structured_llm.invoke(prompt)
    return {"query": result["query"]}

def execute_query(state: State):
    """Execute SQL query."""
    query = state["query"]
    
    # Execute query - Redis cache will handle LLM response caching automatically
    execute_query_tool = QuerySQLDatabaseTool(db=db)
    result = execute_query_tool.invoke(query)
    
    return {"result": result}

def generate_sql_answer(state: State):
    """Generate SQL answer with conversation context."""
    messages = state["messages"]
    latest_message = messages[-1].content if messages else ""
    thread_id = state.get("thread_id", "")
    
    # Get recent conversation context
    recent_messages = messages[-6:] if len(messages) > 6 else messages
    
    # Build context
    context_messages = [
        SystemMessage(content="You are an AI assistant. Answer based on the SQL query and result.")
    ]
    context_messages.extend(recent_messages)
    
    # Add current task
    current_task = f"""
    Question: {latest_message}
    SQL Query: {state['query']}
    Result: {state['result']}
    
    Please provide a clear answer based on this information.
    """
    context_messages.append(HumanMessage(content=current_task))
    
    response = llm.invoke(context_messages)
    
    # Save to memory
    memory_service.save_conversation(thread_id, latest_message, response.content, "sql")
    
    return {
        "answer": response.content,
        "messages": [AIMessage(content=response.content)]
    }

def generate_vector_answer(state: State):
    """Generate vector answer with chat history context."""
    messages = state["messages"]
    latest_message = messages[-1].content if messages else ""
    thread_id = state.get("thread_id", "")
    
    # Get chat history for context
    chat_history = messages[-6:] if len(messages) > 6 else messages

    # Perform vector search - LLM responses automatically cached by Redis
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 10,
            "fetch_k": 20,
            "lambda_mult": 0.7,
        }
    )

    docs = vectorstore.similarity_search(latest_message, k=20)
    
    bm25_retriever = BM25Retriever.from_documents(docs)
    bm25_retriever.k = 10 
    
    hybrid_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, retriever],
        weights=[0.3, 0.7]  
    )

    rag_prompt = ChatPromptTemplate.from_messages([
        ("system", vectordb_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])

    question_answer_chain = create_stuff_documents_chain(llm, rag_prompt)
    rag_chain = create_retrieval_chain(hybrid_retriever, question_answer_chain)
    
    result = rag_chain.invoke({
        "input": latest_message,
        "chat_history": chat_history
    })
    
    answer = result["answer"]
    memory_service.save_conversation(thread_id, latest_message, answer, "vector")
    
    return {
        "answer": answer,
        "messages": [AIMessage(content=answer)]
    }

def generate_general_answer(state: State):
    """Generate general answer with conversation context."""
    messages = state["messages"]
    latest_message = messages[-1].content if messages else ""
    thread_id = state.get("thread_id", "")
    
    # Get conversation context
    recent_messages = messages[-8:] if len(messages) > 8 else messages
    
    context_messages = [
        SystemMessage(content="""You are a helpful assistant. Answer based on conversation history.
        
        Guidelines:
        - For movie-related questions, say you don't know the answer.
        - For general questions, provide helpful responses.
        - Use conversation history for context.""")
    ]
    context_messages.extend(recent_messages)
    context_messages.append(HumanMessage(content=latest_message))
    
    response = llm.invoke(context_messages)
    memory_service.save_conversation(thread_id, latest_message, response.content, "general")
    
    return {
        "answer": response.content,
        "messages": [AIMessage(content=response.content)]
    }

# Graph Builder Function
def build_graph():
    """Build and return the compiled graph."""
    graph_builder = StateGraph(State)
    
    # Add nodes
    graph_builder.add_node("router", router)
    graph_builder.add_node("write_query", write_query)
    graph_builder.add_node("execute_query", execute_query)
    graph_builder.add_node("generate_sql_answer", generate_sql_answer)
    graph_builder.add_node("generate_vector_answer", generate_vector_answer)
    graph_builder.add_node("generate_general_answer", generate_general_answer)
    
    # Add edges
    graph_builder.add_edge(START, "router")
    graph_builder.add_conditional_edges(
        "router",
        lambda x: x["route"],
        {
            "sql": "write_query",
            "vector": "generate_vector_answer",
            "general": "generate_general_answer"
        }
    )
    graph_builder.add_edge("write_query", "execute_query")
    graph_builder.add_edge("execute_query", "generate_sql_answer")
    
    # End edges
    graph_builder.add_edge("generate_sql_answer", END)
    graph_builder.add_edge("generate_vector_answer", END)
    graph_builder.add_edge("generate_general_answer", END)
    
    return graph_builder

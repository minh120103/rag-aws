from .resources import QueryOutput, State, llm, db, vectorstore
from .prompts import router_prompt, sql_prompt, vectordb_prompt
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage 
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langgraph.graph import START, StateGraph, END


def get_last_n_conversations(questions, answers, n=7):
    """Helper function to get last n conversations (Q&A pairs)"""
    if not questions or not answers:
        return [], []
    
    # Get the minimum length to avoid index errors
    min_len = min(len(questions), len(answers))
    
    # If we have fewer than n conversations, return all
    if min_len <= n:
        return list(questions[:min_len]), list(answers[:min_len])
    
    # Return last n conversations
    return list(questions[-n:]), list(answers[-n:])

def router(state: State):
    question = state["question"]    
    answer = state["answer"]

    # Only use last 7 conversations for context
    last_questions, last_answers = get_last_n_conversations(question, answer, 7)
    
    response = llm.invoke(router_prompt.format(
        question=last_questions[-1] if last_questions else question, 
        questions=last_questions, 
        answer=last_answers
    ))
    answer = response.content.strip().lower()
    print(f"Router Decision (LLM): {answer}")
    # print(question)

    if "sql" in answer:
        return {"route": "sql"}
    elif "vector" in answer:
        return {"route": "vector"}
    else:
        return {"route": "general"}

def write_query(state: State):
    """Generate SQL query to fetch information with context awareness."""
    # Get only last 5 conversations for context
    messages = state["question"]
    answer = state["answer"]
    
    last_questions, last_answers = get_last_n_conversations(messages, answer, 5)
    
    prompt = sql_prompt.format(
        dialect=db.dialect,
        top_k=10,
        table_info=db.get_table_info(),
        answer=last_answers,
        input=last_questions,
    )    
    structured_llm = llm.with_structured_output(QueryOutput)
    result = structured_llm.invoke(prompt)
    return {"query": result["query"]}

def execute_query(state: State):
    """Execute SQL query."""
    execute_query_tool = QuerySQLDatabaseTool(db=db)
    return {"result": execute_query_tool.invoke(state["query"])}

def generate_sql_answer(state: State):
    """Answer question using retrieved information with previous context (last 5 only)."""
    # Get current question
    messages = state["question"]
    current_question = messages[-1].content if messages else ""
    
    # Build context from last 5 Q&A pairs only
    context_messages = []
    context_messages.append(SystemMessage(content="You are an AI assistant. Answer the current question based on the given SQL query and its result."))
    
    # Include only last 5 previous questions and answers as context if available
    if len(messages) > 1 and "answer" in state and len(state["answer"]) > 0:
        # Get last 5 conversations
        prev_questions, prev_answers = get_last_n_conversations(messages[:-1], state["answer"], 5)

        # Add them to context
        for i in range(len(prev_questions)):
            if i < len(prev_answers):
                context_messages.append(HumanMessage(content=prev_questions[i].content))
                context_messages.append(AIMessage(content=prev_answers[i].content))
    
    # Add the current question with SQL context
    current_task_message = (
        f"Please answer the following question: \"{current_question}\"\n"
        f"To help you, here is the SQL query that was executed: \"{state['query']}\"\n"
        f"And this is the result from the database: \"{state['result']}\""
    )
    context_messages.append(HumanMessage(content=current_task_message))
    
    response = llm.invoke(context_messages)
    return {"answer": response.content}

def generate_vector_answer(state: State):
    """Answer question using RAG with previous context (last 5 only)."""
    # Get current question
    messages = state["question"]
    current_question = messages[-1].content if messages else ""
    
    # Build chat history from last 5 Q&A pairs only
    chat_history_messages = []
    if len(messages) > 1 and "answer" in state and len(state["answer"]) > 0:
        # Get last 5 conversations
        prev_questions, prev_answers = get_last_n_conversations(messages[:-1], state["answer"], 5)
        
        # Add them to chat history
        for i in range(len(prev_questions)):
            if i < len(prev_answers):
                chat_history_messages.append(HumanMessage(content=prev_questions[i].content))
                chat_history_messages.append(AIMessage(content=prev_answers[i].content))

    retriever = vectorstore.as_retriever(
        search_type="mmr",  # Maximum Marginal Relevance - balances relevance with diversity
        search_kwargs={
            "k": 10,        # Number of documents to retrieve
            "fetch_k": 20,  # Fetch more docs initially for filtering
            "lambda_mult": 0.7,  # 0 = max diversity, 1 = max relevance
        }
    )

    docs = vectorstore.similarity_search(current_question, k=20)
    
    bm25_retriever = BM25Retriever.from_documents(docs)
    bm25_retriever.k = 10 
    
    hybrid_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, retriever],
        weights=[0.3, 0.7]  
    )

    rag_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", vectordb_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])

    question_answer_chain = create_stuff_documents_chain(llm, rag_prompt)
    rag_chain = create_retrieval_chain(hybrid_retriever, question_answer_chain)
    result = rag_chain.invoke({
        "input": current_question,
        "chat_history": chat_history_messages
    })
    return {"answer": result["answer"]}

def generate_general_answer(state: State):
    """Generate conversational responses based on last 5 conversations only."""
    # Start with a system message
    messages = [SystemMessage(content="""You are a helpful assistant. Answer the user's question based on the conversation history and context.
    
    Important guidelines:
    - If you receive a question that is related to movies metadata (like directors, cast, release dates, ratings, etc.), say that you don't know the answer.
    - For general conversational questions, provide helpful and natural responses.
    - Use the conversation history to maintain context and provide coherent responses.""")]

    # Add only last 5 Q&A pairs to build conversation context
    question_messages = state["question"]
    answer_messages = state.get("answer", [])
    
    # Build last 7 Q&A history for context
    if len(question_messages) > 1 and len(answer_messages) > 0:
        # Get last 7 conversations (excluding current question)
        prev_questions, prev_answers = get_last_n_conversations(question_messages[:-1], answer_messages, 5)
        
        # Add them to context
        for i in range(len(prev_questions)):
            if i < len(prev_answers):
                messages.append(HumanMessage(content=prev_questions[i].content))
                messages.append(AIMessage(content=prev_answers[i].content))
    
    # Add the current question
    current_question = question_messages[-1].content if question_messages else ""
    messages.append(HumanMessage(content=current_question))
    
    # print(f"Using last {(len(messages)-2)//2} conversations for context")  # -2 for system message and current question
    
    response = llm.invoke(messages)
    return {"answer": response.content}

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

from langchain_ollama import ChatOllama

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph

from langchain_core.messages import (
    HumanMessage, 
    SystemMessage,
)

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph

import asyncio
from websockets.asyncio.server import serve


async def invoke(websocket):
    async for message in websocket:
        memory = MemorySaver()
        global workflow
        app = workflow.compile(checkpointer=memory)
        response = app.invoke(
                        {"messages": [HumanMessage(content=message)]},
                        config={"configurable": {"thread_id": "1"}},
                    )["messages"][-1].content
        await websocket.send(response)


async def main():
    async with serve(invoke, "IP ADDRESS", 4242) as server:
        await server.serve_forever()


if __name__ == "__main__":
    model = ChatOllama(model="llama3.3",temperature=0)
    
    global workflow
    workflow = StateGraph(state_schema=MessagesState)

    # Define the function that calls the model
    def call_model(state: MessagesState):
        system_prompt = (
            "You are a helpful assistant. "
            "Answer all questions to the best of your ability."
        )
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = model.invoke(messages)
        return {"messages": response}

    # Define the node and edge
    workflow.add_node("model", call_model)
    workflow.add_edge(START, "model")
    
    asyncio.run(main())
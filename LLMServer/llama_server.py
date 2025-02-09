import asyncio
from websockets.asyncio.server import serve

from langchain_ollama import ChatOllama

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph

from langchain_core.messages import (
    HumanMessage, 
    SystemMessage,
)

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph

async def llama_handler(websocket):
    async for message in websocket:
        try:
            # Expected format: "adv:<adv_audio_b64>|nat:<nat_audio_b64>|transcript:<transcript_text>"
            print("Received message from client:")
            print(message)
            parts = message.split("|SPLTI|")
            adv_transcript = parts[0]
            nat_transcript = parts[1]

            if adv_transcript is None:
                raise ValueError("Transcript not found in the message.")

            # Process the transcript as needed (for example, call your Llama parser).
            print("Parsed Transcript:", adv_transcript)
            # Optionally, if you want to further process the transcript with a ChatOpenAI or other model:
            # parsed_result = your_llama_processing_function(transcript)
            # For now, we simply echo back a confirmation message.
            
            memory = MemorySaver()
            global workflow
            app = workflow.compile(checkpointer=memory)
            
            adv_response = app.invoke(
                            {"messages": [HumanMessage(content=adv_transcript)]},
                            config={"configurable": {"thread_id": "1"}},
                        )["messages"][-1].content
            
            nat_response = app.invoke(
                            {"messages": [HumanMessage(content=nat_transcript)]},
                            config={"configurable": {"thread_id": "2"}},
                        )["messages"][-1].content
            
            response = f"{adv_response}|SPLTI|{nat_response}"
            await websocket.send(response)
        except Exception as e:
            error_msg = f"Error parsing message: {str(e)}"
            print(error_msg)
            await websocket.send(error_msg)

async def main():
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
    
    # Start a websocket server listening on localhost:9000
    async with serve(llama_handler, "IPADDR2", 4242):
        print("Llama WebSocket server is running on ws://IPADDR2:4242")
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())

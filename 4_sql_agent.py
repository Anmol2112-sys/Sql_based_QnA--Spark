from dotenv import load_dotenv
load_dotenv()

### db, llm , tools,create-agent,system_prompt
import streamlit as st
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase   
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent

db=SQLDatabase.from_uri("sqlite:///My_tasks.db")

db.run("""CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY AUTOINCREMENT,
       title TEXT NOT NULL,
       description TEXT,
       status TEXT CHECK(status IN('pending','in_progress','completed')) DEFAULT 'pending',
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
""")


### llm,tools, memory, system_prompt
llm=ChatGroq(model="openai/gpt-oss-20b")
toolkit=SQLDatabaseToolkit(db=db,llm=llm)
tools=toolkit.get_tools()
memory=InMemorySaver()
 
system_prompt="""
You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct SQLite query to run, then look at the results of the query and return the answer.
Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 5 results.
You can order the results by a relevant column to return the most interesting examples in the database.
Never query for all columns from a table. You must query only the columns that are needed to answer the question.
Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist.
Also, pay attention to which column is in which table.

TASK RULES:
1. Limit SELECT queries to 10 results max with ORDER BY created_at DESC
2. After CREATE/UPDATE/DELETE, confirm with SELECT query
3. If the user requests a list of tasks,present the output in a structured table format to e

CRUD OPERATIONS:
 
- CREATE: Use INSERT INTO tasks (title, description) VALUES (?, ?)
- READ: Use SELECT * FROM tasks WHERE status = 'pending' ORDER BY created_at DESC
- UPDATE: Use UPDATE tasks SET status = 'completed' WHERE id = ?
- DELETE: Use DELETE FROM tasks WHERE id = ?
"""

@st.cache_resource
def get_agent():
    agent=create_agent(
        model=llm,
        tools=tools,
        checkpointer=memory,
        system_prompt=system_prompt
    )
    return agent
agent=get_agent()

st.subheader("Spark- Manage your todo's")


if "messages" not in st.session_state:
    st.session_state.messages=[]
    
    
for message in st.session_state.messages:
     st.chat_message(message["role"]).markdown(message["content"])
    




prompt=st.chat_input("Ask me to manage your tasks ?")
if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("ai"):
        with st.spinner("Processing...."):
            response=agent.invoke({
                "messages":[{"role":"user","content":prompt}]
            },
                                  {"configurable":{"thread_id":"1"}})
            result=response["messages"][-1].content
            st.markdown(result)
            st.session_state.messages.append({"role":"ai","content":result})
    
    
while True:
    query=input("User: ")
    response=agent.invoke({
        "messages":[
            {"role":"user", "content":query}
        ]},
                          {"configurable":{"thread_id":"1"}})
    
    result=response["messages"][-1].content
    print("AI:",result)
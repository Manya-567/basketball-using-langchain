
import streamlit as st
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.agents import Tool, AgentExecutor, initialize_agent
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter
from langchain.schema import SystemMessage
import os

# Setup Gemini
os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.4)

# Streamlit UI
st.set_page_config(page_title="🏀 CoachIQ - Basketball AI", layout="wide")
st.title("🏀 CoachIQ - Smart Basketball AI Assistant")

# File Upload
uploaded_file = st.file_uploader("📂 Upload Team X's last 20 night game data (TXT)", type="txt")
if not uploaded_file:
    st.info("Please upload game data to start using the assistant.")
    st.stop()

# Read and chunk data
raw_text = uploaded_file.read().decode("utf-8")
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
docs = text_splitter.split_documents([Document(page_content=raw_text)])

# Vector Store (FAISS + HuggingFace MiniLM)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_db = FAISS.from_documents(docs, embeddings)
retriever = vector_db.as_retriever()

# RAG QA Chain
rag_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True
)

# Memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Define RAG-enabled Tools
tools = [
    Tool(
        name="Fast Break Pattern Analyzer",
        func=lambda q: rag_chain.run("Analyze fast-break patterns in the past 20 night games: " + q),
        description="Analyzes fast-break patterns in the game logs"
    ),
    Tool(
        name="3-Point Defense Exploiter",
        func=lambda q: rag_chain.run("Analyze weak 3-point defense and suggest training: " + q),
        description="Suggests how to exploit weak 3-point defense"
    ),
    Tool(
        name="Counter Strategy Recommender",
        func=lambda q: rag_chain.run("Suggest counter training strategies to beat fast-breaks: " + q),
        description="Recommends defensive training activities"
    ),
]

# Initialize Agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent="chat-zero-shot-react-description",
    memory=memory,
    verbose=True
)

# Chat Interface
st.subheader("🧠 Ask Tactical Questions")
user_input = st.text_input("🤔 How can we beat Team X?", placeholder="e.g., What are their weaknesses?")
if st.button("💡 Get Strategy") and user_input:
    with st.spinner("Analyzing game logs..."):
        response = agent.run(user_input)
        st.success("🎯 Assistant's Recommendation:")
        st.write(response)

# Display strategy checklist
st.markdown("---")
st.subheader("📋 AI Tactical Plan (Example Output)")
st.markdown("""
#### 1. Fast-Break Counter Strategy
- Assign 2 players to immediately fall back on defense after each shot.
- Conduct drills focused on defensive transition speed.

#### 2. Exploiting 3-Point Defense Weakness
- Practice corner 3-point shots.
- Use fake drives to draw defenders in and pass to open shooters.

#### 3. Continuous Learning
- Retrain strategy weekly by uploading latest game logs.
""")
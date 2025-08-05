import streamlit as st

st.set_page_config(page_title="Chat with Emails (RAG)", page_icon="🤖")

st.title("🤖 Chat with Your Emails")
st.write("Use our AI-powered chat to ask questions about your sent emails. The system uses Retrieval-Augmented Generation (RAG) to find the most relevant information.")
st.info("For this to work, you will need to set up a vector database and an LLM integration (e.g., using LangChain and OpenAI).")

# Placeholder for chat interface
user_question = st.text_input("Ask a question about your emails, e.g., 'What did I promise to send to Jane Smith?'")

if user_question:
    st.write(f"**You:** {user_question}")
    st.write(f"**AI:** I found an email to Jane Smith where you mentioned you would send the 'Q3 report'.")
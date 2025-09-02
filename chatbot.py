from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
# from langchain_community.chat_models import ChatOpenAI
from langchain_community.vectorstores import FAISS
# from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
# from langchain.chat_models import ChatOpenAI
# from langchain.vectorstores import FAISS
# from langchain.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv
import os



load_dotenv()

def load_chatbot():
    embedding = OpenAIEmbeddings()
    db = FAISS.load_local("vector_store", embedding, allow_dangerous_deserialization=True)

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template= """

You are a helpful assistant. Use only the information provided in the following context to answer the question.
If the context does not contain the answer, respond politely with: "Please ask some related questions to this app."
Your response should be in complete sentence format.

Context:
{context}

Question:
{question}

""" )

    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 4})
    llm = ChatOpenAI(temperature=0, model="gpt-4")  # or "gpt-4" if you're using it

    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True
    )

    return qa


def get_answer(query):
    qa_chain = load_chatbot()

    result = qa_chain.invoke(query)
    # result = qa_chain(query)

    answer = result['result']
    sources = [doc.metadata.get("source") for doc in result["source_documents"]]

    return {
        "answer": answer,
        "sources": sources
    }
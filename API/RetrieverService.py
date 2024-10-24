from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA
from pinecone import Pinecone
from langchain_openai import OpenAI
import uuid
from LangSmithRunManager import LangSmithRunManager

class RetrieverService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.pc = Pinecone()
        self.logger = LangSmithRunManager()

    def retrieve_context(self, query: str, domain: str, transaction_id) -> str:
        try:
            run_id = str(uuid.uuid4())
            self.logger.post_run(
                {"retreiver": query},
                f"RetrieverService {transaction_id}", run_id, parent_run_id=transaction_id
            )
            # Initialize Pinecone retriever using the specified domain as the index name
            pinecone_index = self.pc.Index(domain)
            vector_store = PineconeVectorStore(index=pinecone_index, embedding=self.embeddings)
            retriever = RetrievalQA.from_chain_type(chain_type="stuff", retriever=vector_store.as_retriever(), llm=OpenAI())
            # Retrieve relevant context from Pinecone based only on the query
            result = retriever.run(query)

            self.logger.patch_run(
                run_id=run_id,
                output={"context":result}
            )
            return result
        except Exception as e:
            #raise HTTPException(status_code=500, detail=f"Retriever service error: {str(e)}")
            self.logger.patch_run(
                run_id=run_id,
                output="",
            )
            return ""
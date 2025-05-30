import os
import glob
from typing import List, Dict, Any, Generator, Union

from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_ollama.llms import OllamaLLM
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

class RAGSystem:
    def __init__(self, documents_dir: str = "./data"):
        self.documents_dir = documents_dir
        self.documents = []
        self.vector_store = None
        self.qa_chain = None
        self.retriever = None
        
        # 初始化嵌入模型
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text:latest")
        
        # 初始化語言模型
        self.llm = OllamaLLM(model="cwchang/llama3-taide-lx-8b-chat-alpha1:latest", temperature=0.1)
        
    def load_documents(self) -> None:
        """從指定目錄載入所有文字文件"""
        text_files = glob.glob(os.path.join(self.documents_dir, "*.txt"))
        
        for file_path in text_files:
            try:
                # 明確指定編碼為 utf-8
                loader = TextLoader(file_path, encoding="utf-8")
                self.documents.extend(loader.load())
                print(f"成功載入文件: {file_path}")
            except Exception as e:
                print(f"載入文件 {file_path} 時發生錯誤: {str(e)}")
                # 嘗試以其他編碼載入
                try:
                    loader = TextLoader(file_path, encoding="big5")
                    self.documents.extend(loader.load())
                    print(f"使用 big5 編碼成功載入文件: {file_path}")
                except Exception as e2:
                    print(f"使用 big5 編碼載入文件 {file_path} 仍失敗: {str(e2)}")
        
        if not self.documents:
            raise ValueError("未能載入任何文件，請確認文件編碼是否為 UTF-8 或 Big5，並確認文件權限是否正確。")
            
        print(f"Loaded {len(self.documents)} documents")
        
    def process_documents(self) -> None:
        """處理文件並建立向量資料庫"""
        # 文本分割
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        chunks = text_splitter.split_documents(self.documents)
        print(f"Split into {len(chunks)} chunks")
        
        # 建立向量資料庫
        self.vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory="./chroma_db"
        )
        
        print("Vector database created successfully")
        
    def setup_qa_chain(self) -> None:
        """設置問答鏈"""
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )
        
        template = """請根據以下提供的上下文資料回答問題：

        上下文資料：
        {context}
        
        問題：{question}
        
        如果上下文資料中找不到相關資訊，請回答「我無法從提供的資料中找到相關資訊。」
        
        回答時可以適當表明你是「根據提供的資料」或「根據上下文」來回答，
        
        回答："""
        
        QA_PROMPT = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            chain_type_kwargs={"prompt": QA_PROMPT},
            return_source_documents=True  # 返回源文檔
        )
        
    def get_relevant_documents(self, question: str) -> List[Dict[str, str]]:
        """獲取與問題相關的文檔"""
        if not self.retriever:
            raise ValueError("Retriever has not been set up. Please run setup_qa_chain() first.")
            
        docs = self.retriever.get_relevant_documents(question)
        
        context_docs = []
        for doc in docs:
            context_docs.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", "未知來源")
            })
            
        return context_docs
        
    def query(self, question: str, stream: bool = False) -> Union[Dict[str, Any], Generator[str, None, None]]:
        """執行查詢並回傳答案和匹配的上下文"""
        if not self.qa_chain:
            raise ValueError("QA chain has not been set up. Please run setup_qa_chain() first.")
        
        # 獲取相關文檔
        context_docs = self.get_relevant_documents(question)
            
        if stream:
            # 使用流式回調處理器
            callbacks = [StreamingStdOutCallbackHandler()]
            
            # 使用帶有回調的 llm
            streaming_llm = OllamaLLM(
                model="cwchang/llama3-taide-lx-8b-chat-alpha1:latest", 
                temperature=0.1,
                streaming=True,
                callbacks=callbacks
            )
            
            # 創建新的鏈以支持流式輸出
            streaming_chain = RetrievalQA.from_chain_type(
                llm=streaming_llm,
                chain_type="stuff",
                retriever=self.retriever,
                chain_type_kwargs={"prompt": self.qa_chain.combine_documents_chain.llm_chain.prompt}
            )
            
            # 以生成器方式返回結果
            def generate_response():
                response = streaming_chain.invoke({"query": question})
                yield response["result"]
                
            return generate_response(), context_docs
        else:
            # 正常查詢
            response = self.qa_chain.invoke({"query": question})
            
            # 構建結果
            result = {
                "result": response["result"],
                "context_docs": context_docs
            }
            
            return result
        
    def initialize(self) -> None:
        """初始化整個RAG系統"""
        self.load_documents()
        self.process_documents()
        self.setup_qa_chain()
        print("RAG system initialized successfully") 
import sys
import os
import time
from rag import RAGSystem

def create_sample_document():
    """建立範例文件以供測試"""
    if not os.path.exists("data"):
        os.makedirs("data")
        
    sample_text = """人工智能（AI）是指由人類製造出的機器所表現出的智能。
它通常通過機器學習、深度學習等技術實現。
深度學習是機器學習的一個分支，使用多層神經網絡進行模型訓練。
語言模型是自然語言處理中的重要工具，可以用於文本生成、翻譯等任務。
2022年，ChatGPT的發布讓生成式AI成為熱門話題。
RAG（檢索增強生成）是一種將檢索系統與生成模型結合的技術，可以提高生成內容的準確性。"""
    
    with open("data/sample.txt", "w", encoding="utf-8") as f:
        f.write(sample_text)
    print("已建立範例文件")

def display_documents(context_docs):
    """顯示匹配的文檔"""
    print("\n匹配的上下文:")
    if context_docs:
        for i, doc in enumerate(context_docs, 1):
            print(f"\n[文件 {i}] 來源: {os.path.basename(doc['source'])}")
            print("-" * 50)
            print(doc['content'])
            print("-" * 50)
    else:
        print("沒有匹配到相關上下文")

def main():
    # 檢查數據目錄中是否有文件
    if not os.path.exists("data") or not any(file.endswith('.txt') for file in os.listdir("data")):
        print("數據目錄為空，建立範例文件...")
        create_sample_document()
    
    # 初始化RAG系統
    rag_system = RAGSystem()
    
    try:
        print("正在初始化RAG系統...")
        rag_system.initialize()
        print("RAG系統初始化完成！")
        
        # 互動式問答
        print("\n輸入 'exit' 或 'quit' 退出")
        while True:
            question = input("\n請輸入您的問題: ")
            if question.lower() in ['exit', 'quit']:
                break
                
            print("\n正在處理您的問題...")
            try:
                # 獲取相關文檔
                context_docs = rag_system.get_relevant_documents(question)
                
                # 先顯示匹配的文檔
                display_documents(context_docs)
                
                # 顯示回答開始標記
                print("\n回答:")
                print("=" * 50)
                
                # 使用流式輸出方式獲取回答
                streaming_generator = rag_system.query(question, stream=True)
                
                # 確保這是適用於流式輸出的返回結果
                if isinstance(streaming_generator, tuple) and len(streaming_generator) == 2:
                    # 如果返回的是元組 (generator, context_docs)
                    generator = streaming_generator[0]
                else:
                    # 如果直接返回生成器
                    generator = streaming_generator
                
                # 逐字輸出回答
                for chunk in generator:
                    print(chunk, end="", flush=True)
                    time.sleep(0.01)  # 添加一點延遲讓流式效果更明顯
                
                print("\n" + "=" * 50)
                
            except Exception as e:
                print(f"查詢時發生錯誤: {e}")
                import traceback
                traceback.print_exc()  # 印出詳細錯誤堆疊便於調試
    
    except Exception as e:
        print(f"初始化RAG系統時發生錯誤: {e}")

if __name__ == "__main__":
    main() 
document.addEventListener('DOMContentLoaded', () => {
    const questionInput = document.getElementById('question');
    const submitButton = document.getElementById('submit-btn');
    const answerElement = document.getElementById('answer');
    const loader = document.getElementById('loader');

    submitButton.addEventListener('click', async () => {
        const question = questionInput.value.trim();
        
        if (!question) {
            alert('請輸入問題');
            return;
        }

        // 清空答案區域
        answerElement.innerHTML = '';
        
        // 顯示載入動畫
        submitButton.disabled = true;
        loader.style.display = 'block';

        try {
            // 使用 SSE（Server-Sent Events）進行流式請求
            const eventSource = new EventSource(`/stream_query?question=${encodeURIComponent(question)}`);
            
            // 創建上下文區域容器
            const contextContainer = document.createElement('div');
            contextContainer.className = 'context-container';
            
            // 創建回答區域容器
            const answerContent = document.createElement('div');
            answerContent.className = 'answer-content';
            
            // 標題元素
            const contextTitle = document.createElement('h3');
            contextTitle.textContent = '匹配的上下文';
            contextTitle.className = 'context-title';
            
            const answerTitle = document.createElement('h3');
            answerTitle.textContent = '回答';
            answerTitle.className = 'answer-title';
            
            let hasSetupAnswer = false;
            
            // 處理流式更新
            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                switch (data.type) {
                    case 'context':
                        // 顯示上下文
                        if (data.data && data.data.length > 0) {
                            // 添加上下文標題和容器
                            answerElement.appendChild(contextTitle);
                            answerElement.appendChild(contextContainer);
                            
                            // 添加每個文檔
                            data.data.forEach((doc, index) => {
                                const docDiv = document.createElement('div');
                                docDiv.className = 'context-doc';
                                
                                const docTitle = document.createElement('div');
                                docTitle.className = 'context-doc-title';
                                docTitle.textContent = `文件 ${index + 1}: ${doc.source.split('/').pop() || '未知來源'}`;
                                
                                const docContent = document.createElement('pre');
                                docContent.className = 'context-doc-content';
                                docContent.textContent = doc.content;
                                
                                docDiv.appendChild(docTitle);
                                docDiv.appendChild(docContent);
                                contextContainer.appendChild(docDiv);
                            });
                        } else {
                            // 沒有上下文的情況
                            answerElement.appendChild(contextTitle);
                            
                            const noContextMsg = document.createElement('div');
                            noContextMsg.className = 'no-context-message';
                            noContextMsg.textContent = '沒有匹配到相關上下文';
                            
                            answerElement.appendChild(noContextMsg);
                        }
                        
                        // 添加回答區域
                        answerElement.appendChild(answerTitle);
                        answerElement.appendChild(answerContent);
                        hasSetupAnswer = true;
                        break;
                        
                    case 'answer':
                        // 確保回答區域已設置
                        if (!hasSetupAnswer) {
                            answerElement.appendChild(answerTitle);
                            answerElement.appendChild(answerContent);
                            hasSetupAnswer = true;
                        }
                        
                        // 添加流式回答
                        answerContent.textContent += data.data;
                        break;
                        
                    case 'done':
                        // 流式傳輸結束，關閉連接
                        eventSource.close();
                        submitButton.disabled = false;
                        loader.style.display = 'none';
                        break;
                }
            };
            
            eventSource.onerror = (error) => {
                console.error('SSE錯誤:', error);
                eventSource.close();
                
                answerElement.textContent = `錯誤: 流式傳輸中斷`;
                submitButton.disabled = false;
                loader.style.display = 'none';
            };
            
        } catch (error) {
            console.error('查詢錯誤:', error);
            answerElement.textContent = `錯誤: 無法連接到伺服器，請確認 API 服務已啟動`;
            submitButton.disabled = false;
            loader.style.display = 'none';
        }
    });

    // 支援按 Enter 鍵提交
    questionInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submitButton.click();
        }
    });

    // 檢查伺服器狀態
    checkServerStatus();

    async function checkServerStatus() {
        try {
            const response = await fetch('/health');
            if (response.ok) {
                console.log('伺服器連線正常');
            } else {
                answerElement.textContent = '警告: API 伺服器可能未正常運行';
            }
        } catch (error) {
            console.error('伺服器狀態檢查錯誤:', error);
            answerElement.textContent = '警告: 無法連接到 API 伺服器，請確認服務已啟動';
        }
    }
}); 
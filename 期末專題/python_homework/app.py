from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import openai
import json
from datetime import datetime, timedelta
import pytz
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app)

# 直接設定 API key
openai.api_key = "輸入自己的 OpenAI API 金鑰"

# 檔案路徑
DATA_DIR = 'data'
CHAT_HISTORY_FILE = os.path.join(DATA_DIR, 'chat_history.json')
CALENDAR_EVENTS_FILE = os.path.join(DATA_DIR, 'calendar_events.json')

# 確保資料目錄存在
os.makedirs(DATA_DIR, exist_ok=True)

def load_chat_history():
    try:
        if os.path.exists(CHAT_HISTORY_FILE):
            with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"載入聊天記錄時發生錯誤: {e}")
    return []

def save_chat_history(chat_history):
    try:
        with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(chat_history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"儲存聊天記錄時發生錯誤: {e}")

def load_calendar_events():
    try:
        if os.path.exists(CALENDAR_EVENTS_FILE):
            with open(CALENDAR_EVENTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"載入日曆事件時發生錯誤: {e}")
    return []

def save_calendar_events(calendar_events):
    try:
        with open(CALENDAR_EVENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(calendar_events, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"儲存日曆事件時發生錯誤: {e}")

# 載入儲存的資料
chat_history = load_chat_history()
calendar_events = load_calendar_events()

def get_current_time():
    # 使用台北時區
    tz = pytz.timezone('Asia/Taipei')
    return datetime.now(tz)

def format_system_prompt():
    current_time = get_current_time()
    today_date = current_time.strftime("%Y-%m-%d")
    
    return f"""你是一個學習助手，可以幫助安排讀書計畫和管理行事曆。

當使用者要新增事件時，你可以一次處理多筆任務。請依照以下格式回覆：

1. 用自然語言回應使用者
2. 接著另起一行，提供 JSON 格式的事件資料陣列，每個事件包含以下欄位：
   [
     {{
       "title": "事件標題",
       "start_time": "YYYY-MM-DDTHH:mm:ss",  // 請使用 ISO 8601 格式
       "end_time": "YYYY-MM-DDTHH:mm:ss",    // 請使用 ISO 8601 格式
       "description": "事件描述"
     }},
     {{
       // 第二個事件
     }},
     // ... 更多事件
   ]

今天是 {today_date}。
如果使用者沒有指定時間，請使用合理的預設時間。
如果使用者要求排定多個任務，請幫忙安排適當的時間，避免時間重疊。
請考慮學習效率，在安排時間時注意：
1. 每個學習時段建議 1-2 小時
2. 不同科目之間最好有休息時間
3. 避免安排太晚的時段（除非使用者特別要求）
4. 可以建議最佳的學習順序

範例回應：
好的，我已經幫您安排了讀書計畫，考慮了各科目的難度和時間分配。

[
  {{"title": "英文讀書時間", "start_time": "{today_date}T14:00:00", "end_time": "{today_date}T15:30:00", "description": "專注英文學習"}},
  {{"title": "休息時間", "start_time": "{today_date}T15:30:00", "end_time": "{today_date}T16:00:00", "description": "適當休息，恢復精神"}},
  {{"title": "數學讀書時間", "start_time": "{today_date}T16:00:00", "end_time": "{today_date}T17:30:00", "description": "數學練習與複習"}}
]"""

@app.route('/')
def index():
    # 載入日曆事件
    events = load_calendar_events()
    # 將事件資料轉換為 FullCalendar 格式
    calendar_events = []
    for event in events:
        calendar_events.append({
            'title': event['title'],
            'start': event['start_time'],
            'end': event['end_time'],
            'description': event.get('description', '')
        })
    return render_template('index.html', events=calendar_events)

@socketio.on('send_message')
def handle_message(data):
    message = data['message']
    chat_history.append({"role": "user", "content": message})
    save_chat_history(chat_history)
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": format_system_prompt()},
                *chat_history
            ]
        )
        
        assistant_message = response.choices[0].message.content
        chat_history.append({"role": "assistant", "content": assistant_message})
        save_chat_history(chat_history)
        
        # 嘗試從回應中提取 JSON
        try:
            json_start = assistant_message.rfind('[')
            if json_start != -1:
                json_str = assistant_message[json_start:]
                events_data = json.loads(json_str)
                
                if isinstance(events_data, list):  # 確保是陣列
                    for event_data in events_data:
                        if all(key in event_data for key in ['title', 'start_time', 'end_time']):
                            try:
                                # 驗證日期時間格式
                                start_time = datetime.fromisoformat(event_data['start_time'].replace('Z', '+00:00'))
                                end_time = datetime.fromisoformat(event_data['end_time'].replace('Z', '+00:00'))
                                
                                calendar_events.append(event_data)
                            except ValueError as e:
                                print(f"日期時間格式錯誤: {e}")
                    
                    save_calendar_events(calendar_events)
                    emit('calendar_update', calendar_events)
        except json.JSONDecodeError:
            pass  # 不是 JSON 格式，當作普通對話處理
        except Exception as e:
            print(f"處理事件時發生錯誤: {e}")
        
        emit('receive_message', {'message': assistant_message, 'is_bot': True})
    except Exception as e:
        emit('receive_message', {'message': f"發生錯誤: {str(e)}", 'is_bot': True})

@app.route('/api/events', methods=['GET'])
def get_events():
    return jsonify(calendar_events)

@app.route('/api/events', methods=['POST'])
def add_event():
    event = request.json
    calendar_events.append(event)
    save_calendar_events(calendar_events)  # 儲存日曆事件
    return jsonify({"status": "success"})

# 新增：查看聊天記錄的路由
@app.route('/chat_history')
def view_chat_history():
    return jsonify(chat_history)

if __name__ == '__main__':
    socketio.run(app, debug=True) 
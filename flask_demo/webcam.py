import cv2
import os

OUTPUT_FILENAME = 'result.jpg'

def capture_image():
    try:
        # 啟動預設攝影機 (通常是 0)
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("無法開啟攝影機")
            return

        # 等待一小段時間讓攝影機啟動
        cv2.waitKey(1000)

        # 讀取一幀影像
        ret, frame = cap.read()

        if ret:
            # 儲存影像
            cv2.imwrite(OUTPUT_FILENAME, frame)
            print(f"照片已儲存為 {OUTPUT_FILENAME}")
        else:
            print("無法讀取影像")

        # 釋放攝影機資源
        cap.release()
        cv2.destroyAllWindows()

    except Exception as e:
        print(f"發生錯誤: {e}")

if __name__ == "__main__":
    capture_image()
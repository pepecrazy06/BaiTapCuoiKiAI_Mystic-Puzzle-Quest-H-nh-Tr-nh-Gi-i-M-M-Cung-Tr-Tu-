import hupper
import main

if __name__ == '__main__':
    # Kích hoạt chế độ theo dõi và tự động chạy lại hàm main() trong file main.py
    hupper.start_reloader('main.main')
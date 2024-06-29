import os
import re
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, \
    QProgressBar, QTextEdit, QToolBar, QGridLayout, QScrollArea, QTableWidget, QDockWidget, QTableWidgetItem, \
    QColorDialog, QInputDialog
from PyQt5.QtGui import QPainter, QPen, QImage
from PyQt5.QtCore import Qt, QPoint, QThread, pyqtSignal
import requests
import json
import base64
import openai
import pandas as pd
import openpyxl
class Worker(QThread):
    progress_updated = pyqtSignal(int)  # Signal for progress updates
    content_updated = pyqtSignal(str)  # Signal for content updates
    tokens_used_updated = pyqtSignal(int, float)  # Signal for tokens used updates with cost

    def __init__(self, headers, params, is_image=False, image_width=512, image_height=512):
        super().__init__()
        self.headers = headers
        self.params = params
        self.is_image = is_image
        self.image_width = image_width
        self.image_height = image_height

    def run(self):
        try:
            client = requests.Session()
            response = client.post("https://api.openai.com/v1/chat/completions", headers=self.headers, json=self.params, stream=True)

            if response.status_code != 200:
                print(f"Error: HTTP {response.status_code} - {response.text}")
                return

            total_received_content = 0
            total_content_length = 4096  # Assuming max_tokens is the total content length
            reply = ""
            tokens_used = 0
            input_cost_per_token = 5.00 / 1_000_000  # Cost per input token in USD
            output_cost_per_token = 15.00 / 1_000_000  # Cost per output token in USD

            # Calculate image cost based on dimensions
            if self.is_image:
                tiles_x = (self.image_width + 511) // 512
                tiles_y = (self.image_height + 511) // 512
                total_tiles = tiles_x * tiles_y
                base_tokens = 85
                tile_tokens = 170 * total_tiles
                total_image_tokens = base_tokens + tile_tokens
                image_cost_per_tile = total_image_tokens * input_cost_per_token
            else:
                image_cost_per_tile = 0

            for line in response.iter_lines():
                if line:
                    decoded_line = json.loads(line.decode('utf-8').strip()[len("data: "):])
                    if 'choices' in decoded_line:
                        for choice in decoded_line['choices']:
                            if 'delta' in choice and 'content' in choice['delta']:
                                content_chunk = choice['delta']['content']
                                if content_chunk:
                                    reply += content_chunk
                                    total_received_content += len(content_chunk)
                                    tokens_used += len(content_chunk.split())
                                    progress_percentage = int((total_received_content / total_content_length) * 100)
                                    # Calculate progress percentage
                                    self.progress_updated.emit(progress_percentage)

                                    total_cost = tokens_used * (input_cost_per_token + output_cost_per_token) + image_cost_per_tile
                                    self.tokens_used_updated.emit(tokens_used, total_cost)
                                    self.content_updated.emit(content_chunk)

            self.progress_updated.emit(100)  # Ensure progress bar reaches 100%
        except Exception as e:
            print(f"Error in worker thread: {e}")

class DrawingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = QImage(self.size(), QImage.Format_RGB32)
        self.image.fill(Qt.white)
        self.drawing = False
        self.last_point = QPoint()
        self.pen_color = Qt.black

    def paintEvent(self, event):
        canvas_painter = QPainter(self)
        canvas_painter.drawImage(self.rect(), self.image, self.image.rect())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.last_point = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.drawing:
            painter = QPainter(self.image)
            pen = QPen(self.pen_color, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self.last_point, event.pos())
            self.last_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False

    def resizeEvent(self, event):
        if self.width() > self.image.width() or self.height() > self.image.height():
            new_image = QImage(self.size(), QImage.Format_RGB32)
            new_image.fill(Qt.white)
            painter = QPainter(new_image)
            painter.drawImage(QPoint(0, 0), self.image)
            self.image = new_image
    def change_pen_color(self, new_color):
        self.pen_color = new_color
    def save_image(self, path):
        self.image.save(path)

    def clear_image(self):
        self.image.fill(Qt.white)
        self.update()

class TableWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Table Window")
        self.table = QTableWidget(self)  # 5 rows, 3 columns
        self.setCentralWidget(self.table)




    # Then, when you want to show the table window, use `self.table_window.show()`

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 Drawing App with GPT-4")
        self.setGeometry(100, 100, 800, 600)

        self.drawing_widget = DrawingWidget(self)
        #self.setCentralWidget(self.drawing_widget)

        self.init_ui()
        self.table_widget = TableWindow(self)

    def init_ui(self):
        # Layout principale
        widget = QWidget()
        # QVBoxLayout for this new widget
        layout = QVBoxLayout()
        widget.setLayout(layout)

        self.token_counter = QLabel("Tokens used: 0 - Total cost: $0.0000")
        layout.addWidget(self.token_counter)

        self.progress = QProgressBar()
        layout.addWidget(self.progress)



        self.prompt_text = QTextEdit()
        self.prompt_text.setPlaceholderText("Enter your request here...")
        layout.addWidget(self.prompt_text)
        self.result_label = QTextEdit()
        self.result_label.setReadOnly(True)  # Imposta come read-only
        layout.addWidget(self.result_label)

        # Create toolbar
        toolbar = self.addToolBar("Toolbar")

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_image)
        toolbar.addWidget(save_button)

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_image)
        toolbar.addWidget(clear_button)

        analyze_button = QPushButton("Analyze")
        analyze_button.clicked.connect(self.analyze_image)
        toolbar.addWidget(analyze_button)
        color_button = QPushButton("Color")
        color_button.clicked.connect(self.change_color)
        toolbar.addWidget(color_button)

        # Set widget as central widget
        self.setCentralWidget(widget)
        # Create dock widget and add drawing widget to it
        drawing_dock = QDockWidget()
        drawing_dock.setWidget(self.drawing_widget)

        # Add dock widget to QMainWindow
        self.addDockWidget(Qt.LeftDockWidgetArea, drawing_dock)

    def change_color(self):
        color = QColorDialog.getColor()

        if color.isValid():
            self.current_color = color

        self.drawing_widget.change_pen_color(self.current_color)
    def save_image(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG Files (*.png);;All Files (*)")
        if file_path:
            self.drawing_widget.save_image(file_path)

    def clear_image(self):
        self.drawing_widget.clear_image()

    def analyze_image(self):
        prompt = self.prompt_text.toPlainText()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG Files (*.png);;All Files (*)")
        if file_path:
            self.drawing_widget.save_image(file_path)
            response = self.get_gpt4_response(prompt, file_path)
            self.result_label.setText(response)

    def start_worker(self, headers, params, is_image=False):
        self.worker = Worker(headers, params, is_image=is_image)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.content_updated.connect(self.update_content)
        self.worker.tokens_used_updated.connect(self.update_tokens_used)
        self.worker.start()

    def process_response(self, response):
        # Cerca tutte le linee con dati della tabella
        table_data = re.findall(r'\|(.+)\|', response)

        table_data = table_data[1:]  # Rimuovi l'intestazione

        # Rimuove gli spazi bianchi iniziali e finali e divide ogni linea in celle
        table_data = [list(map(str.strip, row.split("|"))) for row in table_data]

        self.table_widget.table.setRowCount(len(table_data))
        self.table_widget.table.setColumnCount(len(table_data[0]))

        for row in range(len(table_data)):
            for column in range(len(table_data[0])):
                self.table_widget.table.setItem(row, column, QTableWidgetItem(table_data[row][column]))
        self.table_widget.show()

    def get_api_key(self):
        api_key_file = "apikey.txt"

        # Check if the API key file exists
        if os.path.exists(api_key_file):
            with open(api_key_file, 'r') as file:
                apikey = file.read().strip()
        else:
            # Create a QApplication instance (required for QDialog)
            app = QApplication([])

            # Prompt the user to input the API key
            apikey, ok = QInputDialog.getText(None, "API Key Input", "Enter your API key:")

            if ok and apikey:
                # Save the API key to a text file
                with open(api_key_file, 'w') as file:
                    file.write(apikey)
            else:
                raise ValueError("API key input was cancelled or empty.")

        return apikey
    def get_gpt4_response(self, prompt, url):
        apikey = self.get_api_key()
        instructions_path = "example.xlsx"

        # Leggi le istruzioni dal file Excel
        df = pd.read_excel(instructions_path)
        instructions_content = df.to_string(index=False)

        def encode_image(image_path):
            try:
                with open(image_path, "rb") as image_file:
                    return base64.b64encode(image_file.read()).decode('utf-8')
            except FileNotFoundError:
                print(f"No file found at {image_path}. Please check the file path.")
                return None

        openai.api_key = apikey
        base64_image = encode_image(url)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai.api_key}"
        }

        params = {
            "model": "gpt-4o",
            "temperature": 0.5,
            "user": "my_customer",
            "max_tokens": 4096,
            "top_p": 0.5,
            "stream": True,
            "messages": [
                {
                    "role": "system",
                    "content": f"Sono un assistente che fornisce descrizioni dettagliate e collegamenti utili sulla base"
                               f" di queste istruzioni{instructions_content}."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
        }

        self.start_worker(headers, params, is_image=True)

    def update_progress(self, progress):
        self.progress.setValue(progress)

    def update_content(self, content):
        combined_message = self.result_label.toPlainText() + content
        self.result_label.setText(combined_message)
        self.process_response(combined_message)

    def update_tokens_used(self, tokens_used, total_cost):
        self.token_counter.setText(f"Tokens used: {tokens_used} - Total cost: ${total_cost:.4f}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
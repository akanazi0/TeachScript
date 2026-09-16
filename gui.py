import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QTextEdit, QPushButton, 
                             QTabWidget, QSplitter)
from PyQt5.QtCore import Qt
from parser import LexicalScanner

class LexicalAnalyzerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lexical Analyzer")
        self.resize(800, 600)

        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Input Area
        input_label = QLabel("Source Code:")
        input_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        main_layout.addWidget(input_label)

        self.input_text = QTextEdit()
        self.input_text.setFontFamily("Courier")
        self.input_text.setFontPointSize(10)
        
        default_test = """name = Khalid;
if (name > 5) {
then print "Hello Khalid";
}
// test for lexical analyzer """
        self.input_text.setText(default_test)

        # Button and Status Area
        btn_layout = QHBoxLayout()
        self.scan_btn = QPushButton("Scan Code")
        self.scan_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 5px;")
        self.scan_btn.clicked.connect(self.run_scan)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: blue;")

        btn_layout.addWidget(self.scan_btn)
        btn_layout.addWidget(self.status_label)
        btn_layout.addStretch()

        # Tabs for Output
        self.tabs = QTabWidget()
        
        # Tokens Tab
        self.tokens_text = QTextEdit()
        self.tokens_text.setReadOnly(True)
        self.tokens_text.setFontFamily("Courier")
        self.tabs.addTab(self.tokens_text, "Tokens")

        # Symbols Tab
        self.symbols_text = QTextEdit()
        self.symbols_text.setReadOnly(True)
        self.symbols_text.setFontFamily("Courier")
        self.tabs.addTab(self.symbols_text, "Symbol Table")

        # Errors Tab
        self.errors_text = QTextEdit()
        self.errors_text.setReadOnly(True)
        self.errors_text.setFontFamily("Courier")
        self.errors_text.setStyleSheet("color: red;")
        self.tabs.addTab(self.errors_text, "Errors")

        # Use Splitter to make input and output resizable
        splitter = QSplitter(Qt.Vertical)
        
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(self.input_text)
        top_layout.addLayout(btn_layout)
        
        splitter.addWidget(top_widget)
        splitter.addWidget(self.tabs)
        
        main_layout.addWidget(splitter)

    def run_scan(self):
        source_code = self.input_text.toPlainText()
        scanner = LexicalScanner(source_code)
        tokens, symbols, errors = scanner.scan()

        # Update Tokens
        self.tokens_text.clear()
        tokens_str = "\n".join([str(t) for t in tokens])
        self.tokens_text.setPlainText(tokens_str)

        # Update Symbols
        self.symbols_text.clear()
        symbols_str = "\n".join([f"{name}: First seen at line {line}" for name, line in symbols.items()])
        self.symbols_text.setPlainText(symbols_str)

        # Update Errors
        self.errors_text.clear()
        if errors:
            errors_str = "\n".join(errors)
            self.errors_text.setPlainText(errors_str)
            self.tabs.setCurrentIndex(2) # Switch to errors tab
        else:
            self.errors_text.setPlainText("No lexical errors found.\n")
            self.tabs.setCurrentIndex(0) # Switch to tokens tab

        self.status_label.setText(f"Total lexemes found: {len(tokens)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LexicalAnalyzerGUI()
    window.show()
    sys.exit(app.exec_())

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import yfinance as yf
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
import random
import threading
import queue
import time

class StockAdvisorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Real-Time Stock Advisor")
        self.root.geometry("1200x800")
        
        # Configure styles)
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Helvetica', 10))
        self.style.configure('Title.TLabel', font=('Helvetica', 16, 'bold'))
        self.style.configure('Stock.TLabel', font=('Helvetica', 12, 'bold'))
        self.style.configure('Positive.TLabel', foreground='green')
        self.style.configure('Negative.TLabel', foreground='red')
        
        # Create main frames
        self.header_frame = ttk.Frame(root)
        self.header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.footer_frame = ttk.Frame(root)
        self.footer_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Header
        ttk.Label(self.header_frame, text="AI Real-Time Stock Advisor , (Tathagata Ghosh - 12301189, Susovhan Kundu - 12303595)", style='Title.TLabel').pack(side=tk.LEFT)
        
        # Current time label
        self.time_label = ttk.Label(self.header_frame, text="")
        self.time_label.pack(side=tk.RIGHT)
        self.update_time()
        
        # Main content - split into left and right
        self.left_frame = ttk.Frame(self.main_frame, width=300)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # Left frame - stock selection and details
        self.setup_stock_selection()
        self.setup_stock_details()
        
        # Right frame - chart and chat
        self.setup_chart_frame()
        self.setup_chat_bot()
        
        # Footer - market status and news
        self.setup_footer()
        
        # Initialize with default stock
        self.selected_stock = "AAPL"
        self.update_stock_data()
        
        # Message queue for chat bot
        self.message_queue = queue.Queue()
        self.root.after(100, self.process_messages)
        
        # Start background data updates
        self.running = True
        self.update_thread = threading.Thread(target=self.background_update, daemon=True)
        self.update_thread.start()
    
    def update_time(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=now)
        self.root.after(1000, self.update_time)
    
    def setup_stock_selection(self):
        frame = ttk.LabelFrame(self.left_frame, text="Stock Selection", padding=10)
        frame.pack(fill=tk.X, pady=5)
        
        self.stock_var = tk.StringVar(value="AAPL")
        
        popular_stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", "V", "WMT"]
        
        for stock in popular_stocks:
            rb = ttk.Radiobutton(
                frame, 
                text=stock, 
                variable=self.stock_var, 
                value=stock,
                command=self.on_stock_select
            )
            rb.pack(anchor=tk.W)
        
        # Custom stock entry
        ttk.Label(frame, text="Or enter symbol:").pack(anchor=tk.W, pady=(10, 0))
        
        self.custom_stock_entry = ttk.Entry(frame)
        self.custom_stock_entry.pack(fill=tk.X, pady=5)
        
        self.custom_stock_button = ttk.Button(
            frame, 
            text="Load Custom Stock", 
            command=self.on_custom_stock
        )
        self.custom_stock_button.pack(fill=tk.X)
    
    def setup_stock_details(self):
        frame = ttk.LabelFrame(self.left_frame, text="Stock Details", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Basic info
        self.stock_name_label = ttk.Label(frame, text="", style='Stock.TLabel')
        self.stock_name_label.pack(anchor=tk.W, pady=(0, 10))
        
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(info_frame, text="Current Price:").grid(row=0, column=0, sticky=tk.W)
        self.price_label = ttk.Label(info_frame, text="", style='Stock.TLabel')
        self.price_label.grid(row=0, column=1, sticky=tk.E)
        
        ttk.Label(info_frame, text="Today's Change:").grid(row=1, column=0, sticky=tk.W)
        self.change_label = ttk.Label(info_frame, text="")
        self.change_label.grid(row=1, column=1, sticky=tk.E)
        
        ttk.Label(info_frame, text="Market Cap:").grid(row=2, column=0, sticky=tk.W)
        self.mcap_label = ttk.Label(info_frame, text="")
        self.mcap_label.grid(row=2, column=1, sticky=tk.E)
        
        ttk.Label(info_frame, text="PE Ratio:").grid(row=3, column=0, sticky=tk.W)
        self.pe_label = ttk.Label(info_frame, text="")
        self.pe_label.grid(row=3, column=1, sticky=tk.E)
        
        # AI recommendation
        ttk.Label(frame, text="AI Recommendation:", style='Stock.TLabel').pack(anchor=tk.W, pady=(10, 0))
        
        self.recommendation_label = ttk.Label(frame, text="", style='Stock.TLabel')
        self.recommendation_label.pack(anchor=tk.W)
        
        self.recommendation_detail = tk.Text(frame, height=5, wrap=tk.WORD, state=tk.DISABLED)
        self.recommendation_detail.pack(fill=tk.X, pady=5)
        
        # Action buttons
        action_frame = ttk.Frame(frame)
        action_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            action_frame, 
            text="Buy", 
            command=lambda: self.trade_action("buy")
        ).pack(side=tk.LEFT, expand=True)
        
        ttk.Button(
            action_frame, 
            text="Sell", 
            command=lambda: self.trade_action("sell")
        ).pack(side=tk.LEFT, expand=True)
        
        ttk.Button(
            action_frame, 
            text="Watchlist", 
            command=lambda: self.trade_action("watchlist")
        ).pack(side=tk.LEFT, expand=True)
    
    def setup_chart_frame(self):
        frame = ttk.LabelFrame(self.right_frame, text="Stock Chart", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Time frame selection
        time_frame = ttk.Frame(frame)
        time_frame.pack(fill=tk.X, pady=5)
        
        self.time_period = tk.StringVar(value="1mo")
        
        periods = [
            ("1D", "1d"),
            ("1W", "1wk"),
            ("1M", "1mo"),
            ("3M", "3mo"),
            ("1Y", "1y"),
            ("5Y", "5y")
        ]
        
        for text, period in periods:
            rb = ttk.Radiobutton(
                time_frame, 
                text=text, 
                variable=self.time_period, 
                value=period,
                command=self.update_chart
            )
            rb.pack(side=tk.LEFT, padx=5)
        
        # Chart area
        self.figure = plt.Figure(figsize=(8, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        
        self.canvas = FigureCanvasTkAgg(self.figure, master=frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Indicators
        indicator_frame = ttk.Frame(frame)
        indicator_frame.pack(fill=tk.X, pady=5)
        
        self.show_ma = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            indicator_frame, 
            text="Moving Average (50)", 
            variable=self.show_ma,
            command=self.update_chart
        ).pack(side=tk.LEFT, padx=5)
        
        self.show_rsi = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            indicator_frame, 
            text="RSI", 
            variable=self.show_rsi,
            command=self.update_chart
        ).pack(side=tk.LEFT, padx=5)
    
    def setup_chat_bot(self):
        frame = ttk.LabelFrame(self.right_frame, text="AI Stock Advisor Chat", padding=10)
        frame.pack(fill=tk.BOTH, pady=5)
        
        self.chat_display = scrolledtext.ScrolledText(
            frame, 
            height=10, 
            wrap=tk.WORD, 
            state=tk.DISABLED
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=5)
        
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        self.chat_input = ttk.Entry(input_frame)
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.chat_input.bind("<Return>", self.send_chat_message)
        
        ttk.Button(
            input_frame, 
            text="Send", 
            command=self.send_chat_message
        ).pack(side=tk.RIGHT)
        
        # Add welcome message
        self.add_chat_message("AI Advisor", "Welcome to AI Stock Advisor! How can I help you today?")
    
    def setup_footer(self):
        # Market status
        status_frame = ttk.LabelFrame(self.footer_frame, text="Market Status", padding=10)
        status_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.market_status = ttk.Label(status_frame, text="Market: Closed", style='Stock.TLabel')
        self.market_status.pack(anchor=tk.W)
        
        indices = ["^GSPC", "^DJI", "^IXIC", "^RUT"]
        
        for index in indices:
            idx_frame = ttk.Frame(status_frame)
            idx_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(idx_frame, text=index).pack(side=tk.LEFT)
            ttk.Label(idx_frame, text="", width=15).pack(side=tk.RIGHT)
        
        # News headlines
        news_frame = ttk.LabelFrame(self.footer_frame, text="Latest News", padding=10)
        news_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        self.news_list = tk.Listbox(
            news_frame, 
            height=4, 
            selectmode=tk.SINGLE,
            background="white"
        )
        self.news_list.pack(fill=tk.BOTH, expand=True)
        
        # Add some sample news
        sample_news = [
            "Fed signals potential rate cuts in Q3",
            "Tech stocks rally on AI optimism",
            "Oil prices surge amid supply concerns",
            "Retail sales exceed expectations"
        ]
        
        for news in sample_news:
            self.news_list.insert(tk.END, news)
    
    def on_stock_select(self):
        self.selected_stock = self.stock_var.get()
        self.update_stock_data()
    
    def on_custom_stock(self):
        custom_stock = self.custom_stock_entry.get().strip().upper()
        if custom_stock:
            self.selected_stock = custom_stock
            self.update_stock_data()
        else:
            messagebox.showwarning("Input Error", "Please enter a stock symbol")
    
    def update_stock_data(self):
        try:
            stock = yf.Ticker(self.selected_stock)
            info = stock.info
            
            # Update basic info
            self.stock_name_label.config(text=f"{info.get('longName', 'N/A')} ({self.selected_stock})")
            
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
            prev_close = info.get('previousClose', 'N/A')
            
            if current_price != 'N/A' and prev_close != 'N/A':
                change = current_price - prev_close
                change_pct = (change / prev_close) * 100
                
                self.price_label.config(text=f"${current_price:.2f}")
                
                if change >= 0:
                    self.change_label.config(
                        text=f"+${change:.2f} (+{change_pct:.2f}%)", 
                        style='Positive.TLabel'
                    )
                else:
                    self.change_label.config(
                        text=f"-${abs(change):.2f} ({change_pct:.2f}%)", 
                        style='Negative.TLabel'
                    )
            else:
                self.price_label.config(text="N/A")
                self.change_label.config(text="N/A")
            
            # Market cap
            market_cap = info.get('marketCap', 'N/A')
            if market_cap != 'N/A':
                if market_cap >= 1e12:
                    market_cap_str = f"${market_cap/1e12:.2f}T"
                elif market_cap >= 1e9:
                    market_cap_str = f"${market_cap/1e9:.2f}B"
                elif market_cap >= 1e6:
                    market_cap_str = f"${market_cap/1e6:.2f}M"
                else:
                    market_cap_str = f"${market_cap:.2f}"
                
                self.mcap_label.config(text=market_cap_str)
            else:
                self.mcap_label.config(text="N/A")
            
            # PE ratio
            pe_ratio = info.get('trailingPE', 'N/A')
            self.pe_label.config(text=pe_ratio if pe_ratio != 'N/A' else "N/A")
            
            # Generate AI recommendation
            self.generate_recommendation(stock)
            
            # Update chart
            self.update_chart()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch data for {self.selected_stock}: {str(e)}")
    
    def generate_recommendation(self, stock):
        # Simulate AI analysis with some randomness
        actions = ["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"]
        weights = [0.2, 0.3, 0.3, 0.15, 0.05]  # Higher probability for positive recommendations
        
        recommendation = random.choices(actions, weights=weights)[0]
        
        # Generate reasoning
        reasons = {
            "Strong Buy": [
                "Exceptional growth potential with strong fundamentals",
                "Undervalued based on our AI analysis with positive momentum",
                "Industry leader with expanding market share"
            ],
            "Buy": [
                "Solid financials with reasonable valuation",
                "Positive earnings outlook with manageable risks",
                "Technical indicators show upward momentum"
            ],
            "Hold": [
                "Fairly valued with balanced risk/reward",
                "Waiting for clearer signals on future performance",
                "Mixed technical and fundamental indicators"
            ],
            "Sell": [
                "Valuation appears stretched relative to peers",
                "Deteriorating fundamentals and negative momentum",
                "Increased competitive pressures affecting margins"
            ],
            "Strong Sell": [
                "Significant downside risk identified",
                "Severe fundamental deterioration",
                "Technical indicators show strong downward momentum"
            ]
        }
        
        reason = random.choice(reasons[recommendation])
        
        # Update UI
        self.recommendation_label.config(text=recommendation)
        
        # Set color based on recommendation
        if "Buy" in recommendation:
            self.recommendation_label.config(foreground="green")
        elif "Sell" in recommendation:
            self.recommendation_label.config(foreground="red")
        else:
            self.recommendation_label.config(foreground="black")
        
        # Update detail
        self.recommendation_detail.config(state=tk.NORMAL)
        self.recommendation_detail.delete(1.0, tk.END)
        
        analysis = f"""AI Analysis for {self.selected_stock}:
        
Recommendation: {recommendation}
Reason: {reason}

Key Metrics:
- P/E Ratio: {stock.info.get('trailingPE', 'N/A')}
- PEG Ratio: {stock.info.get('pegRatio', 'N/A')}
- Profit Margins: {stock.info.get('profitMargins', 'N/A')}
- Debt/Equity: {stock.info.get('debtToEquity', 'N/A')}
"""
        
        self.recommendation_detail.insert(tk.END, analysis)
        self.recommendation_detail.config(state=tk.DISABLED)
    
    def update_chart(self):
        try:
            period = self.time_period.get()
            stock = yf.Ticker(self.selected_stock)
            
            # Determine interval based on period
            if period == "1d":
                interval = "5m"
                data = stock.history(period=period, interval=interval)
                # For intraday, we need to filter out pre/post market if desired
                data = data.between_time('09:30', '16:00')
            elif period in ["1wk", "5d"]:
                interval = "60m"
                data = stock.history(period="5d", interval=interval)
            else:
                interval = "1d"
                data = stock.history(period=period, interval=interval)
            
            # Clear previous chart
            self.ax.clear()
            
            # Plot closing prices
            self.ax.plot(data.index, data['Close'], label='Price', color='blue')
            
            # Add moving average if selected
            if self.show_ma.get():
                ma_window = 50 if len(data) > 50 else len(data) // 2
                if ma_window > 1:
                    ma = data['Close'].rolling(window=ma_window).mean()
                    self.ax.plot(data.index, ma, label=f'MA {ma_window}', color='orange')
            
            # Add RSI if selected
            if self.show_rsi.get() and len(data) > 14:
                delta = data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                
                # Create a second y-axis for RSI
                ax2 = self.ax.twinx()
                ax2.plot(data.index, rsi, label='RSI', color='purple', alpha=0.5)
                ax2.axhline(70, color='red', linestyle='--', alpha=0.3)
                ax2.axhline(30, color='green', linestyle='--', alpha=0.3)
                ax2.set_ylim(0, 100)
                ax2.set_ylabel('RSI')
                ax2.legend(loc='upper right')
            
            # Format chart
            self.ax.set_title(f"{self.selected_stock} Price Chart ({period})")
            self.ax.set_xlabel("Date")
            self.ax.set_ylabel("Price ($)")
            self.ax.grid(True, alpha=0.3)
            self.ax.legend(loc='upper left')
            
            # Rotate x-axis labels for better readability
            plt.setp(self.ax.get_xticklabels(), rotation=45, ha='right')
            
            # Adjust layout
            self.figure.tight_layout()
            
            # Redraw canvas
            self.canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Chart Error", f"Failed to update chart: {str(e)}")
    
    def add_chat_message(self, sender, message):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def send_chat_message(self, event=None):
        message = self.chat_input.get().strip()
        if message:
            self.add_chat_message("You", message)
            self.chat_input.delete(0, tk.END)
            
            # Simulate AI thinking
            self.root.after(1000, lambda: self.generate_ai_response(message))
    
    def generate_ai_response(self, user_message):
        # Simple AI response logic
        user_message = user_message.lower()
        
        if any(word in user_message for word in ["hello", "hi", "hey"]):
            response = "Hello! How can I assist you with your stock research today?"
        elif any(word in user_message for word in ["price", "current", "value"]):
            response = f"The current price of {self.selected_stock} is {self.price_label.cget('text')}."
        elif any(word in user_message for word in ["recommend", "suggest", "advice"]):
            response = f"Our AI recommends: {self.recommendation_label.cget('text')}. " \
                      "Would you like more details about this recommendation?"
        elif any(word in user_message for word in ["chart", "graph", "technical"]):
            response = "I can help you analyze the technical indicators. " \
                      "Try enabling RSI or moving averages from the chart controls."
        elif any(word in user_message for word in ["news", "update", "headline"]):
            response = "Recent market news is displayed at the bottom of the screen. " \
                      "Would you like me to summarize any specific news item?"
        elif any(word in user_message for word in ["thank", "thanks"]):
            response = "You're welcome! Let me know if you have any other questions."
        else:
            response = "I'm an AI stock advisor. I can help with stock analysis, " \
                      "price information, recommendations, and technical analysis. " \
                      "How can I assist you?"
        
        self.add_chat_message("AI Advisor", response)
    
    def trade_action(self, action):
        stock = self.selected_stock
        price = self.price_label.cget("text")
        
        if action == "buy":
            message = f"Buy order placed for {stock} at {price}"
            messagebox.showinfo("Order Confirmation", message)
        elif action == "sell":
            message = f"Sell order placed for {stock} at {price}"
            messagebox.showinfo("Order Confirmation", message)
        elif action == "watchlist":
            message = f"{stock} added to your watchlist"
            messagebox.showinfo("Watchlist", message)
        
        self.add_chat_message("System", f"Action: {action} for {stock}")
    
    def background_update(self):
        while self.running:
            try:
                # Update market status
                market_open = 9 <= datetime.now().hour < 16
                status = "Market: Open" if market_open else "Market: Closed"
                self.message_queue.put(("update_status", status))
                
                # Update stock data every 60 seconds
                if datetime.now().second == 0:
                    self.message_queue.put(("update_stock", None))
                
                time.sleep(1)
            except:
                pass
    
    def process_messages(self):
        try:
            while not self.message_queue.empty():
                msg_type, data = self.message_queue.get_nowait()
                
                if msg_type == "update_status":
                    self.market_status.config(text=data)
                elif msg_type == "update_stock":
                    self.update_stock_data()
        
        finally:
            self.root.after(100, self.process_messages)
    
    def on_closing(self):
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = StockAdvisorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
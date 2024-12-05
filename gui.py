import tkinter as tk
from tkinter import ttk
import asyncio
import threading
import websockets
import json
import time

class TradingGUI:
    def __init__(self, master):
        self.master = master
        master.title("Trading Bot")

        # Parameters
        self.parameters_frame = tk.LabelFrame(master, text="Parameters")
        self.parameters_frame.pack(padx=10, pady=10, fill="x")

        self.total_amount_label = tk.Label(self.parameters_frame, text="Total Amount")
        self.total_amount_label.grid(row=0, column=0, sticky="e")
        self.total_amount_entry = tk.Entry(self.parameters_frame)
        self.total_amount_entry.grid(row=0, column=1)
        self.total_amount_entry.insert(0, "1.0")

        self.chunk_size_label = tk.Label(self.parameters_frame, text="Chunk Size")
        self.chunk_size_label.grid(row=1, column=0, sticky="e")
        self.chunk_size_entry = tk.Entry(self.parameters_frame)
        self.chunk_size_entry.grid(row=1, column=1)
        self.chunk_size_entry.insert(0, "0.1")

        self.spread_label = tk.Label(self.parameters_frame, text="Spread")
        self.spread_label.grid(row=2, column=0, sticky="e")
        self.spread_entry = tk.Entry(self.parameters_frame)
        self.spread_entry.grid(row=2, column=1)
        self.spread_entry.insert(0, "0.001")

        self.min_spread_label = tk.Label(self.parameters_frame, text="Min Spread")
        self.min_spread_label.grid(row=3, column=0, sticky="e")
        self.min_spread_entry = tk.Entry(self.parameters_frame)
        self.min_spread_entry.grid(row=3, column=1)
        self.min_spread_entry.insert(0, "0.0005")

        self.max_slippage_label = tk.Label(self.parameters_frame, text="Max Slippage")
        self.max_slippage_label.grid(row=4, column=0, sticky="e")
        self.max_slippage_entry = tk.Entry(self.parameters_frame)
        self.max_slippage_entry.grid(row=4, column=1)
        self.max_slippage_entry.insert(0, "0.002")

        # Start and Stop buttons
        self.buttons_frame = tk.Frame(master)
        self.buttons_frame.pack(pady=5)

        self.start_button = tk.Button(self.buttons_frame, text="Start", command=self.start_trading)
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = tk.Button(self.buttons_frame, text="Stop", command=self.stop_trading, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=5)

        # Progress
        self.progress_frame = tk.LabelFrame(master, text="Progress")
        self.progress_frame.pack(padx=10, pady=10, fill="x")

        self.current_spread_label = tk.Label(self.progress_frame, text="Current Spread: ")
        self.current_spread_label.pack(anchor="w")

        self.orders_placed_label = tk.Label(self.progress_frame, text="Orders Placed: ")
        self.orders_placed_label.pack(anchor="w")

        self.orders_filled_label = tk.Label(self.progress_frame, text="Orders Filled: ")
        self.orders_filled_label.pack(anchor="w")

        self.total_traded_label = tk.Label(self.progress_frame, text="Total Traded Amount: ")
        self.total_traded_label.pack(anchor="w")

        self.remaining_amount_label = tk.Label(self.progress_frame, text="Remaining Amount: ")
        self.remaining_amount_label.pack(anchor="w")

        # Variables to store trading data
        self.trading_data = {
            'current_spread': 0.0,
            'orders_placed': 0,
            'orders_filled': 0,
            'total_traded': 0.0,
            'remaining_amount': 0.0
        }

        self.is_trading = False

        self.lock = threading.Lock()

    def start_trading(self):
        # Get parameters from entries
        self.TOTAL_AMOUNT = float(self.total_amount_entry.get())
        self.CHUNK_SIZE = float(self.chunk_size_entry.get())
        self.SPREAD = float(self.spread_entry.get())
        self.MIN_SPREAD = float(self.min_spread_entry.get())
        self.MAX_SLIPPAGE = float(self.max_slippage_entry.get())

        # Update remaining amount
        self.trading_data['remaining_amount'] = self.TOTAL_AMOUNT

        self.is_trading = True

        # Disable start button and enable stop button
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

        # Start the trading in a separate thread
        trading_thread = threading.Thread(target=self.run_trading, daemon=True)
        trading_thread.start()

        # Start updating the GUI
        self.update_gui()

    def stop_trading(self):
        self.is_trading = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        print("Trading stopped.")

    def run_trading(self):
        asyncio.run(self.main_async())

    async def main_async(self):
        try:
            await self.fetch_orderbooks()
        except Exception as e:
            print(f"An error occurred: {e}")

    async def fetch_orderbooks(self):
        """
        Connect to WebSocket streams for real-time order book updates.
        """
        orderbooks = {
            "Exchange1": {'bids': [], 'asks': []},
            "Exchange2": {'bids': [], 'asks': []}
        }

        EXCHANGE1_WS_URL = f"ws://localhost:8765"
        EXCHANGE2_WS_URL = f"ws://localhost:8766"

        # Create events to signal when order books are updated
        self.orderbook_events = {
            "Exchange1": asyncio.Event(),
            "Exchange2": asyncio.Event()
        }

        async with websockets.connect(EXCHANGE1_WS_URL) as ws_long, \
                   websockets.connect(EXCHANGE2_WS_URL) as ws_short:

            # Subscribe to order book updates
            await ws_long.send(json.dumps({
                "method": "SUBSCRIBE",
                "params": ["BTCUSDT@depth"],
                "id": 1
            }))
            await ws_short.send(json.dumps({
                "method": "SUBSCRIBE",
                "params": ["BTCUSDT@depth"],
                "id": 1
            }))

            # Start tasks to read from websockets
            long_task = asyncio.create_task(self.read_orderbook(ws_long, "Exchange1", orderbooks))
            short_task = asyncio.create_task(self.read_orderbook(ws_short, "Exchange2", orderbooks))
            manage_task = asyncio.create_task(self.manage_orders_loop(orderbooks))

            await asyncio.gather(long_task, short_task, manage_task)

    async def read_orderbook(self, websocket, exchange_name, orderbooks):
        """
        Read messages from the websocket and update the orderbook.
        """
        try:
            async for message in websocket:
                data = json.loads(message)
                parsed_data = self.parse_orderbook(data, orderbooks[exchange_name])
                if parsed_data:
                    orderbooks[exchange_name] = parsed_data
                    self.orderbook_events[exchange_name].set()
        except websockets.ConnectionClosed:
            print(f"{exchange_name}: WebSocket connection closed.")

    async def manage_orders_loop(self, orderbooks):
        """
        Continuously manage orders based on updated orderbooks.
        """
        while self.is_trading and self.trading_data['remaining_amount'] > 0:
            await asyncio.gather(
                self.orderbook_events["Exchange1"].wait(),
                self.orderbook_events["Exchange2"].wait()
            )
            await self.manage_orders(orderbooks)
            self.orderbook_events["Exchange1"].clear()
            self.orderbook_events["Exchange2"].clear()

    async def manage_orders(self, orderbooks):
        """
        Manage orders based on the current order books and remaining trade amount.
        """
        with self.lock:
            remaining_amount = self.trading_data['remaining_amount']

        long_orderbook = orderbooks["Exchange1"]
        short_orderbook = orderbooks["Exchange2"]

        if not long_orderbook['bids'] or not short_orderbook['asks']:
            await asyncio.sleep(0.1)
            return

        # Get the best bid/ask prices
        long_best_bid = float(long_orderbook['bids'][0]['price'])
        short_best_ask = float(short_orderbook['asks'][0]['price'])

        # Calculate the current spread
        current_spread = (long_best_bid - short_best_ask) / short_best_ask

        with self.lock:
            self.trading_data['current_spread'] = current_spread

        # Check if the desired spread is met
        if current_spread >= self.SPREAD:
            # Determine the chunk size
            long_chunk = min(self.CHUNK_SIZE, remaining_amount, float(long_orderbook['bids'][0]['quantity']))
            short_chunk = min(self.CHUNK_SIZE, remaining_amount, float(short_orderbook['asks'][0]['quantity']))
            trade_amount = min(long_chunk, short_chunk)

            if trade_amount <= 0:
                await asyncio.sleep(0.1)
                return

            # Place limit orders
            self.place_limit_order("Exchange1", "BTCUSDT", long_best_bid, trade_amount, "SELL")
            self.place_limit_order("Exchange2", "BTCUSDT", short_best_ask, trade_amount, "BUY")

            with self.lock:
                self.trading_data['orders_placed'] += 2

            # Wait for one of the limit orders to be filled
            while self.is_trading:
                # Check order status
                long_filled = self.check_order_filled("Exchange1", "BTCUSDT", "SELL")
                short_filled = self.check_order_filled("Exchange2", "BTCUSDT", "BUY")

                if long_filled:
                    # Place a market order on the opposite exchange
                    self.place_market_order("Exchange2", "BTCUSDT", trade_amount, "BUY")
                    self.cancel_all_orders("Exchange1", "BTCUSDT")
                    with self.lock:
                        self.trading_data['orders_filled'] += 1
                        self.trading_data['total_traded'] += trade_amount
                        self.trading_data['remaining_amount'] -= trade_amount
                    break

                elif short_filled:
                    # Place a market order on the opposite exchange
                    self.place_market_order("Exchange1", "BTCUSDT", trade_amount, "SELL")
                    self.cancel_all_orders("Exchange2", "BTCUSDT")
                    with self.lock:
                        self.trading_data['orders_filled'] += 1
                        self.trading_data['total_traded'] += trade_amount
                        self.trading_data['remaining_amount'] -= trade_amount
                    break

                await asyncio.sleep(0.1)

        else:
            print(f"Spread too low: {current_spread:.5f}. Waiting for better conditions.")
            await asyncio.sleep(1)

    def parse_orderbook(self, data, orderbook):
        """
        Parse order book update and update the local orderbook.
        """
        if 'b' in data and 'a' in data:
            bids = [{'price': bid[0], 'quantity': bid[1]} for bid in data['b']]
            asks = [{'price': ask[0], 'quantity': ask[1]} for ask in data['a']]

            orderbook['bids'] = sorted(bids, key=lambda x: float(x['price']), reverse=True)
            orderbook['asks'] = sorted(asks, key=lambda x: float(x['price']))

            return orderbook
        else:
            return None

    # Placeholder functions to emulate exchange actions
    def place_limit_order(self, exchange, symbol, price, amount, side):
        """
        Emulate placing a limit order on the exchange.
        """
        print(f"Placing limit {side} order on {exchange}: {amount} {symbol} at {price}")

    def cancel_all_orders(self, exchange, symbol):
        """
        Emulate canceling all open orders for a specific symbol on the exchange.
        """
        print(f"Cancelling all orders on {exchange} for {symbol}")

    def check_order_filled(self, exchange, symbol, side):
        """
        Emulate checking if an order has been filled on the specified exchange.
        """
        # For demonstration, we simulate an order being filled randomly
        return random.choice([True, False])

    def place_market_order(self, exchange, symbol, amount, side):
        """
        Emulate placing a market order on the exchange.
        """
        print(f"Placing market {side} order on {exchange}: {amount} {symbol}")

    def update_gui(self):
        # Update the GUI with the latest trading data
        with self.lock:
            current_spread = self.trading_data['current_spread']
            orders_placed = self.trading_data['orders_placed']
            orders_filled = self.trading_data['orders_filled']
            total_traded = self.trading_data['total_traded']
            remaining_amount = self.trading_data['remaining_amount']

        self.current_spread_label.config(text=f"Current Spread: {current_spread:.5f}")
        self.orders_placed_label.config(text=f"Orders Placed: {orders_placed}")
        self.orders_filled_label.config(text=f"Orders Filled: {orders_filled}")
        self.total_traded_label.config(text=f"Total Traded Amount: {total_traded:.4f}")
        self.remaining_amount_label.config(text=f"Remaining Amount: {remaining_amount:.4f}")

        if self.is_trading and remaining_amount > 0:
            # Schedule the next update
            self.master.after(1000, self.update_gui)  # Update every 1 second
        else:
            self.is_trading = False
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            print("Trading completed.")

if __name__ == "__main__":
    import random  # Import random module for check_order_filled function

    root = tk.Tk()
    gui = TradingGUI(root)
    root.mainloop()

import asyncio
import websockets
import json
import random

# Configuration for the mock exchanges
EXCHANGE1_PORT = 8765
EXCHANGE2_PORT = 8766
SYMBOL = "BTCUSDT"

async def mock_exchange_server(websocket, exchange_name):
    """
    Mock exchange server that sends fake order book updates.
    """
    async for message in websocket:
        # Parse the received message
        data = json.loads(message)
        # Check if it's a subscription message
        if data.get('method') == 'SUBSCRIBE':
            print(f"{exchange_name}: Client subscribed to {data.get('params')}")
            # Send fake order book updates periodically
            try:
                while True:
                    # Adjust price ranges based on the exchange to simulate a positive spread
                    if exchange_name == "Exchange1":
                        # Exchange1 has higher bid prices and ask prices
                        bid_prices = [random.uniform(60500, 61000) for _ in range(5)]
                        ask_prices = [random.uniform(61000, 61500) for _ in range(5)]
                    elif exchange_name == "Exchange2":
                        # Exchange2 has lower bid prices and ask prices
                        bid_prices = [random.uniform(59500, 60000) for _ in range(5)]
                        ask_prices = [random.uniform(60000, 60500) for _ in range(5)]
                    else:
                        # Default price ranges
                        bid_prices = [random.uniform(50000, 60000) for _ in range(5)]
                        ask_prices = [random.uniform(60000, 70000) for _ in range(5)]
                    
                    # Generate fake order book data
                    orderbook_update = {
                        'e': 'depthUpdate',
                        'E': int(asyncio.get_event_loop().time() * 1000),
                        's': SYMBOL,
                        'b': [[str(price), str(random.uniform(0.1, 1.0))] for price in bid_prices],
                        'a': [[str(price), str(random.uniform(0.1, 1.0))] for price in ask_prices]
                    }
                    await websocket.send(json.dumps(orderbook_update))
                    await asyncio.sleep(1)  # Send updates every second
            except websockets.ConnectionClosed:
                print(f"{exchange_name}: Client disconnected")
                break

async def main():
    server1 = await websockets.serve(
        lambda ws: mock_exchange_server(ws, "Exchange1"),
        "localhost",
        EXCHANGE1_PORT
    )
    server2 = await websockets.serve(
        lambda ws: mock_exchange_server(ws, "Exchange2"),
        "localhost",
        EXCHANGE2_PORT
    )
    print(f"Mock Exchange1 server started on port {EXCHANGE1_PORT}")
    print(f"Mock Exchange2 server started on port {EXCHANGE2_PORT}")
    await asyncio.gather(server1.wait_closed(), server2.wait_closed())

if __name__ == "__main__":
    asyncio.run(main())

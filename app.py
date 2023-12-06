from flask import Flask, render_template, request, jsonify
import alpaca_trade_api as tradeapi
import config, json, requests

app = Flask(__name__)

api = tradeapi.REST(config.API_KEY, config.API_SECRET, base_url='https://paper-api.alpaca.markets')

@app.route('/')
def dashboard():
    orders = api.list_orders()
    return render_template('dashboard.html', alpaca_orders=orders)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        webhook_message = json.loads(request.data)
        
        if webhook_message['passphrase'] != config.WEBHOOK_PASSPHRASE:
            return jsonify({
                'code': 'error',
                'message': 'Nice try buddy'
            })
        
        price = webhook_message['strategy']['order_price']
        symbol = webhook_message['ticker']
        side = webhook_message['strategy']['order_action']
        
        quantity = 4  # Set the quantity to 4 contracts or any fixed value you prefer
        
        order = api.submit_order(symbol, quantity, side, 'limit', 'gtc', limit_price=price)

        if config.DISCORD_WEBHOOK_URL:
            chat_message = {
                "username": "strategyalert",
                "avatar_url": "https://i.imgur.com/4M34hi2.png",
                "content": f"TradingView strategy alert triggered: {quantity} {symbol} @ {price}"
            }

            requests.post(config.DISCORD_WEBHOOK_URL, json=chat_message)

        return jsonify(webhook_message)
    
    except json.decoder.JSONDecodeError as e:
        # Print the error for debugging purposes
        print("JSON decoding error:", e)
        # Return a simple error response
        return jsonify({'error': 'JSON decoding error'})

if __name__ == "__main__":
    app.run()

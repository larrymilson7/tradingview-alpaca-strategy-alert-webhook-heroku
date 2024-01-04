from flask import Flask, render_template, request
import alpaca_trade_api as tradeapi
import config, json, requests

app = Flask(__name__)

api = tradeapi.REST(config.API_KEY, config.API_SECRET, base_url='https://paper-api.alpaca.markets')

def close_positions(symbol, current_side):
    positions = api.list_positions()
    for position in positions:
        if position.symbol == symbol:
            if int(position.qty) > 0 and current_side == 'sell':
                api.submit_order(symbol, abs(int(position.qty - positions)), 'sell', 'market', 'gtc')
            elif int(position.qty) < 0 and current_side == 'buy':
                api.submit_order(symbol, abs(int(position.qty - positions)), 'buy', 'market', 'gtc')

@app.route('/')
def dashboard():
    orders = api.list_orders()
    return render_template('dashboard.html', alpaca_orders=orders)

@app.route('/webhook', methods=['POST'])
def webhook():
    webhook_message = json.loads(request.data)

    if webhook_message['passphrase'] != config.WEBHOOK_PASSPHRASE:
        return {
            'code': 'error',
            'message': 'nice try buddy'
        }
    
    quantity = webhook_message['strategy']['order_contracts']
    symbol = webhook_message['ticker']
    side = webhook_message['strategy']['order_action']

    # Close positions if needed before opening new ones
    close_positions(symbol, side)

    order = api.submit_order(symbol, quantity, side, 'market', 'gtc')

    if config.DISCORD_WEBHOOK_URL:
        chat_message = {
            "username": "strategyalert",
            "avatar_url": "https://i.imgur.com/4M34hi2.png",
            "content": f"tradingview strategy alert triggered: {quantity} {symbol} - Market Order"
        }
        requests.post(config.DISCORD_WEBHOOK_URL, json=chat_message)

    return webhook_message

if __name__ == '__main__':
    app.run(debug=True)

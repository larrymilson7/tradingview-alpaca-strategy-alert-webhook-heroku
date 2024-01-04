from flask import Flask, render_template, request
import alpaca_trade_api as tradeapi
import config
import json
import requests

app = Flask(__name__)

api = tradeapi.REST(config.API_KEY, config.API_SECRET, base_url='https://paper-api.alpaca.markets')

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

    # Get current positions
    positions = api.list_positions()
    current_position = 0
    for position in positions:
        if position.symbol == symbol:
            current_position = int(position.qty)
            break

    if (side == 'buy' and current_position < 0) or (side == 'sell' and current_position > 0):
        # Calculate the net position to be closed
        net_position = abs(current_position) if abs(current_position) < abs(quantity) else abs(quantity)

        # Close the net position
        close_order = api.submit_order(symbol, net_position, 'sell' if current_position > 0 else 'buy', 'market', 'day')

        # Calculate the remaining quantity to be opened
        remaining_quantity = abs(quantity) - net_position

        if remaining_quantity != 0:
            # Open the remaining position
            remaining_order = api.submit_order(symbol, remaining_quantity, side, 'market', 'day')

        # Respond to the webhook request
        return webhook_message

    else:
        # If no position to close, open a new one
        order = api.submit_order(symbol, abs(quantity), side, 'market', 'day')

        # Respond to the webhook request
        return webhook_message

if __name__ == '__main__':
    app.run(debug=True)

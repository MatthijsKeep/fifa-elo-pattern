from flask import Flask, request, jsonify
import elo

app = Flask(__name__)

@app.route('/calculate_elo', methods=['POST'])
def calculate_elo():
    data = request.get_json()
    player1_elo = data['player1_elo']
    player2_elo = data['player2_elo']
    player1_result = data['player1_result']

    new_elo1, new_elo2 = elo.update_elo(player1_elo, player2_elo, player1_result)

    return jsonify({
        'player1_new_elo': new_elo1,
        'player2_new_elo': new_elo2
    })

if __name__ == '__main__':
    app.run()

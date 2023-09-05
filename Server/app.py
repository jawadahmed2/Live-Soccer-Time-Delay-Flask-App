# Main file to run the server
from flask import  jsonify, request
# from scrapeTimeDelayTeams import display_bet365live_matches, display_22betlive_matches, get_timedelay
import os
from flask import Flask, render_template
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "projectlivematches"
CORS(app)
basedir = os.path.abspath(os.path.dirname(__file__))

@app.route('/')
def index():
    return 'Server Is Active. Access its Services Through Client or Frontend'


@app.route('/home/api')
def home():
    pass
    # Return the JSON data to the home.html template
    return


@app.route('/get-22betmatches/api', methods=['GET'])
def get_22betmatches():
    if request.method == 'GET':
        from scrapeTimeDelayTeams import display_22betlive_matches
        # result get in the pandas dataframe
        result = display_22betlive_matches()

        # Convert the DataFrame to JSON format
        result_json = result.to_json(orient='records')

        print('Successfully Scraped 22bet Matches')
        return jsonify(result_json)
    else:
        return "Invalid request method", 405


@app.route('/get-bet365matches/api', methods=['GET'])
def get_bet365matches():
    if request.method == 'GET':
        from scrapeTimeDelayTeams import display_bet365live_matches
        # result get in the pandas dataframe
        result = display_bet365live_matches()

        # Convert the DataFrame to JSON format
        result_json = result.to_json(orient='records')

        print('Successfully Scraped bet365 Matches')
        return jsonify(result_json)
    else:
        return "Invalid request method", 405




if __name__ == '__main__':
    app.run(debug=True)
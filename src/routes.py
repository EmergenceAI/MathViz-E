import logging
import os

from flask import render_template
from flask import request
from flask import Response
from flask import send_from_directory
from flask import stream_with_context


def register_routes(app, math_viz_agent, base_dir):
    """Register routes for the app

    Args:
        app (Flask): Flask app
        math_viz_agent (MathVizAgent): MathVizAgent instance
        base_dir (str): Base directory of the app
    """
    @app.route('/desmos/interpret', methods=['POST'])
    def handle_interpret():
        print(request.json)
        input_text = request.json['text']
        #sessionid=request.json['sessionid']
        input_expressions = request.json["expressions"]
        use_validation = (os.environ.get('USE_EXPRESSION_VALIDATION') == "True")
        return Response(
            stream_with_context(
                math_viz_agent.process_user_request(
                    input_text,
                    input_expressions,
                    use_validation
                )
            ),
            mimetype='text/event-stream'
        )

    @app.route('/desmos/')
    def serve_index():
        logging.info("Starting app ...")
        desmos_api_key = os.environ.get('DESMOS_API_KEY') # Desmos API key will be send to the client
        return render_template('desmos_calc.html', desmos_api_key=desmos_api_key)

    @app.route('/desmos/static/<path:path>')
    def get_assets(path):
        return send_from_directory(os.path.join(base_dir, "static"), path)

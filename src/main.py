import logging
import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask

from src.agents.math_viz_agent import MathVizAgent
from src.routes import register_routes

#TODO: Set permanent session lifetime to sensible value.
app = Flask(__name__, template_folder='.')
app.permanent_session_lifetime = timedelta(days=1)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
)

if __name__ == '__main__':
    load_dotenv()
    math_viz_agent = MathVizAgent()
    register_routes(app, math_viz_agent, BASE_DIR)
    host="localhost"
    if os.getenv("USE_DOCKER") == "True":
        host = "0.0.0.0"
    app.run(debug=False, port=5001, host=host)

from .config import bp as config_bp
from .env_vars import bp as env_vars_bp
from .environments import bp as environments_bp
from .packages import bp as packages_bp
from .files import bp as files_bp

ALL_BLUEPRINTS = [
    config_bp,
    env_vars_bp,
    environments_bp,
    packages_bp,
    files_bp,
]


def register_blueprints(app):
    for bp in ALL_BLUEPRINTS:
        app.register_blueprint(bp)

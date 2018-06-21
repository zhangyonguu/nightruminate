from app import create_app
from app import db
from app.models import User
app = create_app()


@app.shell_context_processor
def shell_context():
    return {'db': db, 'User': User,}


if __name__ == '__main__':
    app.run()

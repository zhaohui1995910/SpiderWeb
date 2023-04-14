from main import create_app
from flask_script import Manager, Server
from flask_migrate import MigrateCommand


app = create_app()
app.app_context().push()

manager = Manager(app)

manager.add_command('db', MigrateCommand)
# manager.add_command("runserver", Server(port=6868, ssl_crt='cert.pem', ssl_key='key.pem', host='0.0.0.0'))
manager.add_command("runserver", Server(port=5000,  host='0.0.0.0'))

if __name__ == '__main__':
    manager.run()


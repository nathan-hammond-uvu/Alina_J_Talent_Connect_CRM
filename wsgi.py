from crm.ui.web.app import create_app

# Gunicorn entrypoint: gunicorn wsgi:app
app = create_app()

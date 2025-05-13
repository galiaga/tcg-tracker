import os
from dotenv import load_dotenv

load_dotenv()

from backend import create_app

app = create_app()

if __name__ == '__main__':
    debug_mode = app.config.get('DEBUG', False)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)), debug=debug_mode)

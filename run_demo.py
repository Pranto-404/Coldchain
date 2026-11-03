"""Start complete local demo: python run_demo.py. Default demo passwords in README."""
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent/'.env')
os.environ.setdefault('DEMO_MODE','1')
os.environ.setdefault('MQTT_ENABLED','0')
if __name__=='__main__':
    import uvicorn
    uvicorn.run('coldchain.app:app',host=os.getenv('BIND_HOST','127.0.0.1'),port=int(os.getenv('PORT','8000')),reload=False)

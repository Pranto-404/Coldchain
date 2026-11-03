"""Prepare Vercel rewrites after your Render backend has a public URL."""
from pathlib import Path
from urllib.parse import urlparse
import json,sys

def create_config(url):
    url=url.strip().rstrip('/')
    u=urlparse(url)
    if u.scheme!='https' or not u.hostname or u.path not in ('','/') or u.query or u.fragment or u.username or u.password or u.port:
        raise ValueError('Use a clean HTTPS hostname only, e.g. https://myapp.onrender.com')
    return {
        '$schema':'https://openapi.vercel.sh/vercel.json',
        'framework':None,
        'outputDirectory':'public',
        'rewrites':[
            {'source':'/api/:path*','destination':url+'/api/:path*'},
            {'source':'/check/:token','destination':url+'/check/:token'},
            {'source':'/health','destination':url+'/health'},
        ],
    }

def main():
    url=(sys.argv[1] if len(sys.argv)>1 else input('Paste your Render backend URL (https://...onrender.com): '))
    cfg=create_config(url)
    target=Path(__file__).resolve().parent/'vercel-frontend'/'vercel.json'
    target.write_text(json.dumps(cfg,indent=2)+'\n',encoding='utf-8')
    print('OK - configured:',target)
    print('Next: commit and push to GitHub, then import in Vercel with Root Directory=vercel-frontend')
    print('Do not deploy before replacing the placeholder URL.')

if __name__=='__main__':
    try:main()
    except (ValueError,EOFError) as e:
        print('ERROR:',e); sys.exit(1)

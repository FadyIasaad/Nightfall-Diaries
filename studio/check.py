"""Read-only Meta SUAT verification without exposing credentials."""
import json,os,urllib.request,urllib.error

def main():
 token=os.getenv('INSTAGRAM_ACCESS_TOKEN','').strip(); account=os.getenv('INSTAGRAM_ACCOUNT_ID','').strip()
 if not token or not account:
  raise SystemExit('BLOCKED: Instagram token and account ID secrets are both required')
 if not account.isdigit(): raise SystemExit('BLOCKED: invalid account ID format')
 url=f'https://graph.facebook.com/v25.0/{account}?fields=id,username'
 req=urllib.request.Request(url,headers={'Authorization':'Bearer '+token})
 try:
  with urllib.request.urlopen(req,timeout=30) as r: result=json.load(r)
 except urllib.error.HTTPError as e:
  try: err=json.loads(e.read()).get('error',{})
  except Exception: err={}
  print('META_CHECK_FAILED HTTP',e.code,'error code',err.get('code'),'subcode',err.get('error_subcode'))
  raise SystemExit(1)
 except Exception as e:
  print('META_CHECK_FAILED',type(e).__name__)
  raise SystemExit(1)
 if str(result.get('id'))!=account: raise SystemExit('BLOCKED: account ID mismatch')
 print('META_CHECK_PASS: Instagram ID matches configured account')
 print('USERNAME:',result.get('username','not returned'))
if __name__=='__main__': main()

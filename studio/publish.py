"""Explicit permission-checked draft upload adapters.
No credentials => skipped with clear receipt. No native YouTube Studio unsaved Draft API.
"""
import os, json
from pathlib import Path
import requests
from .util import ROOT, read, save, utcnow, checkpoint

PLATFORMS=('youtube','facebook','tiktok')

class MissingCredentials(Exception):pass
class UploadError(Exception):pass

def _need(*names):
    missing=[name for name in names if not os.getenv(name)]
    if missing:raise MissingCredentials('Missing: '+', '.join(missing))

def _check_public(mode,secret):
    if mode in ('public','PUBLISHED') and not (secret and os.environ.get('DRAMA_ALLOW_UNREVIEWED_PUBLIC')=='true'):
        raise UploadError('Public mode disabled: requires config publish_unreviewed=true and secret DRAMA_ALLOW_UNREVIEWED_PUBLIC=true')

def _good(resp):
    resp.raise_for_status()
    data=resp.json()
    if 'error' in data and isinstance(data['error'],dict) and data['error'].get('code') not in ('ok',0,None):raise UploadError(f'Remote API rejected request: {data["error"].get("code")}')
    return data

def youtube(path,title,description,config):
    _need('YOUTUBE_CLIENT_ID','YOUTUBE_CLIENT_SECRET','YOUTUBE_REFRESH_TOKEN','YOUTUBE_EXPECTED_CHANNEL_ID')
    mode=config['platform_modes']['youtube'];_check_public(mode,config['publish_unreviewed'])
    tok=_good(requests.post('https://oauth2.googleapis.com/token',data={'client_id':os.environ['YOUTUBE_CLIENT_ID'],'client_secret':os.environ['YOUTUBE_CLIENT_SECRET'],
        'refresh_token':os.environ['YOUTUBE_REFRESH_TOKEN'],'grant_type':'refresh_token'},timeout=30))['access_token']
    headers={'Authorization':'Bearer '+tok}
    channel=_good(requests.get('https://www.googleapis.com/youtube/v3/channels',params={'part':'id','mine':'true'},headers=headers,timeout=30))
    ids=[c['id'] for c in channel.get('items',[])]
    if os.environ['YOUTUBE_EXPECTED_CHANNEL_ID'] not in ids:raise UploadError('OAuth account does not match expected EXISTING YouTube channel; check read scope/authorization')
    meta={'snippet':{'title':title[:100],'description':description[:4900],'categoryId':'24'},'status':{'privacyStatus':mode,'containsSyntheticMedia':True}}
    size=Path(path).stat().st_size
    response=requests.post('https://www.googleapis.com/upload/youtube/v3/videos',params={'uploadType':'resumable','part':'snippet,status'},headers={**headers,'Content-Type':'application/json','X-Upload-Content-Length':str(size),'X-Upload-Content-Type':'video/mp4'},json=meta,timeout=60)
    response.raise_for_status()
    location=response.headers.get('Location')
    if not location or not location.startswith('https://www.googleapis.com/'):raise UploadError('No validated YouTube resumable Location')
    with open(path,'rb') as f:
        end=requests.put(location,data=f,headers={'Content-Type':'video/mp4','Content-Length':str(size)},timeout=300)
    data=_good(end)
    if not data.get('id'):raise UploadError('No YouTube video id returned')
    actual=data.get('status',{}).get('privacyStatus',mode)
    # YouTube may enforce a different visibility from the requested value.
    return {'status':'staged','kind':'youtube_video_submission','id':data['id'],
            'mode_requested':mode,'mode_reported':actual,
            'public_confirmed': actual=='public',
            'watch_url':f'https://www.youtube.com/watch?v={data["id"]}'}

def facebook(path,title,description,config):
    _need('FB_PAGE_ID','FB_PAGE_ACCESS_TOKEN')
    mode=config['platform_modes']['facebook'];_check_public(mode,config['publish_unreviewed'])
    if mode not in ('DRAFT','PUBLISHED'):raise UploadError('Unsupported Facebook mode')
    token=os.environ['FB_PAGE_ACCESS_TOKEN'];page=os.environ['FB_PAGE_ID']
    version=os.getenv('FB_GRAPH_API_VERSION','v25.0')
    base=f'https://graph.facebook.com/{version}/{page}/video_reels'
    auth={'Authorization':'Bearer '+token}
    start=_good(requests.post(base,headers=auth,data={'upload_phase':'start'},timeout=45))
    video_id=start.get('video_id');url=start.get('upload_url')
    if not video_id or not url or not url.startswith('https://rupload.facebook.com/'):
        raise UploadError('Bad Meta Reel upload URL/session')
    size=Path(path).stat().st_size
    with open(path,'rb') as f:
        uploaded=requests.post(url,headers={'Authorization':'OAuth '+token,'offset':'0','file_size':str(size),'Content-Type':'application/octet-stream'},data=f,timeout=300)
    _good(uploaded)
    _good(requests.post(base,headers=auth,data={'upload_phase':'finish','video_id':video_id,'video_state':mode,'title':title,'description':description},timeout=60))
    return {'status':'staged','kind':'facebook_page_reel_draft' if mode=='DRAFT' else 'facebook_page_reel_publish_submitted','id':video_id,'mode':mode}

def _tiktok_access():
    _need('TIKTOK_CLIENT_KEY','TIKTOK_CLIENT_SECRET','DRAMA_TOKEN_KEY')
    from cryptography.fernet import Fernet
    cipher=Fernet(os.environ['DRAMA_TOKEN_KEY'].encode())
    vault=ROOT/'cloud_data'/'tiktok_token.enc'
    if vault.exists():
        refresh=cipher.decrypt(vault.read_bytes()).decode()
    else:
        _need('TIKTOK_REFRESH_TOKEN');refresh=os.environ['TIKTOK_REFRESH_TOKEN']
    data=_good(requests.post('https://open.tiktokapis.com/v2/oauth/token/',data={
        'client_key':os.environ['TIKTOK_CLIENT_KEY'],'client_secret':os.environ['TIKTOK_CLIENT_SECRET'],
        'grant_type':'refresh_token','refresh_token':refresh},headers={'Content-Type':'application/x-www-form-urlencoded'},timeout=45))
    token=data.get('access_token');rotated=data.get('refresh_token')
    if not token or not rotated:raise UploadError('TikTok refresh did not return both tokens')
    vault.write_bytes(cipher.encrypt(rotated.encode()))
    # Persist encrypted rotated refresh token before remote upload, otherwise
    # ephemeral GitHub runner would lose the rotated token each night.
    checkpoint('cloud: encrypted TikTok refresh token rotation')
    return token

def tiktok(path,title,description,config):
    # TikTok no public posts here; inbox only.
    if config['platform_modes']['tiktok']!='inbox':raise UploadError('Only TikTok inbox is implemented; no Direct Post shortcut')
    _need('TIKTOK_CLIENT_KEY','TIKTOK_CLIENT_SECRET','DRAMA_TOKEN_KEY')
    token=_tiktok_access()
    size=Path(path).stat().st_size
    # 1 chunk when <= 64 MiB; renderer under target 60s usually small.
    if size>64*1024*1024:raise UploadError('TikTok uploader currently supports videos <=64MiB')
    data=_good(requests.post('https://open.tiktokapis.com/v2/post/publish/inbox/video/init/',headers={'Authorization':'Bearer '+token},
        json={'source_info':{'source':'FILE_UPLOAD','video_size':size,'chunk_size':size,'total_chunk_count':1}},timeout=45))
    payload=data.get('data',{});url=payload.get('upload_url');publish_id=payload.get('publish_id')
    if not url or not url.startswith('https://open-upload.tiktokapis.com/'):
        raise UploadError('TikTok upload URL not from expected official domain')
    with open(path,'rb') as f:
        res=requests.put(url,data=f,headers={'Content-Type':'video/mp4','Content-Range':f'bytes 0-{size-1}/{size}','Content-Length':str(size)},timeout=300)
    res.raise_for_status()
    return {'status':'staged','kind':'tiktok_inbox_pending_creator_publish','id':publish_id,'mode':'inbox'}

ADAPTERS={'youtube':youtube,'facebook':facebook,'tiktok':tiktok}

def resolved_upload_config(config, platform):
    """Downgrade BEFORE upload when the owner has not unlocked unattended public posting.

    This is a safe preventive fallback, not a blind retry after a possibly successful remote request.
    """
    if platform not in ('youtube','facebook'):
        return config,False
    requested=config['platform_modes'][platform]
    if requested not in ('public','PUBLISHED'):
        return config,False
    authorized=bool(config.get('publish_unreviewed') and os.environ.get('DRAMA_ALLOW_UNREVIEWED_PUBLIC')=='true')
    if authorized:
        return config,False
    fallback={'youtube':'private','facebook':'DRAFT'}[platform]
    return {**config,'platform_modes':{**config['platform_modes'],platform:fallback},'publish_unreviewed':False},True


def upload_all(ep_id,path,title,description,config,only_missing=False,platforms=None,allow_safe_fallback=False):
    queue=read('cloud_data/episode_queue.json')
    queue.setdefault('uploads',{}).setdefault(ep_id,{})
    output={}
    if platforms is not None and any(p not in PLATFORMS for p in platforms):
        raise ValueError('Unknown platform selected')
    for platform in (platforms if platforms is not None else PLATFORMS):
        previous=queue['uploads'][ep_id].get(platform,{})
        if previous.get('status') in ('staged','inflight','needs_reconcile'):
            output[platform]={'status':'not_retried','reason':'Already staged or requires manual reconciliation'};continue
        if only_missing and previous.get('status')!='missing_credentials':continue
        # Downgrade locally before remote calls; prevents an unwanted public post.
        effective_config,downgraded=resolved_upload_config(config,platform) if allow_safe_fallback else (config,False)
        mode=effective_config['platform_modes'][platform]
        if mode in ('public','PUBLISHED') and not (effective_config.get('publish_unreviewed') and os.environ.get('DRAMA_ALLOW_UNREVIEWED_PUBLIC')=='true'):
            receipt={'status':'blocked_public_approval','message':'Use private/draft; public mode requires approved assets and explicit public opt-in','updated_utc':utcnow()}
            queue['uploads'][ep_id][platform]=receipt
            save('cloud_data/episode_queue.json',queue)
            checkpoint(f'cloud: public upload blocked {ep_id} {platform}')
            output[platform]=receipt
            continue
        try:
            # Prevent duplicate public upload on runner termination: checkpoint BEFORE external API.
            queue['uploads'][ep_id][platform]={'status':'inflight','intent_utc':utcnow()}
            save('cloud_data/episode_queue.json',queue)
            checkpoint(f'cloud: upload intent {ep_id} {platform}')
            receipt=ADAPTERS[platform](path,title,description,effective_config)
        except MissingCredentials as e:
            receipt={'status':'missing_credentials','message':str(e)}
        except Exception as e:
            receipt={'status':'needs_reconcile','error':f'{type(e).__name__}: {str(e)[:240]}'}
        if downgraded:
            receipt['fallback_reason']='No public autopublish approval secret: selected private/draft before uploading'
        receipt['updated_utc']=utcnow()
        queue['uploads'][ep_id][platform]=receipt
        save('cloud_data/episode_queue.json',queue)
        checkpoint(f'cloud: upload receipt {ep_id} {platform}')
        output[platform]=receipt
    return output

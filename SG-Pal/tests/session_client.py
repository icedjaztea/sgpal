from fastapi.testclient import TestClient

class SessionClient(TestClient):
    """Test convenience only: real cookies/CSRF, fresh precondition unless overridden."""
    def post(self, url, **kwargs):
        session=self.get('/api/auth/session').json()
        headers={'X-SGPal-CSRF':session['csrf'],'X-SGPal-Owner':session['owner_id']}
        if url in ('/api/adopt','/api/sound','/api/room/place','/api/quests/activate'):
            headers['If-Match']=self.get('/api/state').json().get('revision','unavailable')
        headers.update(kwargs.pop('headers',{}))
        return super().post(url,headers=headers,**kwargs)

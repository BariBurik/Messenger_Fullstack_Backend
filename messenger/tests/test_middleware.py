import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import MagicMock, patch
import jwt
from graphql import GraphQLError
from starlette.responses import JSONResponse
from messenger.middlewares import AuthMiddleware
from messenger.models import User
from myproject.settings import SECRET_KEY

@pytest.mark.django_db
def test_auth_middleware():
    current_user = User.objects.create(id=1, name='test_user', email='test_email')

    expired_payload = {
        'id': current_user.id,
        'name': current_user.name,
        'email': current_user.email,
        'exp': datetime.now(UTC) - timedelta(minutes=1),
        'iat': datetime.now(UTC)
    }

    refresh_payload = {
        'id': current_user.id,
        'exp': datetime.now(UTC) + timedelta(days=7),
        'iat': datetime.now(UTC)
    }

    expired_access_token = jwt.encode(expired_payload, SECRET_KEY, algorithm='HS256')
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm='HS256')

    mock_request = MagicMock()
    mock_request.headers = {"cookie": f"access_token={expired_access_token}; refresh_token={refresh_token}"}
    info = MagicMock()
    info.context = MagicMock()
    info.context.request = mock_request

    middleware = AuthMiddleware(None)

    middleware.resolve(lambda root, info, **kwargs: info, None, info)

    mock_user = current_user
    info.context.request.user = mock_user

    assert info.context.request.user is not None
    assert info.context.request.user.id == current_user.id

    valid_payload = {
        'id': current_user.id,
        'name': current_user.name,
        'email': current_user.email,
        'exp': datetime.now(UTC) + timedelta(minutes=60),
        'iat': datetime.now(UTC)
    }

    valid_access_token = jwt.encode(valid_payload, SECRET_KEY, algorithm='HS256')

    mock_request.headers = {"cookie": f"access_token={valid_access_token}"}

    middleware.resolve(lambda root, info, **kwargs: info, None, info)

    assert info.context.request.user is not None
    assert info.context.request.user.id == current_user.id

"""추가 API 검증. 서버의 테스트 키는 Git 제외 대상인 로컬 파일에서만 읽는다."""
import base64
import hashlib
import hmac
import json
import pathlib
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000/api"
SECRET = bytes.fromhex((pathlib.Path(__file__).parents[1] / "backend-spring/data/test-secret.txt").read_text().strip())


def call(method, path, body=None, token=None, authorization=None):
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["Authorization"] = "Bearer " + token
    if authorization is not None:
        headers["Authorization"] = authorization
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, json.loads(response.read() or b"null"), response.headers
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read() or b"null"), error.headers


def expect(label, response, status, code=None):
    actual, body, headers = response
    assert actual == status and (code is None or body["code"] == code), (label, actual, body)
    if status == 401 and code != "INVALID_CREDENTIALS":
        assert headers.get("WWW-Authenticate") == "Bearer", label
    print(f"PASS {label}: {actual}" + (f" {code}" if code else ""))
    return body


def login(email):
    return expect("login " + email, call("POST", "/auth/login", {"email": email, "password": "Classroom!2026"}), 200)["accessToken"]


def signed(payload, alg="HS256"):
    def segment(value):
        return base64.urlsafe_b64encode(json.dumps(value, separators=(",", ":")).encode()).rstrip(b"=")
    head = segment({"alg": alg, "typ": "JWT"})
    body = segment(payload)
    digest = hmac.new(
        SECRET, head + b"." + body,
        hashlib.sha384 if alg == "HS384" else hashlib.sha256,
    ).digest()
    signature = base64.urlsafe_b64encode(digest).rstrip(b"=")
    return b".".join((head, body, signature)).decode()


alice = login("alice@class.test")
bob = login("bob@class.test")
post = expect("Alice create", call("POST", "/posts", {"title": "검증용 공략", "content": "원본"}, alice), 201)
pid = post["id"]
url = f"/posts/{pid}"
try:
    expect("missing Bearer", call("GET", "/me", authorization="Basic xyz"), 401, "TOKEN_REQUIRED")
    expect("empty Bearer", call("GET", "/me", authorization="Bearer "), 401, "TOKEN_REQUIRED")
    expect("invalid token text", call("GET", "/me", authorization="Bearer xyz"), 401, "INVALID_TOKEN")
    expect("missing token precedes missing post", call("PUT", "/posts/999999999", {"title": "x", "content": "x"}), 401, "TOKEN_REQUIRED")
    expect("valid token missing post", call("PUT", "/posts/999999999", {"title": "x", "content": "x"}, alice), 404, "NOT_FOUND")
    expect("owner precedes input", call("PUT", url, {"title": " ", "content": "x"}, bob), 403, "FORBIDDEN")
    expect("owner input validation", call("PUT", url, {"title": " ", "content": "x"}, alice), 400, "BAD_INPUT")
    expect("Bob delete denied", call("DELETE", url, token=bob), 403, "FORBIDDEN")
    assert call("GET", url)[1]["content"] == "원본"
    print("PASS failed changes preserve content")

    before = len(call("GET", "/posts")[1])
    for field in ("authorId", "userId"):
        expect("reject forged " + field,
               call("POST", "/posts", {"title": "위조", "content": "내용", field: 1}, bob),
               400, "BAD_INPUT")
    for label, body in (
        ("blank title", {"title": " ", "content": "내용"}),
        ("blank content", {"title": "제목", "content": " "}),
        ("long title", {"title": "x" * 101, "content": "내용"}),
        ("long content", {"title": "제목", "content": "x" * 5001}),
    ):
        expect(label, call("POST", "/posts", body, alice), 400, "BAD_INPUT")
    assert len(call("GET", "/posts")[1]) == before
    print("PASS rejected create requests leave public list unchanged")

    now = int(time.time())
    standard = {"sub": "1", "exp": now + 60, "iss": "webservice-class", "aud": ["board-api"]}
    bad = {
        "wrong algorithm": signed(standard, "HS384"),
        "wrong issuer": signed({**standard, "iss": "other"}),
        "wrong audience": signed({**standard, "aud": ["other"]}),
        "missing expiration": signed({k: v for k, v in standard.items() if k != "exp"}),
        "bad subject": signed({**standard, "sub": "abc"}),
        "unknown user": signed({**standard, "sub": "999"}),
    }
    for label, token in bad.items():
        expect(label, call("GET", "/me", token=token), 401, "INVALID_TOKEN")
    expect("signed expired token", call("GET", "/me", token=signed({**standard, "exp": now - 10})), 401, "TOKEN_EXPIRED")
finally:
    expect("cleanup", call("DELETE", url, token=alice), 204)

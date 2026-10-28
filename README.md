# 게임 공략 공유 게시판

게임 플레이 경험을 글로 공유하는 로컬 웹서비스입니다. 누구나 공략을 읽고, Alice/Bob 테스트 계정으로 로그인하면 글을 작성할 수 있습니다. 작성자만 자신의 글을 수정·삭제할 수 있습니다.

작성자: 202012213 안정웅 · GitHub 저장소: https://github.com/onestarluv/webservice2

## 기술과 구조

- Vue 3.5.43 + Vite 8.3.4 (`frontend-vue/`)
- Spring Boot 3.5.16 + Java 17 + JJWT 0.13.0 (`backend-spring/`)
- SQLite 파일 (`backend-spring/data/board.sqlite`), 서버 시작 시 테이블 생성
- 로컬 확인 환경: Windows, Microsoft OpenJDK 17.0.16, Node.js 24.19.0, npm 11.17.0, Python 3.12.11

브라우저 → Vue의 `/api` 요청 → Vite 프록시 → Spring API → SQLite 순서로 동작합니다. JWT는 브라우저 메모리에만 보관하므로 새로고침하면 로그아웃됩니다. 게시글은 DB 파일에 유지됩니다.

## 설치와 실행: Windows PowerShell

JDK 17 이상, Node.js 20.19 이상, Python 3.10 이상을 준비합니다. 최초 Maven/npm 의존성 설치에는 인터넷이 필요합니다. 두 터미널을 사용하고 과제 루트에서 시작합니다.

터미널 A:

```powershell
cd backend-spring
$env:JWT_SECRET = node -e "console.log(require('node:crypto').randomBytes(32).toString('hex'))"
$env:TOKEN_TTL = '90'
.\mvnw.cmd package
java -jar target/jwt-board-1.0.0.jar
```

`JWT_SECRET`은 새로 생성한 64자리 16진수로 설정하세요. 예시 키는 거부됩니다. 실제 키를 Git·보고서에 넣지 마세요. Spring은 `.env`를 자동으로 읽지 않습니다. `JWT_ISSUER` 기본값은 `webservice-class`, `JWT_AUDIENCE` 기본값은 `board-api`입니다. DB 경로는 `DB_FILE`로 변경할 수 있습니다.

터미널 B:

```powershell
cd frontend-vue
npm ci
npm run build
npm run preview
```

브라우저에서 http://127.0.0.1:4173 을 열고 API 상태는 http://127.0.0.1:8000/api/health 에서 확인합니다. 개발 중에는 `frontend-vue`에서 `npm run dev`를 실행하고 5173번 주소를 사용합니다. 소스 변경 후에는 백엔드를 다시 패키징·실행하고 프론트를 다시 빌드합니다. 종료는 각 터미널에서 Ctrl+C입니다.

로그인이 되지 않으면 **먼저 8000번 `/api/health`가 `ok/spring`을 반환하는지** 확인하세요. Spring 서버가 꺼져 있거나 `JWT_SECRET` 설정 오류로 시작하지 못하면 Vite 프록시가 빈 본문의 502를 반환합니다. 화면에는 백엔드 실행 안내가 표시됩니다. 프론트 수정 후 4173번에서 이전 화면이 보이면 preview를 종료하고 `npm run build` → `npm run preview`를 다시 실행하세요.

IntelliJ IDEA의 Spring Boot 실행 구성에서 **Working directory**를 `backend-spring`의 절대 경로로 지정하고 환경변수 `JWT_SECRET=<새로 생성한 64자리 16진수>;TOKEN_TTL=90`을 설정합니다. 실제 키가 공유 설정 파일에 포함되지 않게 확인하세요. DB 상대 경로는 이 Working directory 기준입니다.

테스트 계정: `alice@class.test`, `bob@class.test` / 공통 비밀번호 `Classroom!2026`. DB 초기화가 필요하면 서버를 종료한 뒤 `backend-spring/data/board.sqlite`만 삭제하고 다시 실행합니다. 기존 글은 사라집니다.

## 검증

백엔드 실행 중 루트에서 `python tools/check_api.py --mode final`을 실행합니다. 만료 검사는 백엔드를 종료한 뒤 같은 키와 `TOKEN_TTL=3`으로 재시작하고 `python tools/check_api.py --mode final --expiry`를 실행합니다. 추가 클레임 검사는 로컬 키를 `backend-spring/data/test-secret.txt`에 넣고 `python tools/verify_extended.py`로 재현할 수 있습니다. 키 파일은 Git에서 제외됩니다.

로컬 작업에서 일반 API 검사 40개, 만료 포함 48개, 추가 서명·클레임 검사가 통과했습니다. Vue 빌드 화면에서는 자동 브라우저로 Alice/Bob 로그인·본인 CRUD, 오류 안내, 로그아웃, 새로고침과 만료를 확인했습니다. 이 저장소에는 요청에 따라 `docs/`의 보고서·증거와 `work.md`, `save.md`를 포함하지 않습니다. 과제에서 보고서와 증거를 GitHub에 요구한다면 별도 제출 방법을 확인해야 합니다.

## 구현과 제출

`AuthService`에서 로그인 토큰 발급·검증과 작성자 권한 검사를 합니다. `BoardController`는 검증된 ID를 글 저장에 사용합니다. Vue `api.js`는 메모리 세션과 Bearer 헤더를 처리하고 `App.vue`는 응답별 안내와 작성자 버튼을 처리합니다. 제공 CRUD·SQLite 구조는 유지했습니다.

AI 코딩 도구를 사용해 인증·화면 코드와 추가 검사 스크립트를 작성했습니다. 제출 전 본인이 코드를 검토하고 화면을 직접 확인하세요.

이 저장소에는 `backend-spring/`, `frontend-vue/`, `tools/check_api.py`, `tools/verify_extended.py`, 루트 README와 `.gitignore`만 포함합니다. `.gitignore`는 의존성, 빌드 산출물, DB, 키, IDE 파일과 로컬 문서를 제외합니다. 최종 커밋 SHA는 push 후 `git rev-parse HEAD`로 확인해 LMS에 제출해야 합니다.

let session = { accessToken: "", user: null };
export const getSession = () => session;
export function clearSession() {
  session = { accessToken: "", user: null };
}
function authorizationHeaders() {
  return session.accessToken
    ? { Authorization: `Bearer ${session.accessToken}` }
    : {};
}
export async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`/api${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...authorizationHeaders(),
        ...options.headers,
      },
    });
  } catch {
    throw new Error("서버에 연결할 수 없습니다. Spring 백엔드 실행 상태를 확인해 주세요.");
  }
  let data = null;
  if (response.status !== 204) {
    const body = await response.text();
    if (body) {
      try {
        data = JSON.parse(body);
      } catch {
        // 프록시나 서버가 JSON 대신 HTML·텍스트를 보낼 수 있습니다.
      }
    }
  }
  if (!response.ok) {
    if (response.status === 401) clearSession();
    const error = new Error(
      data?.message || (response.status === 502 || response.status === 503
        ? "Spring 백엔드에 연결할 수 없습니다. 8000번 서버를 실행해 주세요."
        : `요청이 실패했습니다. HTTP ${response.status}`),
    );
    error.status = response.status;
    error.code = data?.code;
    throw error;
  }
  if (response.status !== 204 && data === null)
    throw new Error("서버 응답이 비어 있거나 JSON 형식이 아닙니다. Spring 백엔드를 확인해 주세요.");
  return data;
}
export async function login(email, password) {
  const result = await request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  session = { accessToken: result.accessToken, user: result.user };
  return result.user;
}
export function canEdit(post) {
  return Boolean(session.user && session.user.id === post.authorId);
}
export const api = {
  list: () => request("/posts"),
  detail: (id) => request(`/posts/${id}`),
  create: (input) =>
    request("/posts", { method: "POST", body: JSON.stringify(input) }),
  update: (id, input) =>
    request(`/posts/${id}`, { method: "PUT", body: JSON.stringify(input) }),
  remove: (id) => request(`/posts/${id}`, { method: "DELETE" }),
  me: () => request("/me"),
};

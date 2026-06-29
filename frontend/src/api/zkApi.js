const ZK_API_BASE_URL =
  import.meta.env.VITE_ZK_API_BASE_URL || "http://127.0.0.1:8000/api";

async function request(endpoint, options = {}) {
  const url = `${ZK_API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const message =
      data?.detail?.message ||
      data?.detail ||
      data?.message ||
      `Error HTTP ${response.status}`;

    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }

  return data;
}

export async function getZkHealth() {
  return request("/zk/health");
}

export async function getZkUsers({ includeAdmin = true } = {}) {
  const params = new URLSearchParams();
  params.set("include_admin", String(includeAdmin));

  return request(`/zk/users?${params.toString()}`);
}

export async function getZkUserByUserId(userId) {
  if (!userId) {
    throw new Error("El userId es obligatorio.");
  }

  return request(`/zk/users/${encodeURIComponent(userId)}`);
}
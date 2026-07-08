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

export async function getZkEmployeeReconciliation() {
  return request("/zk/reconciliation/employees");
}

export async function linkEmployeeWithZkUser({ codigoEmpleado, zkUserId }) {
  if (!codigoEmpleado) {
    throw new Error("El código de empleado es obligatorio.");
  }

  if (!zkUserId) {
    throw new Error("El User ID ZKTeco es obligatorio.");
  }

  return request(
    `/zk/reconciliation/employees/${encodeURIComponent(codigoEmpleado)}/link`,
    {
      method: "PATCH",
      body: JSON.stringify({
        zk_user_id: String(zkUserId),
      }),
    }
  );
}

export async function unlinkEmployeeFromZkUser(codigoEmpleado) {
  if (!codigoEmpleado) {
    throw new Error("El código de empleado es obligatorio.");
  }

  return request(
    `/zk/reconciliation/employees/${encodeURIComponent(codigoEmpleado)}/unlink`,
    {
      method: "PATCH",
    }
  );
}
export async function getZkAttendanceRaw({
  limit = 100,
  userId = "",
  dateFrom = "",
  dateTo = "",
} = {}) {
  const params = new URLSearchParams();

  params.set("limit", String(limit));

  if (userId.trim()) {
    params.set("user_id", userId.trim());
  }

  if (dateFrom) {
    params.set("date_from", dateFrom);
  }

  if (dateTo) {
    params.set("date_to", dateTo);
  }

  return request(`/zk/attendance/raw?${params.toString()}`);
}

export async function syncZkAttendanceToDb({
  limit = 1000,
  userId = "",
  dateFrom = "",
  dateTo = "",
} = {}) {
  const params = new URLSearchParams();

  params.set("limit", String(limit));

  if (userId.trim()) {
    params.set("user_id", userId.trim());
  }

  if (dateFrom) {
    params.set("date_from", dateFrom);
  }

  if (dateTo) {
    params.set("date_to", dateTo);
  }

  return request(`/zk/attendance/sync?${params.toString()}`, {
    method: "POST",
  });
}

export async function getZkAttendanceFromDb({
  limit = 100,
  userId = "",
  dateFrom = "",
  dateTo = "",
} = {}) {
  const params = new URLSearchParams();

  params.set("limit", String(limit));

  if (userId.trim()) {
    params.set("user_id", userId.trim());
  }

  if (dateFrom) {
    params.set("date_from", dateFrom);
  }

  if (dateTo) {
    params.set("date_to", dateTo);
  }

  return request(`/zk/attendance/db?${params.toString()}`);
}
export async function syncZkTime({ force = false } = {}) {
  const params = new URLSearchParams();

  if (force) {
    params.set("force", "true");
  }

  const queryString = params.toString();

  return request(
    `/zk/time/sync${queryString ? `?${queryString}` : ""}`,
    {
      method: "POST",
    }
  );
}
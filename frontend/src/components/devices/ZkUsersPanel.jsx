import { useEffect, useMemo, useState } from "react";
import { getZkHealth, getZkUsers } from "../../api/zkApi";

export default function ZkUsersPanel() {
  const [users, setUsers] = useState([]);
  const [health, setHealth] = useState(null);
  const [includeAdmin, setIncludeAdmin] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadZkData() {
    setLoading(true);
    setError("");

    try {
      const [healthResponse, usersResponse] = await Promise.all([
        getZkHealth(),
        getZkUsers({ includeAdmin }),
      ]);

      setHealth(healthResponse);
      setUsers(usersResponse.users || []);
    } catch (err) {
      setError(err.message || "No se pudo consultar el reloj ZKTeco.");
      setHealth(null);
      setUsers([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadZkData();
  }, [includeAdmin]);

  const filteredUsers = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();

    if (!term) return users;

    return users.filter((user) => {
      return (
        String(user.uid).toLowerCase().includes(term) ||
        String(user.user_id).toLowerCase().includes(term) ||
        String(user.name).toLowerCase().includes(term) ||
        String(user.privilege).toLowerCase().includes(term)
      );
    });
  }, [users, searchTerm]);

  return (
    <section className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-800">
            Usuarios del reloj ZKTeco
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Lectura directa desde el dispositivo. Esta vista no crea, edita ni borra usuarios.
          </p>
        </div>

        <button
          type="button"
          onClick={loadZkData}
          disabled={loading}
          className="px-4 py-2 rounded-xl bg-slate-900 text-white text-sm font-medium disabled:opacity-60"
        >
          {loading ? "Actualizando..." : "Actualizar"}
        </button>
      </div>

      <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Estado conexión</p>
          <p className="text-lg font-semibold text-slate-800">
            {health?.ok ? "Conectado" : "Sin validar"}
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Usuarios detectados</p>
          <p className="text-lg font-semibold text-slate-800">
            {users.length}
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Modo</p>
          <p className="text-lg font-semibold text-slate-800">
            Solo lectura
          </p>
        </div>
      </div>

      <div className="mt-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <input
          type="text"
          placeholder="Buscar por UID, User ID, nombre o privilegio..."
          value={searchTerm}
          onChange={(event) => setSearchTerm(event.target.value)}
          className="w-full md:max-w-md px-4 py-2 rounded-xl border border-slate-300 text-sm outline-none focus:ring-2 focus:ring-slate-300"
        />

        <label className="flex items-center gap-2 text-sm text-slate-600">
          <input
            type="checkbox"
            checked={includeAdmin}
            onChange={(event) => setIncludeAdmin(event.target.checked)}
          />
          Incluir usuario admin
        </label>
      </div>

      {error && (
        <div className="mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="mt-5 overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50 text-left text-slate-600">
              <th className="px-4 py-3 font-semibold">UID</th>
              <th className="px-4 py-3 font-semibold">User ID</th>
              <th className="px-4 py-3 font-semibold">Nombre</th>
              <th className="px-4 py-3 font-semibold">Privilegio</th>
              <th className="px-4 py-3 font-semibold">PIN</th>
              <th className="px-4 py-3 font-semibold">Protegido</th>
              <th className="px-4 py-3 font-semibold">Grupo</th>
            </tr>
          </thead>

          <tbody>
            {filteredUsers.map((user) => (
              <tr
                key={`${user.uid}-${user.user_id}`}
                className="border-b border-slate-100 hover:bg-slate-50"
              >
                <td className="px-4 py-3 text-slate-700">{user.uid}</td>
                <td className="px-4 py-3 text-slate-700">{user.user_id}</td>
                <td className="px-4 py-3 font-medium text-slate-800">
                  {user.name || "Sin nombre"}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={
                      user.is_admin
                        ? "inline-flex rounded-full bg-amber-100 px-2 py-1 text-xs font-medium text-amber-700"
                        : "inline-flex rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700"
                    }
                  >
                    {user.privilege}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {user.has_pin ? "Sí" : "No"}
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {user.is_protected ? "Sí" : "No"}
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {user.group_id || "-"}
                </td>
              </tr>
            ))}

            {!loading && filteredUsers.length === 0 && (
              <tr>
                <td colSpan="7" className="px-4 py-8 text-center text-slate-500">
                  No se encontraron usuarios.
                </td>
              </tr>
            )}

            {loading && (
              <tr>
                <td colSpan="7" className="px-4 py-8 text-center text-slate-500">
                  Cargando usuarios del reloj...
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
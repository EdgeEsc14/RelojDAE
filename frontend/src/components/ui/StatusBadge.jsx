function getBadgeClass(status) {
  const normalized = String(status).toLowerCase();

  if (
    normalized.includes("activo") ||
    normalized.includes("activa") ||
    normalized.includes("conectado") ||
    normalized.includes("correcto") ||
    normalized.includes("aprobada") ||
    normalized.includes("vigente") ||
    normalized.includes("completo")
  ) {
    return "badge success";
  }

  if (
    normalized.includes("pendiente") ||
    normalized.includes("revisar") ||
    normalized.includes("advertencia") ||
    normalized.includes("retardo") ||
    normalized.includes("media")
  ) {
    return "badge warning";
  }

  if (
    normalized.includes("bloqueado") ||
    normalized.includes("desconectado") ||
    normalized.includes("rechazada") ||
    normalized.includes("falta") ||
    normalized.includes("error") ||
    normalized.includes("alta") ||
    normalized.includes("sin justificar")
  ) {
    return "badge danger";
  }

  return "badge neutral";
}

function StatusBadge({ status }) {
  return <span className={getBadgeClass(status)}>{status}</span>;
}

export default StatusBadge;
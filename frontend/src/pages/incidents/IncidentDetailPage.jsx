import { useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  FileText,
  User,
  XCircle,
} from "lucide-react";

import PageHeader from "../../components/layout/PageHeader";
import { getIncidencia, revisarIncidencia } from "../../api/incidenciasApi";

function getStatusClass(estatus) {
  const s = (estatus || "").toUpperCase();
  if (s === "PENDIENTE") return "badge warning";
  if (s === "SIN_JUSTIFICAR") return "badge danger";
  if (s === "JUSTIFICADA") return "badge success";
  if (s === "APROBADA") return "badge success";
  if (s === "RECHAZADA") return "badge danger";
  if (s === "CANCELADA") return "badge neutral";
  return "badge neutral";
}

function getStatusLabel(estatus) {
  const labels = {
    PENDIENTE: "Pendiente",
    SIN_JUSTIFICAR: "Sin justificar",
    JUSTIFICADA: "Justificada",
    APROBADA: "Aprobada",
    RECHAZADA: "Rechazada",
    CANCELADA: "Cancelada",
  };
  return labels[(estatus || "").toUpperCase()] || estatus || "";
}

function formatDate(value) {
  if (!value) return "—";
  try {
    const d = new Date(value + "T00:00:00");
    return d.toLocaleDateString("es-MX", { day: "2-digit", month: "long", year: "numeric" });
  } catch {
    return value;
  }
}

function formatDateTime(value) {
  if (!value) return "—";
  try {
    const d = new Date(value);
    return d.toLocaleString("es-MX", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return value;
  }
}

function IncidentDetailPage() {
  const { incidentId } = useParams();
  const navigate = useNavigate();

  const [incidencia, setIncidencia] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Review form
  const [comentario, setComentario] = useState("");
  const [reviewLoading, setReviewLoading] = useState(false);
  const [reviewError, setReviewError] = useState("");

  useEffect(() => {
    loadIncidencia();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [incidentId]);

  async function loadIncidencia() {
    setLoading(true);
    setError("");
    try {
      const data = await getIncidencia(incidentId);
      setIncidencia(data);
    } catch (err) {
      setError(err.message || "Error al cargar la incidencia.");
    } finally {
      setLoading(false);
    }
  }

  async function handleReview(nuevoEstatus) {
    setReviewLoading(true);
    setReviewError("");
    try {
      await revisarIncidencia(incidentId, {
        estatus: nuevoEstatus,
        comentario_revision: comentario || null,
      });
      // Recargar datos
      await loadIncidencia();
      setComentario("");
    } catch (err) {
      setReviewError(err.message || "Error al procesar la revisión.");
    } finally {
      setReviewLoading(false);
    }
  }

  const canReview =
    incidencia &&
    (incidencia.estatus === "PENDIENTE" || incidencia.estatus === "SIN_JUSTIFICAR");

  return (
    <div className="page-stack">
      <PageHeader
        title="Detalle de incidencia"
        description={incidencia ? `#${incidencia.id} — ${incidencia.tipo_nombre}` : "Cargando..."}
      >
        <div className="header-actions">
          <Link className="secondary-button link-button" to="/incidents">
            <ArrowLeft size={17} />
            Volver
          </Link>
        </div>
      </PageHeader>

      {error && (
        <div className="panel-card">
          <div className="empty-state">
            <h3>Error</h3>
            <p>{error}</p>
          </div>
        </div>
      )}

      {loading && (
        <div className="panel-card">
          <div className="empty-state">
            <h3>Cargando...</h3>
            <p>Obteniendo detalle de la incidencia.</p>
          </div>
        </div>
      )}

      {!loading && incidencia && (
        <>
          {/* Info principal */}
          <section className="panel-card">
            <div className="panel-header">
              <div>
                <h3>Información de la incidencia</h3>
                <p>
                  <span className={getStatusClass(incidencia.estatus)}>
                    {getStatusLabel(incidencia.estatus)}
                  </span>
                </p>
              </div>
              <FileText size={22} />
            </div>

            <div className="report-info-grid">
              <div>
                <span>Tipo</span>
                <strong>{incidencia.tipo_nombre}</strong>
              </div>
              <div>
                <span>Categoría</span>
                <strong>{incidencia.tipo_categoria}</strong>
              </div>
              <div>
                <span>Fecha</span>
                <strong>{formatDate(incidencia.fecha)}</strong>
              </div>
              <div>
                <span>Origen</span>
                <strong>{incidencia.origen === "PROCESAMIENTO" ? "Automático" : "Manual"}</strong>
              </div>
              <div>
                <span>Puntos originales</span>
                <strong>{incidencia.puntos_originales}</strong>
              </div>
              <div>
                <span>Puntos justificados</span>
                <strong>{incidencia.puntos_justificados}</strong>
              </div>
              <div>
                <span>Puntos efectivos</span>
                <strong>{incidencia.puntos_efectivos}</strong>
              </div>
              <div>
                <span>Requiere revisión</span>
                <strong>{incidencia.requiere_revision ? "Sí" : "No"}</strong>
              </div>
            </div>

            {incidencia.descripcion && (
              <div className="report-info-grid" style={{ marginTop: "1rem" }}>
                <div style={{ gridColumn: "1 / -1" }}>
                  <span>Descripción</span>
                  <strong>{incidencia.descripcion}</strong>
                </div>
              </div>
            )}
          </section>

          {/* Empleado */}
          <section className="panel-card">
            <div className="panel-header">
              <div>
                <h3>Empleado</h3>
              </div>
              <User size={22} />
            </div>

            <div className="report-info-grid">
              <div>
                <span>Código</span>
                <strong>{incidencia.codigo_empleado}</strong>
              </div>
              <div>
                <span>Nombre</span>
                <strong>{incidencia.nombre_empleado}</strong>
              </div>
              <div>
                <span>Departamento</span>
                <strong>{incidencia.departamento || "Sin departamento"}</strong>
              </div>
            </div>
          </section>

          {/* Revisión */}
          {incidencia.fecha_revision && (
            <section className="panel-card">
              <div className="panel-header">
                <div>
                  <h3>Resolución</h3>
                </div>
                <Calendar size={22} />
              </div>

              <div className="report-info-grid">
                <div>
                  <span>Fecha de revisión</span>
                  <strong>{formatDateTime(incidencia.fecha_revision)}</strong>
                </div>
                {incidencia.comentario_revision && (
                  <div style={{ gridColumn: "1 / -1" }}>
                    <span>Comentario</span>
                    <strong>{incidencia.comentario_revision}</strong>
                  </div>
                )}
              </div>
            </section>
          )}

          {/* Formulario de revisión */}
          {canReview && (
            <section className="panel-card">
              <div className="panel-header">
                <div>
                  <h3>Revisar incidencia</h3>
                  <p>Aprobar, rechazar o cancelar esta incidencia.</p>
                </div>
                <Clock size={22} />
              </div>

              {reviewError && (
                <div className="form-error-message">{reviewError}</div>
              )}

              <div className="form-field" style={{ marginTop: "0.5rem" }}>
                <label htmlFor="review-comment">Comentario de revisión</label>
                <textarea
                  id="review-comment"
                  rows={3}
                  placeholder="Observaciones sobre la resolución (opcional)..."
                  value={comentario}
                  onChange={(e) => setComentario(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    border: "1px solid #d8d1d4",
                    borderRadius: "8px",
                    fontFamily: "inherit",
                    fontSize: "0.9rem",
                    resize: "vertical",
                  }}
                />
              </div>

              <div className="modal-footer" style={{ borderTop: "none", paddingTop: "12px" }}>
                <button
                  className="secondary-button"
                  type="button"
                  disabled={reviewLoading}
                  onClick={() => handleReview("CANCELADA")}
                >
                  <XCircle size={17} />
                  Cancelar incidencia
                </button>

                <button
                  className="secondary-button"
                  type="button"
                  disabled={reviewLoading}
                  onClick={() => handleReview("RECHAZADA")}
                  style={{ color: "#dc2626", borderColor: "#fecaca" }}
                >
                  <XCircle size={17} />
                  Rechazar
                </button>

                <button
                  className="primary-button"
                  type="button"
                  disabled={reviewLoading}
                  onClick={() => handleReview("APROBADA")}
                >
                  <CheckCircle2 size={17} />
                  {reviewLoading ? "Procesando..." : "Aprobar"}
                </button>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}

export default IncidentDetailPage;

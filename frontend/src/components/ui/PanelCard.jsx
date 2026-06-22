function PanelCard({ title, description, icon: Icon, children }) {
  return (
    <section className="panel-card">
      {(title || description || Icon) && (
        <div className="panel-header">
          <div>
            {title && <h3>{title}</h3>}
            {description && <p>{description}</p>}
          </div>

          {Icon && <Icon size={22} />}
        </div>
      )}

      {children}
    </section>
  );
}

export default PanelCard;
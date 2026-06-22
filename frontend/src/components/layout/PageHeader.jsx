function PageHeader({ title, description, children }) {
  return (
    <div className="page-header">
      <div>
        <h2>{title}</h2>
        {description && <p>{description}</p>}
      </div>

      {children && <div className="page-header-actions">{children}</div>}
    </div>
  );
}

export default PageHeader;
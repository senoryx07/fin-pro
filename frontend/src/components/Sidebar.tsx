type SidebarProps = {
  activePage: string;
};

function Sidebar({ activePage }: SidebarProps) {
  const menuItems = [
    { id: "home", label: "Home", icon: "⌂" },
    { id: "research", label: "Research", icon: "⌕" },
    { id: "markets", label: "Markets", icon: "◈" },
  ];

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">F</div>

        <div>
          <div className="brand-name">FIN PRO</div>
          <div className="brand-subtitle">Financial Research</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-title">WORKSPACE</div>

        {menuItems.map((item) => (
          <a
            key={item.id}
            href={`#/${item.id}`}
            className={`nav-item ${
              activePage === item.id ? "active" : ""
            }`}
          >
            <span className="nav-icon">{item.icon}</span>
            <span>{item.label}</span>
          </a>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <div className="system-status">
          <span className="status-dot"></span>

          <div>
            <div className="status-title">NSE Data</div>
            <div className="status-subtitle">End-of-day prices</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;

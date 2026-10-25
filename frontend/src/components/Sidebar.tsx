type SidebarProps = {
  activePage: string;
  setActivePage: (page: string) => void;
};

function Sidebar({ activePage, setActivePage }: SidebarProps) {
  const menuItems = [
    { id: "home", label: "Home", icon: "⌂" },
    { id: "research", label: "Research", icon: "⌕" },
    { id: "markets", label: "Markets", icon: "◈" },
    { id: "compare", label: "Compare", icon: "⇄" },
    { id: "reports", label: "Reports", icon: "▤" },
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
          <button
            key={item.id}
            className={`nav-item ${
              activePage === item.id ? "active" : ""
            }`}
            onClick={() => setActivePage(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <button className="nav-item">
          <span className="nav-icon">⚙</span>
          <span>Settings</span>
        </button>

        <div className="system-status">
          <span className="status-dot"></span>

          <div>
            <div className="status-title">System Ready</div>
            <div className="status-subtitle">Research Engine</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
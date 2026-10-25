function TopBar() {
  return (
    <header className="topbar">
      <div className="breadcrumb">
        <span>FIN PRO</span>
        <span className="breadcrumb-separator">/</span>
        <span className="breadcrumb-current">Research Terminal</span>
      </div>

      <div className="topbar-actions">
        <button className="search-button">
          <span className="search-icon">⌕</span>
          <span>Search company</span>
          <span className="search-shortcut">⌘ K</span>
        </button>

        <div className="topbar-divider"></div>

        <button className="icon-button" title="Notifications">
          ♢
        </button>

        <div className="profile">
          <div className="profile-avatar">FP</div>
        </div>
      </div>
    </header>
  );
}

export default TopBar;
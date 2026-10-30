function TopBar() {
  return (
    <header className="topbar">
      <div className="breadcrumb">
        <span>FIN PRO</span>
        <span className="breadcrumb-separator">/</span>
        <span className="breadcrumb-current">Research Terminal</span>
      </div>

      {/* Replaces the sidebar on narrow screens. */}
      <nav className="mobile-nav">
        <a href="#/home">Home</a>
        <a href="#/research">Research</a>
        <a href="#/markets">Markets</a>
      </nav>

      <div className="topbar-actions">
        <a className="search-button" href="#/research">
          <span className="search-icon">⌕</span>
          <span>Search company</span>
        </a>
      </div>
    </header>
  );
}

export default TopBar;

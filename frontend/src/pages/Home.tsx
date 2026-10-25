function Home() {
  return (
    <section className="home-page">
      <div className="hero-section">
        <div className="eyebrow">FINANCIAL RESEARCH TERMINAL</div>

        <h1>
          Understand the business
          <br />
          behind the numbers.
        </h1>

        <p className="hero-description">
          Research companies, industries, financial performance, valuation
          and market behaviour from one place.
        </p>

        <div className="hero-search">
          <span className="hero-search-icon">⌕</span>

          <input
            type="text"
            placeholder="Search a company, ticker or industry..."
          />

          <span className="hero-search-hint">ENTER</span>
        </div>
      </div>

      <div className="section-heading">
        <div>
          <h2>Research Workspace</h2>
          <p>Start by selecting a company to analyse.</p>
        </div>
      </div>

      <div className="research-cards">
        <div className="research-card">
          <div className="card-number">01</div>
          <div className="card-icon">◉</div>
          <h3>Company Research</h3>
          <p>
            Explore a company's business, management, industry, financials
            and market position.
          </p>
        </div>

        <div className="research-card">
          <div className="card-number">02</div>
          <div className="card-icon">▥</div>
          <h3>Fundamental Analysis</h3>
          <p>
            Examine financial statements, growth, profitability, leverage
            and operating performance.
          </p>
        </div>

        <div className="research-card">
          <div className="card-number">03</div>
          <div className="card-icon">⌁</div>
          <h3>Market Analysis</h3>
          <p>
            Study price behaviour, technical indicators, volatility and
            historical market data.
          </p>
        </div>
      </div>

      <div className="home-footer-note">
        <span className="status-dot"></span>
        <span>Research environment initialized</span>
      </div>
    </section>
  );
}

export default Home;
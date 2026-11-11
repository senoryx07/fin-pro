import DataNotice from "./components/DataNotice";
import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";
import Home from "./pages/Home";
import Markets from "./pages/Markets";
import Research from "./pages/Research";
import { useRoute } from "./utils/router";
import "./styles/app.css";
import "./styles/site.css";

function App() {
  const [page = "home", ticker, tab] = useRoute();

  const renderPage = () => {
    switch (page) {
      case "research":
        return <Research ticker={ticker} tab={tab} />;
      case "markets":
        return <Markets />;
      case "home":
      default:
        return <Home />;
    }
  };

  return (
    <div className="app-shell">
      <Sidebar activePage={page} />

      <div className="main-area">
        <TopBar />
        <DataNotice />
        <main className="page-content">
          {/* Keyed by route so each page and tab animates in. */}
          <div className="page-enter" key={`${page}/${ticker ?? ""}/${tab ?? ""}`}>
            {renderPage()}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;

import { useState } from "react";
import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";
import Home from "./pages/Home";
import Research from "./pages/Research";
import "./styles/app.css";

function App() {
  const [activePage, setActivePage] = useState("home");

  const renderPage = () => {
    switch (activePage) {
      case "research":
        return <Research />;
      case "home":
      default:
        return <Home />;
    }
  };

  return (
    <div className="app-shell">
      <Sidebar activePage={activePage} setActivePage={setActivePage} />

      <div className="main-area">
        <TopBar />
        <main className="page-content">{renderPage()}</main>
      </div>
    </div>
  );
}

export default App;
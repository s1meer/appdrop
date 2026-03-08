import { useState } from "react";
import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";
import AppStore from "./pages/AppStore";
import MyApps from "./pages/MyApps";
import Settings from "./pages/Settings";
import InstallModal from "./components/InstallModal";

export type Page = "store" | "myapps" | "settings";
export type Theme = "dark" | "light";

export default function App() {
  const [page, setPage] = useState<Page>("myapps");
  const [theme, setTheme] = useState<Theme>("dark");
  const [showInstallModal, setShowInstallModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const toggleTheme = () => setTheme(t => t === "dark" ? "light" : "dark");

  return (
    <div className={theme} style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <div className={`app-root ${theme}`} style={{ flex: 1, display: "flex", overflow: "hidden" }}>
        <Sidebar page={page} setPage={setPage} theme={theme} />
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <TopBar
            page={page}
            theme={theme}
            toggleTheme={toggleTheme}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            onInstallFromURL={() => setShowInstallModal(true)}
          />
          <main style={{ flex: 1, overflow: "auto" }}>
            {page === "myapps" && <MyApps theme={theme} searchQuery={searchQuery} />}
            {page === "store" && <AppStore theme={theme} searchQuery={searchQuery} />}
            {page === "settings" && <Settings theme={theme} />}
          </main>
        </div>
      </div>
      {showInstallModal && (
        <InstallModal theme={theme} onClose={() => setShowInstallModal(false)} />
      )}
    </div>
  );
}

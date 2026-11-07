import { Brand } from "./components/brand";
import { SearchApp } from "./components/search-app";

export default function Home() {
  return (
    <main>
      <header className="siteHeader">
        <Brand />
        <div className="systemBadge"><span /> HYBRID ENGINE ONLINE</div>
      </header>
      <SearchApp />
    </main>
  );
}

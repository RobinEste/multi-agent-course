import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { TopNav } from "./components/TopNav";
import { About } from "./sections/About";
import { Scope } from "./sections/Scope";
import { Live } from "./sections/Live";
import { useStatus } from "./lib/status";

type Section = "about" | "scope" | "live";

export default function App() {
  const status = useStatus();
  const [section, setSection] = useState<Section>("about");
  const [userLocked, setUserLocked] = useState(false);

  // Auto-advance to Live once the run has begun — unless the user has
  // navigated manually (e.g. back to About for a second explanation).
  useEffect(() => {
    if (userLocked) return;
    if (status.phase === "idle") return;
    if (status.phase === "waiting-for-scope") {
      setSection("scope");
      return;
    }
    setSection("live");
  }, [status.phase, userLocked]);

  const handleNav = (next: Section) => {
    setUserLocked(true);
    setSection(next);
  };

  return (
    <div className="min-h-screen">
      <TopNav section={section} onChange={handleNav} status={status} />
      <main className="max-w-[1240px] mx-auto px-6 pb-24">
        <AnimatePresence mode="wait">
          <motion.div
            key={section}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.22, ease: [0.2, 0.8, 0.2, 1] }}
          >
            {section === "about" && <About onStart={() => handleNav("scope")} />}
            {section === "scope" && <Scope onSubmitted={() => handleNav("live")} status={status} />}
            {section === "live" && <Live status={status} />}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}

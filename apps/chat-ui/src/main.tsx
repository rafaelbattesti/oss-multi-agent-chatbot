import { createRoot } from "react-dom/client"

import "./index.css"
import { LocalRuntimeProvider } from "./App.tsx"
import { ThemeProvider } from "@/components/theme-provider.tsx"
import { Thread } from "@/components/assistant-ui/thread";

createRoot(document.getElementById("root")!).render(
  <LocalRuntimeProvider>
    <ThemeProvider>
      <Thread />
    </ThemeProvider>
  </LocalRuntimeProvider>
)

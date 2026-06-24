import { A2ARuntimeProvider } from "./runtime";
import { Thread } from "@/components/assistant-ui/thread";

export default async function Page() {
  const a2aBaseUrl = process.env.NEXT_PUBLIC_A2A_BASE_URL || "http://localhost:9999";

  return (
    <A2ARuntimeProvider baseUrl={a2aBaseUrl}>
      <Thread />
    </A2ARuntimeProvider>
  );
}

import { Thread } from "@/components/assistant-ui/thread";
import { A2ARuntimeProvider } from "./runtime";

export default function Page() {
  return (
    <A2ARuntimeProvider>
      <Thread />
    </A2ARuntimeProvider>
  );
}
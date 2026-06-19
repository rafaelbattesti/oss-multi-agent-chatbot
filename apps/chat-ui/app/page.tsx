import { A2ARuntimeProvider } from "./runtime";
import { Thread } from "@/components/assistant-ui/thread";

export default function Page() {
  return (
    <A2ARuntimeProvider>
      <Thread />
    </A2ARuntimeProvider>
  );
}
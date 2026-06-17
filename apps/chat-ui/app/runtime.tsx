"use client";

import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { useA2ARuntime } from "@assistant-ui/react-a2a";

export function A2ARuntimeProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const runtime = useA2ARuntime({
    baseUrl: "http://localhost:9999",
  });
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {children}
    </AssistantRuntimeProvider>
  );
}
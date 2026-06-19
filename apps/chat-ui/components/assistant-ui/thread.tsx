"use client";

import {
  ArrowUpIcon,
  BotIcon,
  CheckIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CopyIcon,
  DownloadIcon,
  LoaderIcon,
  PencilIcon,
  RefreshCwIcon,
  SquareIcon,
  ThumbsDownIcon,
  ThumbsUpIcon,
  UserIcon,
} from "lucide-react";
import {
  ActionBarPrimitive,
  AuiIf,
  BranchPickerPrimitive,
  ComposerPrimitive,
  ErrorPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
} from "@assistant-ui/react";
import { useA2AArtifacts } from "@assistant-ui/react-a2a";
import "@assistant-ui/react-markdown/styles/dot.css";

import { Button } from "@/components/ui/button";
import { TooltipIconButton } from "@/components/assistant-ui/tooltip-icon-button";
import { MarkdownText } from "@/components/assistant-ui/markdown-text";
import { ToolFallback } from "@/components/assistant-ui/tool-fallback";
import {
  ComposerAddAttachment,
  ComposerAttachments,
  UserMessageAttachments,
} from "@/components/assistant-ui/attachment";
import { cn } from "@/lib/utils";

const DECOMPOSE_QUERY_ARTIFACT = "decompose-query" as const;

type DecompositionData = {
  intent: string;
  subject: string;
  entities: string[];
  complexity: "simple" | "medium" | "complex";
  sub_queries: string[];
};
export function Thread() {
  return (
    <ThreadPrimitive.Root
      className="flex h-full flex-col bg-background text-base"
      style={{
        ["--thread-max-width" as string]: "48rem",
        ["--accent-color" as string]: "#10a37f",
        ["--accent-foreground" as string]: "#ffffff",
      }}
    >
      <ThreadPrimitive.Viewport
        turnAnchor="top"
        className="relative flex flex-1 flex-col overflow-x-auto overflow-y-scroll scroll-smooth px-4 pt-4"
      >
        <AuiIf condition={(s) => s.thread.isEmpty}>
          <ThreadWelcome />
        </AuiIf>

        <ThreadPrimitive.Messages
          components={{
            UserMessage,
            EditComposer,
            AssistantMessage,
          }}
        />

        <ThreadPrimitive.ViewportFooter className="sticky bottom-0 mx-auto mt-auto flex w-full max-w-[var(--thread-max-width)] flex-col gap-4 overflow-visible rounded-t-3xl bg-background pb-4">
          
          <Composer />
        </ThreadPrimitive.ViewportFooter>
      </ThreadPrimitive.Viewport>
    </ThreadPrimitive.Root>
  );
}
function ThreadWelcome() {
  return (
    <div className="mx-auto my-auto flex w-full max-w-[var(--thread-max-width)] flex-grow flex-col">
      <div className="flex w-full flex-grow flex-col items-center justify-center">
        <div className="flex size-full flex-col justify-center px-8">
          <div className="text-2xl font-semibold">Hello there!</div>
          <div className="text-2xl text-muted-foreground/65">
            How can I help you today?
          </div>
        </div>
      </div>
      
    </div>
  );
}

function Composer() {
  return (
    <ComposerPrimitive.Root className="relative flex w-full flex-col">
      <ComposerPrimitive.AttachmentDropzone className="flex w-full flex-col rounded-3xl border border-input bg-background px-1 pt-2 outline-none transition-shadow has-[textarea:focus-visible]:border-ring has-[textarea:focus-visible]:ring-2 has-[textarea:focus-visible]:ring-ring/20 data-[dragging=true]:border-ring data-[dragging=true]:border-dashed data-[dragging=true]:bg-accent/50">
        <ComposerAttachments />
        <ComposerPrimitive.Input
          placeholder="Send a message..."
          className="mb-1 max-h-32 min-h-14 w-full resize-none bg-transparent px-4 pt-2 pb-3 text-sm outline-none placeholder:text-muted-foreground focus-visible:ring-0"
          rows={1}
          autoFocus
          aria-label="Message input"
        />
        <ComposerAction />
      </ComposerPrimitive.AttachmentDropzone>
    </ComposerPrimitive.Root>
  );
}

function ComposerAction() {
  return (
    <div className="relative mx-2 mb-2 flex items-center justify-between">
      <ComposerAddAttachment />

      <AuiIf condition={(s) => !s.thread.isRunning}>
        <ComposerPrimitive.Send asChild>
          <TooltipIconButton
            tooltip="Send message"
            side="bottom"
            type="submit"
            variant="default"
            size="icon"
            className="size-8 rounded-full"
            style={{
              backgroundColor: "var(--accent-color)",
              color: "var(--accent-foreground)",
            }}
            aria-label="Send message"
          >
            <ArrowUpIcon className="size-4" />
          </TooltipIconButton>
        </ComposerPrimitive.Send>
      </AuiIf>

      <AuiIf condition={(s) => s.thread.isRunning}>
        <ComposerPrimitive.Cancel asChild>
          <Button
            type="button"
            variant="default"
            size="icon"
            className="size-8 rounded-full"
            style={{
              backgroundColor: "var(--accent-color)",
              color: "var(--accent-foreground)",
            }}
            aria-label="Stop generating"
          >
            <SquareIcon className="size-3 fill-current" />
          </Button>
        </ComposerPrimitive.Cancel>
      </AuiIf>
    </div>
  );
}

function UserMessage() {
  return (
    <MessagePrimitive.Root
      className="mx-auto grid w-full max-w-[var(--thread-max-width)] auto-rows-auto grid-cols-[minmax(72px,1fr)_auto] content-start gap-y-2 px-2 py-4 fade-in slide-in-from-bottom-1 animate-in duration-150"
      data-role="user"
    >
      <UserMessageAttachments />

      <div className="relative col-start-2 min-w-0">
        <div className="rounded-3xl bg-muted px-4 py-2.5 break-words text-foreground">
          <MessagePrimitive.Parts />
        </div>
        <div className="absolute top-1/2 left-0 -translate-x-full -translate-y-1/2 pr-2">
          <UserActionBar />
        </div>
      </div>

      <BranchPicker className="col-span-full col-start-1 row-start-3 -mr-1 justify-end" />
    </MessagePrimitive.Root>
  );
}

function UserActionBar() {
  return (
    <ActionBarPrimitive.Root
      hideWhenRunning
      autohide="not-last"
      className="flex flex-col items-end"
    >
      <ActionBarPrimitive.Edit asChild>
        <TooltipIconButton tooltip="Edit" className="p-4">
          <PencilIcon />
        </TooltipIconButton>
      </ActionBarPrimitive.Edit>
    </ActionBarPrimitive.Root>
  );
}

function EditComposer() {
  return (
    <MessagePrimitive.Root className="mx-auto flex w-full max-w-[var(--thread-max-width)] flex-col px-2 py-3">
      <ComposerPrimitive.Root className="ml-auto flex w-full max-w-[85%] flex-col rounded-3xl bg-muted">
        <ComposerPrimitive.Input
          className="min-h-14 w-full resize-none bg-transparent p-4 text-foreground text-sm outline-none"
          autoFocus
        />
        <div className="mx-3 mb-3 flex items-center gap-2 self-end">
          <ComposerPrimitive.Cancel asChild>
            <Button variant="ghost" size="sm">Cancel</Button>
          </ComposerPrimitive.Cancel>
          <ComposerPrimitive.Send asChild>
            <Button size="sm">Update</Button>
          </ComposerPrimitive.Send>
        </div>
      </ComposerPrimitive.Root>
    </MessagePrimitive.Root>
  );
}

function AssistantMessage() {
  const artifacts = useA2AArtifacts();
  const decomposition = artifacts
    ?.find((a) => a.name === DECOMPOSE_QUERY_ARTIFACT)
    ?.parts.find((p) => p.data != null)?.data as DecompositionData | undefined;

  return (
    <MessagePrimitive.Root
      className="relative mx-auto w-full max-w-[var(--thread-max-width)] py-4 fade-in slide-in-from-bottom-1 animate-in duration-150"
      data-role="assistant"
    >
      <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
        <BotIcon className="size-4" />
      </div>
      <div className="break-words px-2 leading-relaxed text-foreground">
        {decomposition ? (
          <DecompositionCard data={decomposition} />
        ) : (
          <MessagePrimitive.Parts
            components={{
              Text: MarkdownText,
              tools: { Fallback: ToolFallback },
            }}
          />
        )}
        <MessageError />
        <AuiIf condition={(s) => s.thread.isRunning && s.message.content.length === 0}>
          <div className="flex items-center gap-2 text-muted-foreground">
            <LoaderIcon className="size-4 animate-spin" />
            <span className="text-sm">Thinking...</span>
          </div>
        </AuiIf>
      </div>

      <div className="mt-1 ml-2 flex min-h-6 items-center">
        <BranchPicker />
        <AssistantActionBar />
      </div>
    </MessagePrimitive.Root>
  );
}

function DecompositionCard({ data }: { data: DecompositionData }) {
  const complexityColor = {
    simple: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
    medium: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
    complex: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  }[data.complexity] ?? "bg-muted text-muted-foreground";

  return (
    <div className="rounded-xl border border-border bg-muted/30 p-4 text-sm space-y-2.5">
      <div className="flex items-center gap-3">
        <span className="w-24 shrink-0 font-medium text-muted-foreground">Intent</span>
        <span>{data.intent}</span>
      </div>
      <div className="flex items-center gap-3">
        <span className="w-24 shrink-0 font-medium text-muted-foreground">Subject</span>
        <span>{data.subject}</span>
      </div>
      <div className="flex items-center gap-3">
        <span className="w-24 shrink-0 font-medium text-muted-foreground">Complexity</span>
        <span className={cn("rounded-full px-2 py-0.5 text-xs font-medium", complexityColor)}>
          {data.complexity}
        </span>
      </div>
      {data.entities.length > 0 && (
        <div className="flex items-start gap-3">
          <span className="w-24 shrink-0 font-medium text-muted-foreground">Entities</span>
          <div className="flex flex-wrap gap-1">
            {data.entities.map((e) => (
              <span key={e} className="rounded-md bg-muted px-2 py-0.5 text-xs">{e}</span>
            ))}
          </div>
        </div>
      )}
      {data.sub_queries.length > 0 && (
        <div className="flex items-start gap-3">
          <span className="w-24 shrink-0 font-medium text-muted-foreground">Sub-queries</span>
          <ul className="space-y-1">
            {data.sub_queries.map((q, i) => (
              <li key={i} className="text-muted-foreground">↳ {q}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function MessageError() {
  return (
    <MessagePrimitive.Error>
      <ErrorPrimitive.Root className="mt-2 rounded-md border border-destructive bg-destructive/10 p-3 text-destructive text-sm dark:bg-destructive/5 dark:text-red-200">
        <ErrorPrimitive.Message className="line-clamp-2" />
      </ErrorPrimitive.Root>
    </MessagePrimitive.Error>
  );
}

function AssistantActionBar() {
  return (
    <ActionBarPrimitive.Root
      hideWhenRunning
      autohide="not-last"
      className="-ml-1 flex gap-1 text-muted-foreground"
    >
      <ActionBarPrimitive.Copy asChild>
        <TooltipIconButton tooltip="Copy">
          <AuiIf condition={(s) => s.message.isCopied}>
            <CheckIcon />
          </AuiIf>
          <AuiIf condition={(s) => !s.message.isCopied}>
            <CopyIcon />
          </AuiIf>
        </TooltipIconButton>
      </ActionBarPrimitive.Copy>
      <ActionBarPrimitive.ExportMarkdown asChild>
        <TooltipIconButton tooltip="Export as Markdown">
          <DownloadIcon />
        </TooltipIconButton>
      </ActionBarPrimitive.ExportMarkdown>
      <ActionBarPrimitive.Reload asChild>
        <TooltipIconButton tooltip="Refresh">
          <RefreshCwIcon />
        </TooltipIconButton>
      </ActionBarPrimitive.Reload>
      
      <ActionBarPrimitive.FeedbackPositive asChild>
        <TooltipIconButton tooltip="Good response">
          <ThumbsUpIcon />
        </TooltipIconButton>
      </ActionBarPrimitive.FeedbackPositive>
      <ActionBarPrimitive.FeedbackNegative asChild>
        <TooltipIconButton tooltip="Bad response">
          <ThumbsDownIcon />
        </TooltipIconButton>
      </ActionBarPrimitive.FeedbackNegative>
    </ActionBarPrimitive.Root>
  );
}

function BranchPicker({ className, ...rest }: { className?: string }) {
  return (
    <BranchPickerPrimitive.Root
      hideWhenSingleBranch
      className={cn("mr-2 -ml-2 inline-flex items-center text-xs text-muted-foreground", className)}
      {...rest}
    >
      <BranchPickerPrimitive.Previous asChild>
        <TooltipIconButton tooltip="Previous">
          <ChevronLeftIcon />
        </TooltipIconButton>
      </BranchPickerPrimitive.Previous>
      <span className="font-medium">
        <BranchPickerPrimitive.Number /> / <BranchPickerPrimitive.Count />
      </span>
      <BranchPickerPrimitive.Next asChild>
        <TooltipIconButton tooltip="Next">
          <ChevronRightIcon />
        </TooltipIconButton>
      </BranchPickerPrimitive.Next>
    </BranchPickerPrimitive.Root>
  );
}
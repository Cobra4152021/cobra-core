import type { ApprovalAction, ApprovalChainStep, ApprovalState, ApprovalTransitionResult } from "./types.js";

const FSM: Record<
  ApprovalState,
  Partial<Record<ApprovalAction, ApprovalState>>
> = {
  draft: {
    submit_for_review: "review",
    archive: "archived",
  },
  review: {
    approve: "approved",
    request_changes: "draft",
    archive: "archived",
  },
  approved: {
    publish: "published",
    request_changes: "review",
    archive: "archived",
  },
  published: {
    archive: "archived",
    reopen: "review",
  },
  archived: {
    reopen: "draft",
  },
};

/** Transition approval state via FSM. Returns ok=false when transition invalid. */
export function transitionApproval(
  state: ApprovalState,
  action: ApprovalAction,
): ApprovalTransitionResult {
  const next = FSM[state]?.[action];
  if (!next) {
    return {
      ok: false,
      error: `Cannot '${action}' from state '${state}'`,
    };
  }
  return { ok: true, nextState: next };
}

/** Build ordered approval chain for a resource workflow. */
export function buildApprovalChain(options: {
  requireLegal?: boolean;
  requireSecurity?: boolean;
  customSteps?: ApprovalChainStep[];
}): ApprovalChainStep[] {
  const steps: ApprovalChainStep[] = [
    { role: "author", order: 1, required: true },
    { role: "reviewer", order: 2, required: true },
    { role: "admin", order: 3, required: true },
  ];

  let order = 4;
  if (options.requireLegal) {
    steps.push({ role: "legal", order: order++, required: true });
  }
  if (options.requireSecurity) {
    steps.push({ role: "security", order: order++, required: true });
  }
  if (options.customSteps?.length) {
    for (const step of options.customSteps) {
      steps.push({ ...step, order: step.order || order++ });
    }
  }

  return steps.sort((a, b) => a.order - b.order);
}

export { FSM as APPROVAL_FSM };

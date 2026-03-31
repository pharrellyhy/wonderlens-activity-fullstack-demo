import { useState } from 'react';

// Catppuccin Mocha palette
const C = {
  base: '#1e1e2e',
  surface0: '#313244',
  surface2: '#585b70',
  overlay0: '#6c7086',
  text: '#cdd6f4',
  subtext0: '#a6adc8',
  blue: '#89b4fa',
  green: '#a6e3a1',
  red: '#f38ba8',
  peach: '#fab387',
  yellow: '#f9e2af',
  border: '#45475a',
};

function Badge({ color, bg, children }) {
  return (
    <span
      className="px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide"
      style={{ color, backgroundColor: bg || `${color}20` }}
    >
      {children}
    </span>
  );
}

function KV({ label, children }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="shrink-0" style={{ color: C.overlay0 }}>{label}:</span>
      <span className="font-semibold" style={{ color: C.text }}>{children}</span>
    </div>
  );
}

function SectionTitle({ children }) {
  return (
    <h4 className="text-[10px] font-bold uppercase tracking-wider mb-2" style={{ color: C.overlay0 }}>
      {children}
    </h4>
  );
}

// Derive step flow from sessionState when debugData.step_flow is unavailable
function deriveStepFlow(sessionState) {
  if (!sessionState) return [];

  const currentStep = sessionState.current_step || '';
  const templateType = sessionState.template_type || 'cat1';

  const totalRounds = sessionState.total_rounds || 3;
  let steps;
  if (templateType === 'cat5') {
    steps = ['STEP_1_HOOK', 'STEP_2_MISSION'];
    for (let i = 1; i <= totalRounds; i++) steps.push(`STEP_3_COLLECT_${i}`);
    steps.push('STEP_4_SYNTHESIS', 'STEP_5_CELEBRATE', 'STEP_6_CLOSING');
  } else {
    steps = ['STEP_1_HOOK', 'STEP_2_RULES'];
    for (let i = 1; i <= totalRounds; i++) steps.push(`STEP_3_ROUND_${i}`);
    steps.push('STEP_4_CELEBRATE', 'STEP_5_CLOSING');
  }

  const normalizedCurrent = currentStep;

  let passedCurrent = false;
  return steps.map((s) => {
    if (s === normalizedCurrent) {
      passedCurrent = true;
      return { step: s, status: 'current' };
    }
    if (!passedCurrent) {
      return { step: s, status: 'done' };
    }
    return { step: s, status: 'pending' };
  });
}

const STEP_STYLES = {
  done:    { color: C.green,    fontWeight: 600 },
  current: { color: C.blue,     fontWeight: 700, backgroundColor: `${C.blue}15` },
  pending: { color: C.surface2, fontWeight: 600 },
};

function StepBadge({ step }) {
  const stepName = step.step || step.name || '';
  const label = stepName.replace(/^STEP_\d+_/, '').replace(/_/g, ' ');
  const s = STEP_STYLES[step.status] || STEP_STYLES.pending;

  return (
    <span
      className="px-2 py-1 rounded-md text-[10px] whitespace-nowrap border"
      style={{ color: s.color, borderColor: s.color, fontWeight: s.fontWeight, backgroundColor: s.backgroundColor }}
    >
      {step.status === 'done' && <>&zwj;&#10003; </>}{label}
    </span>
  );
}

function StateMachineTab({ debugData, sessionState, templateType }) {
  const stepFlow = debugData?.step_flow || deriveStepFlow(sessionState);
  const isCat5 = templateType === 'cat5';
  const collectionPhase = sessionState?.collection_phase;
  const synthesisPhase = sessionState?.synthesis_phase;

  return (
    <div className="grid grid-cols-3 gap-4 p-3">
      {/* Column 1 - Step Flow */}
      <div>
        <SectionTitle>Step Flow</SectionTitle>
        <div className="flex gap-1.5 overflow-x-auto pb-1" style={{ scrollbarWidth: 'thin' }}>
          {stepFlow.map((step, i) => (
            <StepBadge key={i} step={step} />
          ))}
        </div>
        {isCat5 && collectionPhase && (
          <div className="mt-2">
            <Badge color={C.blue}>{collectionPhase}</Badge>
          </div>
        )}
      </div>

      {/* Column 2 - Session State */}
      <div>
        <SectionTitle>Session State</SectionTitle>
        <div className="space-y-1.5">
          <KV label="round">
            {sessionState?.current_round ?? '-'} / {sessionState?.total_rounds ?? '-'}
          </KV>
          {isCat5 && (
            <KV label="collection_phase">
              {collectionPhase
                ? <Badge color={C.blue}>{collectionPhase}</Badge>
                : <span style={{ color: C.surface2 }}>--</span>}
            </KV>
          )}
          {synthesisPhase ? (
            <KV label="synthesis_phase">
              <Badge color={C.yellow}>{synthesisPhase}</Badge>
            </KV>
          ) : isCat5 ? (
            <KV label="synthesis_phase">
              <span style={{ color: C.surface2 }}>--</span>
            </KV>
          ) : null}
          <KV label="silence">{sessionState?.consecutive_silence ?? 0}</KV>
          <KV label="wrong_photos">{sessionState?.consecutive_wrong ?? 0}</KV>
          <KV label="auto_advance">
            <span style={{ color: sessionState?.auto_advance ? C.green : C.red }}>
              {sessionState?.auto_advance ? 'true' : 'false'}
            </span>
          </KV>
        </div>
      </div>

      {/* Column 3 - Collection (cat5 only) */}
      <div>
        {isCat5 ? (
          <>
            <SectionTitle>Collection</SectionTitle>
            <div className="space-y-1.5">
              <KV label="collected">
                <span style={{ color: C.green }}>
                  {sessionState?.collected_photos?.length ?? 0} / {sessionState?.total_rounds ?? '-'}
                </span>
              </KV>
              <KV label="names">
                {sessionState?.collected_names?.join(', ') || '--'}
              </KV>
              {sessionState?.collected_details?.length > 0 && (
                <div className="text-[10px]" style={{ color: C.subtext0 }}>
                  {sessionState.collected_details.join('; ')}
                </div>
              )}
            </div>
          </>
        ) : (
          <>
            <SectionTitle>Info</SectionTitle>
            <p className="text-[10px]" style={{ color: C.surface2 }}>Cat1 -- no collection data</p>
          </>
        )}
      </div>
    </div>
  );
}

function GenerationTab({ debugData }) {
  const gen = debugData?.generation;
  const planner = debugData?.planner;
  const llm = debugData?.llm_output;
  const bestOfN = debugData?.best_of_n;
  const retryStats = debugData?.retry_stats;

  if (!gen && !planner && !retryStats) {
    return (
      <div className="p-3 text-xs" style={{ color: C.surface2 }}>
        No generation data available.
      </div>
    );
  }

  // Compute session-wide totals from per-step retry_stats
  let totalGen = 0, firstPass = 0, retried = 0, exhausted = 0;
  if (retryStats) {
    for (const step of Object.values(retryStats)) {
      totalGen += step.total || 0;
      firstPass += step.first_pass || 0;
      retried += step.retried || 0;
      exhausted += step.exhausted || 0;
    }
  }
  const passRate = totalGen > 0 ? ((firstPass / totalGen) * 100).toFixed(0) : '--';

  const attemptCount = gen?.attempt_count ?? 0;
  const attemptsList = gen?.attempts ?? [];
  const failedAttempts = attemptsList.filter(a => a.verdict !== 'passed');
  const totalLatency = attemptsList.reduce((sum, a) => sum + (a.latency_ms || 0), 0);

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-3">
      {/* Column 1 - This Turn */}
      <div>
        <SectionTitle>This Turn</SectionTitle>
        <div className="space-y-1.5">
          <KV label="attempts">
            <span style={{ color: attemptCount > 1 ? C.peach : C.text }}>
              {attemptCount} / 3
            </span>
          </KV>
          <KV label="verdict">
            <Badge color={gen?.final_verdict === 'passed' ? C.green : gen?.final_verdict === 'exhausted' ? C.red : C.peach}>
              {gen?.final_verdict ?? '--'}
            </Badge>
          </KV>
          <KV label="latency">{totalLatency || '--'}ms</KV>
        </div>
        {failedAttempts.length > 0 && (
          <div
            className="mt-2 rounded p-2 text-[10px] space-y-1"
            style={{ backgroundColor: C.surface0, borderLeft: `3px solid ${C.peach}` }}
          >
            {failedAttempts.map((a, i) => (
              <div key={i}>
                <span style={{ color: C.peach }}>#{a.attempt} ({a.call_type}, {a.latency_ms}ms): </span>
                <span style={{ color: C.subtext0 }}>{a.hint || a.verdict}</span>
              </div>
            ))}
          </div>
        )}
        {attemptsList.length > 0 && (
          <div className="mt-2 space-y-0.5">
            {attemptsList.map((a, i) => (
              <div key={i} className="flex items-center gap-2 text-[10px]">
                <span style={{ color: C.overlay0 }}>#{a.attempt}</span>
                <span style={{ color: a.call_type === 'speaker_retry' ? C.yellow : C.subtext0 }}>
                  {a.call_type}
                </span>
                <span style={{ color: a.verdict === 'passed' ? C.green : a.verdict === 'error' ? C.red : C.peach }}>
                  {a.verdict}
                </span>
                <span style={{ color: C.overlay0 }}>{a.latency_ms}ms</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Column 2 - LLM Output + Planner */}
      <div>
        <SectionTitle>LLM Output</SectionTitle>
        {llm ? (
          <div className="space-y-1.5">
            <KV label="tone"><Badge color={C.blue}>{llm.tone_marker}</Badge></KV>
            <KV label="stay_on_step">
              <span style={{ color: llm.stay_on_step ? C.yellow : C.green }}>
                {llm.stay_on_step ? 'true' : 'false'}
              </span>
            </KV>
            {llm.child_intent && <KV label="intent"><Badge color={C.peach}>{llm.child_intent}</Badge></KV>}
            <KV label="widget">{llm.screen_widget ?? '--'}</KV>
            {llm.sfx_cue && <KV label="sfx">{llm.sfx_cue}</KV>}
          </div>
        ) : (
          <p className="text-[10px]" style={{ color: C.surface2 }}>--</p>
        )}

        {planner && (
          <>
            <SectionTitle>Planner</SectionTitle>
            <div className="space-y-1.5">
              <KV label="suggest">
                <Badge color={planner.do_not_suggest_items ? C.red : C.green}>
                  {planner.do_not_suggest_items ? 'blocked' : 'ok'}
                </Badge>
              </KV>
              <KV label="question">
                <span style={{ color: planner.do_not_ask_question ? C.red : C.green }}>
                  {planner.do_not_ask_question ? 'no' : 'yes'}
                </span>
              </KV>
              <KV label="binary">
                <span style={{ color: planner.offer_binary_choice ? C.green : C.overlay0 }}>
                  {planner.offer_binary_choice ? 'yes' : 'no'}
                </span>
              </KV>
              <KV label="model_first">
                <span style={{ color: planner.must_model_first ? C.green : C.overlay0 }}>
                  {planner.must_model_first ? 'yes' : 'no'}
                </span>
              </KV>
            </div>
          </>
        )}
      </div>

      {/* Column 3 - Best-of-N */}
      <div>
        <SectionTitle>Best-of-N</SectionTitle>
        {bestOfN ? (
          <div className="space-y-1.5">
            <KV label="candidates">{bestOfN.returned} / {bestOfN.n}</KV>
            {bestOfN.errors?.length > 0 && (
              <KV label="errors"><span style={{ color: C.red }}>{bestOfN.errors.length}</span></KV>
            )}
            <div className="mt-1 space-y-1 overflow-y-auto max-h-48" style={{ scrollbarWidth: 'thin' }}>
              {bestOfN.candidates?.map((c, i) => (
                <div
                  key={i}
                  className="rounded p-1.5 text-[10px]"
                  style={{
                    backgroundColor: c.picked ? `${C.green}15` : C.surface0,
                    borderLeft: `2px solid ${c.picked ? C.green : C.surface2}`,
                  }}
                >
                  <div className="flex items-center gap-2 mb-0.5">
                    <span style={{ color: c.picked ? C.green : C.overlay0, fontWeight: c.picked ? 600 : 400 }}>
                      {c.score != null ? c.score.toFixed(3) : '--'}
                    </span>
                    {c.picked && <Badge color={C.green}>picked</Badge>}
                  </div>
                  <div style={{ color: C.subtext0 }}>{c.text}</div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-[10px]" style={{ color: C.surface2 }}>Single generation (no best-of-N)</p>
        )}
      </div>

      {/* Column 4 - Session Stats */}
      <div>
        <SectionTitle>Session Stats</SectionTitle>
        <div className="space-y-1.5">
          <KV label="total_gen">{totalGen}</KV>
          <KV label="first_pass">
            <span style={{ color: C.green }}>{firstPass}</span>
          </KV>
          <KV label="retried">
            <span style={{ color: C.peach }}>{retried}</span>
          </KV>
          <KV label="exhausted">
            <span style={{ color: C.red }}>{exhausted}</span>
          </KV>
          <KV label="pass_rate">
            <span style={{ color: C.green }}>{passRate}%</span>
          </KV>
        </div>
      </div>
    </div>
  );
}

function HistoryTab({ debugHistory }) {
  if (!debugHistory || debugHistory.length === 0) {
    return (
      <div className="p-3 text-xs" style={{ color: C.surface2 }}>
        No history yet -- turns will appear as the session progresses.
      </div>
    );
  }

  return (
    <div className="p-3 space-y-2">
      {[...debugHistory].reverse().map((entry, i) => {
        const gen = entry.generation;
        const synth = entry.synthesis;
        const stepFlow = entry.step_flow || [];
        const currentStep = stepFlow.find(s => s.status === 'current');

        return (
          <div
            key={i}
            className="rounded p-2 text-[10px]"
            style={{ backgroundColor: C.surface0, borderLeft: `2px solid ${C.blue}` }}
          >
            <div className="flex items-center gap-2 mb-1">
              <Badge color={C.blue}>T{entry.turn ?? '?'}</Badge>
              <span style={{ color: C.text, fontWeight: 600 }}>{currentStep?.step || '--'}</span>
              {gen && (
                <>
                  <Badge color={gen.final_verdict === 'passed' ? C.green : C.red}>
                    {gen.final_verdict}
                  </Badge>
                  <span style={{ color: C.overlay0 }}>
                    {gen.attempt_count} attempt{gen.attempt_count !== 1 ? 's' : ''}
                  </span>
                </>
              )}
              {entry.llm_output?.tone_marker && (
                <span style={{ color: C.overlay0 }}>[{entry.llm_output.tone_marker}]</span>
              )}
            </div>
            {synth && (
              <div className="flex gap-2 mt-1">
                <span style={{ color: C.yellow }}>synthesis:{synth.phase}</span>
                {synth.story_attempts > 0 && <span style={{ color: C.green }}>stories:{synth.story_attempts}</span>}
                {synth.declines > 0 && <span style={{ color: C.red }}>declines:{synth.declines}</span>}
                {synth.silences > 0 && <span style={{ color: C.peach }}>silences:{synth.silences}</span>}
                {synth.unrelated > 0 && <span style={{ color: C.peach }}>unrelated:{synth.unrelated}</span>}
              </div>
            )}
            {gen?.attempts?.filter(a => a.verdict !== 'passed').map((a, j) => (
              <div key={j} className="mt-0.5" style={{ color: C.peach }}>
                #{a.attempt} {a.call_type} failed: {a.hint}
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );
}

function TabButton({ label, active, onClick }) {
  return (
    <button
      className="px-3 py-2 text-xs font-semibold transition-colors cursor-pointer"
      style={{
        color: active ? C.blue : C.overlay0,
        borderBottom: active ? `2px solid ${C.blue}` : '2px solid transparent',
      }}
      onClick={onClick}
    >
      {label}
    </button>
  );
}

export default function DebugPanel({ debugData, debugHistory, sessionState, templateType, isOpen }) {
  const [activeTab, setActiveTab] = useState('state');

  if (!sessionState) return null;

  const totalLatency = debugData?.generation?.attempts?.reduce((s, a) => s + (a.latency_ms || 0), 0);

  return (
    <div
      className="fixed bottom-0 left-0 right-0 z-50 font-mono text-xs transition-transform duration-300"
      style={{
        maxHeight: '45vh',
        backgroundColor: C.base,
        borderTop: `1px solid ${C.border}`,
        transform: isOpen ? 'translateY(0)' : 'translateY(100%)',
      }}
    >
      {/* Tab bar */}
      <div
        className="flex items-center justify-between px-3"
        style={{ borderBottom: `1px solid ${C.border}` }}
      >
        <div className="flex">
          <TabButton label="State" active={activeTab === 'state'} onClick={() => setActiveTab('state')} />
          <TabButton label="Generation" active={activeTab === 'generation'} onClick={() => setActiveTab('generation')} />
          <TabButton
            label={`History (${debugHistory?.length || 0})`}
            active={activeTab === 'history'}
            onClick={() => setActiveTab('history')}
          />
        </div>
        <div className="flex items-center gap-3" style={{ color: C.subtext0 }}>
          <span>turn: {sessionState?.turn_count ?? '--'}</span>
          <span>{totalLatency || '--'}ms</span>
        </div>
      </div>

      {/* Tab content */}
      <div className="overflow-y-auto" style={{ maxHeight: 'calc(45vh - 36px)' }}>
        {!debugData && activeTab !== 'history' ? (
          <div className="p-4 text-center" style={{ color: C.surface2 }}>
            No debug data -- interact with the session to see debug info.
          </div>
        ) : activeTab === 'state' ? (
          <StateMachineTab debugData={debugData} sessionState={sessionState} templateType={templateType} />
        ) : activeTab === 'generation' ? (
          <GenerationTab debugData={debugData} />
        ) : (
          <HistoryTab debugHistory={debugHistory} />
        )}
      </div>
    </div>
  );
}

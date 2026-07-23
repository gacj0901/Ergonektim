"use client";

import {
  ChangeEvent,
  useEffect,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";

type Locale = "es" | "en";
const LOCALE_STORAGE_KEY = "ergonektim-locale";
const LOCALE_CHANGE_EVENT = "ergonektim-locale-change";

function localeSnapshot(): Locale {
  const stored = window.localStorage.getItem(LOCALE_STORAGE_KEY);
  return stored === "en" ? "en" : "es";
}

function localeServerSnapshot(): Locale {
  return "es";
}

function subscribeLocale(onStoreChange: () => void) {
  window.addEventListener("storage", onStoreChange);
  window.addEventListener(LOCALE_CHANGE_EVENT, onStoreChange);
  return () => {
    window.removeEventListener("storage", onStoreChange);
    window.removeEventListener(LOCALE_CHANGE_EVENT, onStoreChange);
  };
}

type Severity =
  | "favorable"
  | "informational"
  | "attention"
  | "critical"
  | "indeterminate";
type ObserverKey =
  | "telemetric_status"
  | "stability_status"
  | "performance_status"
  | "condition_report"
  | "causal_link"
  | "estimation_fidelity";

type Presentation = {
  observer_name: string;
  label: string;
  explanation: string;
  review_action: string;
  claim_boundary: string;
};

type Diagnostic = {
  observer: ObserverKey;
  code: string;
  severity: Severity;
  signal: string;
  eligible: boolean;
  timestamp_utc: string;
  evidence: Record<string, unknown>;
  presentations: Record<Locale, Presentation>;
};

type CausalSignal = { component: string; diagnostic: Diagnostic };
type TimelineRow = {
  timestamp_utc: string;
  state: { M: number; G: number; xi: number; theta: number; lambda: number };
  signals: {
    telemetric_status: Diagnostic;
    stability_status: Diagnostic;
    performance_status: Diagnostic;
    causal_link: CausalSignal[];
    estimation_fidelity: Diagnostic;
  };
};

type Assessment = {
  schema_version: string;
  access: { outcomes_accessed: boolean; global_scalar_emitted: boolean };
  input_binding: {
    verified: boolean;
    assessment_id?: string;
    bundle_sha256?: string;
    rows?: number;
    start_utc?: string;
    stop_utc?: string;
  };
  kernel_binding: {
    verified: boolean;
    prama_version: string;
    python_kernel_sha256?: string;
    recertification?: { sha256?: string; verified?: boolean };
  };
  summary: {
    rows: number;
    observer_count: number;
    global_scalar_emitted: boolean;
  };
  condition_report: Diagnostic[];
  timeline: TimelineRow[];
};

const observers: ObserverKey[] = [
  "telemetric_status",
  "stability_status",
  "performance_status",
  "condition_report",
  "causal_link",
  "estimation_fidelity",
];

const observerFallback: Record<ObserverKey, Record<Locale, string>> = {
  telemetric_status: { es: "Estado telemétrico", en: "Telemetric Status" },
  stability_status: { es: "Estado de estabilidad", en: "Stability Status" },
  performance_status: { es: "Estado de desempeño", en: "Performance Status" },
  condition_report: { es: "Reporte de condición", en: "Condition Report" },
  causal_link: { es: "Enlace causal", en: "Causal Link" },
  estimation_fidelity: { es: "Fidelidad de estimación", en: "Estimation Fidelity" },
};

const copy = {
  es: {
    controlRoom: "Sala de evaluación",
    subtitle: "Viabilidad aptadinámica · sistemas eléctricos de potencia",
    demo: "Demostración verificable",
    loaded: "Artefacto cargado",
    load: "Abrir evaluación JSON",
    replace: "Sustituir evaluación",
    localOnly: "El archivo se procesa localmente y no se transmite.",
    independent: "Seis observadores independientes",
    noScalar: "Sin escalar global",
    custody: "Custodia de la evaluación",
    input: "Paquete de entrada",
    kernel: "Kernel PRAMA",
    recert: "Recertificación numérica",
    verified: "Verificado",
    unverified: "No verificado",
    rows: "filas causales",
    observerPanel: "Panel distributivo",
    panelNote: "Cada canal conserva su propio estado y frontera de afirmación.",
    select: "Seleccionar observador",
    trajectory: "Trayectoria estructural",
    trajectoryNote: "Margen M y gradiente G · últimas 72 filas",
    margin: "Margen M",
    gradient: "Gradiente G",
    detail: "Lectura del observador",
    current: "Estado observado",
    evidence: "Evidencia",
    review: "Acción de revisión",
    boundary: "Frontera de afirmación",
    history: "Registro reciente",
    all: "Todos",
    favorable: "Favorables",
    attention: "Atención",
    critical: "Críticos",
    indeterminate: "Indeterminados",
    time: "Tiempo UTC",
    state: "Estado",
    copied: "Hash copiado",
    copyHash: "Copiar hash",
    invalid: "El archivo no cumple el contrato mínimo de assessment.v1.3.",
    access: "Acceso científico",
    outcomeFree: "Sin outcomes",
    demoNotice:
      "Esta vista usa una fixture sintética. Abra un artefacto ERGONEKTIM para inspeccionar una corrida propia.",
  },
  en: {
    controlRoom: "Assessment room",
    subtitle: "Aptadynamic viability · electric power systems",
    demo: "Verifiable demonstration",
    loaded: "Artifact loaded",
    load: "Open assessment JSON",
    replace: "Replace assessment",
    localOnly: "The file is processed locally and is never transmitted.",
    independent: "Six independent observers",
    noScalar: "No global scalar",
    custody: "Assessment custody",
    input: "Input bundle",
    kernel: "PRAMA kernel",
    recert: "Numeric recertification",
    verified: "Verified",
    unverified: "Unverified",
    rows: "causal rows",
    observerPanel: "Distributive panel",
    panelNote: "Every channel keeps its own state and claim boundary.",
    select: "Select observer",
    trajectory: "Structural trajectory",
    trajectoryNote: "Margin M and gradient G · latest 72 rows",
    margin: "Margin M",
    gradient: "Gradient G",
    detail: "Observer reading",
    current: "Observed state",
    evidence: "Evidence",
    review: "Review action",
    boundary: "Claim boundary",
    history: "Recent register",
    all: "All",
    favorable: "Favorable",
    attention: "Attention",
    critical: "Critical",
    indeterminate: "Indeterminate",
    time: "UTC time",
    state: "State",
    copied: "Hash copied",
    copyHash: "Copy hash",
    invalid: "The file does not satisfy the minimum assessment.v1.3 contract.",
    access: "Scientific access",
    outcomeFree: "Outcome-free",
    demoNotice:
      "This view uses a synthetic fixture. Open an ERGONEKTIM artifact to inspect your own run.",
  },
};

const statusText: Record<string, Record<Locale, [string, string, string]>> = {
  observability_clear: {
    es: ["Observabilidad clara", "La máscara causal admite esta fila.", "Continuar vigilancia."],
    en: ["Observability clear", "The causal mask admits this row.", "Continue monitoring."],
  },
  instrument_indeterminate: {
    es: ["Instrumento indeterminado", "La cobertura no permite una lectura sustantiva.", "Revisar fuente y zona muerta."],
    en: ["Instrument indeterminate", "Coverage does not permit a substantive reading.", "Review source and dead zone."],
  },
  viable: {
    es: ["Viable", "El margen es no negativo y no presenta deriva descendente.", "Mantener seguimiento causal."],
    en: ["Viable", "Margin is nonnegative without downward drift.", "Maintain causal monitoring."],
  },
  viable_with_negative_gradient: {
    es: ["Margen viable con gradiente negativo", "El margen es no negativo y G es negativo; no se aplicó umbral de magnitud o persistencia.", "Examinar magnitud y persistencia por separado."],
    en: ["Viable margin with negative gradient", "Margin is nonnegative and G is negative; no magnitude or persistence threshold was applied.", "Inspect magnitude and persistence separately."],
  },
  collapsing: {
    es: ["Viabilidad comprometida", "El margen estructural cruzó la frontera.", "Escalar revisión humana inmediata."],
    en: ["Viability compromised", "The structural margin crossed its boundary.", "Escalate immediate human review."],
  },
  solvent: {
    es: ["Regeneración solvente", "La entrada de regeneración excede el drenaje declarado.", "Verificar persistencia del balance."],
    en: ["Solvent regeneration", "Regeneration exceeds declared drain.", "Verify balance persistence."],
  },
  balanced: {
    es: ["Balance neutro", "Regeneración y drenaje se equilibran.", "Observar cambios de régimen."],
    en: ["Neutral balance", "Regeneration and drain are balanced.", "Watch for regime changes."],
  },
  structural_ledger_inactive: {
    es: ["Libro mayor estructural inactivo", "Drenaje y regeneración son cero; no existe comparación de solvencia.", "Tratarlo como cobertura de rama, no como balance."],
    en: ["Structural ledger inactive", "Drain and regeneration are zero; no solvency comparison exists.", "Treat this as branch coverage, not balance."],
  },
  insolvent: {
    es: ["Regeneración insuficiente", "El drenaje supera la regeneración declarada.", "Revisar capacidad de restitución."],
    en: ["Insufficient regeneration", "Drain exceeds declared regeneration.", "Review restitution capacity."],
  },
  regenerative: {
    es: ["Ventana regenerativa", "El margen posterior supera la referencia previa.", "Conservar la ventana como evidencia."],
    en: ["Regenerative window", "Post-window margin exceeds the prior reference.", "Retain the window as evidence."],
  },
  non_restitutive: {
    es: ["Restitución incompleta", "La ventana planificada no recuperó el margen previo.", "Revisar deuda residual."],
    en: ["Incomplete restitution", "The planned window did not restore prior margin.", "Review residual debt."],
  },
  phi_internal: {
    es: ["Contribución interna", "El cambio de desajuste se concentra en Φ.", "Inspeccionar el registro interno."],
    en: ["Internal contribution", "Mismatch change is concentrated in Φ.", "Inspect the internal register."],
  },
  psi_environmental: {
    es: ["Contribución envolvente", "El componente externo domina el incremento local.", "Revisar fuente y referencia externa."],
    en: ["Environmental contribution", "The external component dominates the local increase.", "Review external source and reference."],
  },
  no_new_deterioration: {
    es: ["Sin deterioro nuevo", "El desajuste local no aumentó.", "Mantener observación distributiva."],
    en: ["No new deterioration", "Local mismatch did not increase.", "Maintain distributive observation."],
  },
  faithful_self_image: {
    es: ["Autoimagen fiel", "R(t) permanece próximo al exceso estructural.", "Continuar contraste externo."],
    en: ["Faithful self-image", "R(t) remains close to structural excess.", "Continue external comparison."],
  },
  critical_self_image: {
    es: ["Autoimagen crítica", "La fidelidad se aproxima a su frontera.", "Revisar escala y acople operacional."],
    en: ["Critical self-image", "Fidelity approaches its boundary.", "Review scale and operational coupling."],
  },
};

const observerBoundaries: Record<ObserverKey, Record<Locale, string>> = {
  telemetric_status: {
    es: "Certifica observabilidad; no afirma estabilidad física.",
    en: "Certifies observability; it does not assert physical stability.",
  },
  stability_status: {
    es: "Describe margen y deriva presentes; no predice outages.",
    en: "Describes present margin and drift; it does not predict outages.",
  },
  performance_status: {
    es: "Audita drenaje y regeneración declarados; no optimiza despacho.",
    en: "Audits declared drain and regeneration; it does not optimize dispatch.",
  },
  condition_report: {
    es: "Caracteriza restitución alrededor de ventanas planificadas.",
    en: "Characterizes restitution around planned windows.",
  },
  causal_link: {
    es: "Atribuye cambio local por componente; no identifica causa raíz definitiva.",
    en: "Attributes local change by component; it does not establish definitive root cause.",
  },
  estimation_fidelity: {
    es: "Contrasta R(t) externo con Ξ−Θ; no reconstruye la opinión del operador.",
    en: "Contrasts external R(t) with Ξ−Θ; it does not reconstruct operator judgment.",
  },
};

function diagnostic(
  observer: ObserverKey,
  code: string,
  severity: Severity,
  timestamp: string,
  evidence: Record<string, unknown>,
): Diagnostic {
  const text = statusText[code] ?? statusText.instrument_indeterminate;
  return {
    observer,
    code,
    severity,
    signal: severity === "critical" ? "red" : severity === "attention" ? "amber" : severity === "favorable" ? "green" : severity === "informational" ? "blue" : "gray",
    eligible: severity !== "indeterminate",
    timestamp_utc: timestamp,
    evidence,
    presentations: {
      es: {
        observer_name: observerFallback[observer].es,
        label: text.es[0],
        explanation: text.es[1],
        review_action: text.es[2],
        claim_boundary: observerBoundaries[observer].es,
      },
      en: {
        observer_name: observerFallback[observer].en,
        label: text.en[0],
        explanation: text.en[1],
        review_action: text.en[2],
        claim_boundary: observerBoundaries[observer].en,
      },
    },
  };
}

function createDemoAssessment(): Assessment {
  const start = Date.parse("2026-07-01T00:00:00Z");
  const timeline: TimelineRow[] = Array.from({ length: 72 }, (_, index) => {
    const timestamp = new Date(start + index * 3_600_000).toISOString();
    const M = 0.34 + Math.sin(index / 8) * 0.17 - Math.max(index - 48, 0) * 0.012;
    const previous = 0.34 + Math.sin((index - 1) / 8) * 0.17 - Math.max(index - 49, 0) * 0.012;
    const G = index === 0 ? 0 : M - previous;
    const telemetryCode = index === 23 ? "instrument_indeterminate" : "observability_clear";
    const stabilityCode = M < 0 ? "collapsing" : G < 0 ? "viable_with_negative_gradient" : "viable";
    const performanceCode = index > 58 ? "insolvent" : index % 16 < 4 ? "structural_ledger_inactive" : "solvent";
    const fidelityCode = index > 62 ? "critical_self_image" : "faithful_self_image";
    const causalCode = index > 51 ? "psi_environmental" : index > 34 ? "phi_internal" : "no_new_deterioration";
    return {
      timestamp_utc: timestamp,
      state: {
        M,
        G,
        xi: 0.72 + index * 0.011,
        theta: 0.61 + Math.sin(index / 10) * 0.04,
        lambda: Math.max(0.28, 0.91 - index * 0.006),
      },
      signals: {
        telemetric_status: diagnostic(
          "telemetric_status",
          telemetryCode,
          telemetryCode === "observability_clear" ? "favorable" : "indeterminate",
          timestamp,
          { interval_width: telemetryCode === "observability_clear" ? 0.012 : 0.684, source_count: 2 },
        ),
        stability_status: diagnostic(
          "stability_status",
          stabilityCode,
          stabilityCode === "collapsing" ? "critical" : stabilityCode === "viable_with_negative_gradient" ? "informational" : "favorable",
          timestamp,
          { M, G, sigma_op: true },
        ),
        performance_status: diagnostic(
          "performance_status",
          performanceCode,
          performanceCode === "insolvent" ? "attention" : performanceCode === "solvent" ? "favorable" : "informational",
          timestamp,
          { structural_drain: 0.00004 + index * 0.000001, regeneration: index > 58 ? 0.00002 : 0.00008, net_solvency: index > 58 ? -0.00003 : 0.00004 },
        ),
        causal_link: [
          {
            component: "wind_forecast_error",
            diagnostic: diagnostic(
              "causal_link",
              causalCode,
              causalCode === "no_new_deterioration" ? "favorable" : "attention",
              timestamp,
              { phi_contribution: index > 34 ? 0.018 : -0.004, psi_contribution: index > 51 ? 0.031 : 0.006, mismatch_change: index > 51 ? 0.049 : 0.012 },
            ),
          },
          {
            component: "interchange_schedule_error",
            diagnostic: diagnostic(
              "causal_link",
              index > 60 ? "psi_environmental" : "no_new_deterioration",
              index > 60 ? "attention" : "favorable",
              timestamp,
              { phi_contribution: 0.005, psi_contribution: index > 60 ? 0.023 : -0.003, mismatch_change: index > 60 ? 0.028 : 0.002 },
            ),
          },
        ],
        estimation_fidelity: diagnostic(
          "estimation_fidelity",
          fidelityCode,
          fidelityCode === "critical_self_image" ? "attention" : "favorable",
          timestamp,
          { operator_R: index > 62 ? 0.36 : 0.16, structural_excess: 0.18 + index * 0.002, fidelity: index > 62 ? 0.08 : 0.82 },
        ),
      },
    };
  });
  const firstEpisode = diagnostic(
    "condition_report",
    "regenerative",
    "favorable",
    new Date(start + 36 * 3_600_000).toISOString(),
    { pre_margin_median: 0.43, during_margin_minimum: 0.21, post_margin_median: 0.49, restoration_per_invested_drain: 1.27 },
  );
  const secondEpisode = diagnostic(
    "condition_report",
    "non_restitutive",
    "attention",
    new Date(start + 64 * 3_600_000).toISOString(),
    { pre_margin_median: 0.32, during_margin_minimum: 0.08, post_margin_median: 0.24, restoration_per_invested_drain: 0.67 },
  );
  return {
    schema_version: "ergonektim.assessment.v1.3",
    access: { outcomes_accessed: false, global_scalar_emitted: false },
    input_binding: {
      verified: true,
      assessment_id: "synthetic-shared-stream-v1",
      bundle_sha256: "4010bbddf52e2e1978d28802d15af3da723b893923bae65bf693eaa35d9350bb",
      rows: 72,
      start_utc: timeline[0].timestamp_utc,
      stop_utc: timeline[timeline.length - 1].timestamp_utc,
    },
    kernel_binding: {
      verified: true,
      prama_version: "0.3.0",
      python_kernel_sha256: "b6fc160c8bd212cb2d693878ad5692a5ab38b3c988bb94db321636bf69d4075d",
      recertification: {
        verified: true,
        sha256: "1be41f35ef4c3ab5230c950dfa6c0bba1c4081eef6a35801ddbf5524aa7ad7bf",
      },
    },
    summary: {
      rows: timeline.length,
      observer_count: 6,
      global_scalar_emitted: false,
    },
    condition_report: [firstEpisode, secondEpisode],
    timeline,
  };
}

const demoAssessment = createDemoAssessment();

function observerSignals(assessment: Assessment, observer: ObserverKey): Diagnostic[] {
  if (observer === "condition_report") return assessment.condition_report ?? [];
  if (observer === "causal_link") {
    return assessment.timeline.flatMap((row) =>
      (row.signals.causal_link ?? []).map((entry) => entry.diagnostic),
    );
  }
  return assessment.timeline
    .map((row) => row.signals[observer as Exclude<ObserverKey, "condition_report" | "causal_link">])
    .filter(Boolean);
}

function currentSignals(assessment: Assessment, observer: ObserverKey): Diagnostic[] {
  if (observer === "condition_report") return assessment.condition_report.slice(-1);
  const row = assessment.timeline[assessment.timeline.length - 1];
  if (!row) return [];
  if (observer === "causal_link") return (row.signals.causal_link ?? []).map((item) => item.diagnostic);
  const signal = row.signals[observer as Exclude<ObserverKey, "condition_report" | "causal_link">];
  return signal ? [signal] : [];
}

function compactHash(value?: string) {
  return value ? `${value.slice(0, 9)}…${value.slice(-7)}` : "—";
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(5);
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function severityLabel(severity: Severity, locale: Locale) {
  const labels: Record<Severity, Record<Locale, string>> = {
    favorable: { es: "Favorable", en: "Favorable" },
    informational: { es: "Informativo", en: "Informational" },
    attention: { es: "Atención", en: "Attention" },
    critical: { es: "Crítico", en: "Critical" },
    indeterminate: { es: "Indeterminado", en: "Indeterminate" },
  };
  return labels[severity][locale];
}

export default function Home() {
  const locale = useSyncExternalStore(
    subscribeLocale,
    localeSnapshot,
    localeServerSnapshot,
  );
  const [assessment, setAssessment] = useState<Assessment>(demoAssessment);
  const [selectedObserver, setSelectedObserver] = useState<ObserverKey>("stability_status");
  const [severityFilter, setSeverityFilter] = useState<Severity | "all">("all");
  const [sourceName, setSourceName] = useState<string>("demo-assessment.json");
  const [isDemo, setIsDemo] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const t = copy[locale];

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  const trajectory = useMemo(() => assessment.timeline.slice(-72), [assessment]);
  const marginRange = useMemo(() => {
    const values = trajectory.map((row) => row.state.M);
    const minimum = Math.min(...values, 0);
    const maximum = Math.max(...values, 0.1);
    return { minimum, maximum, span: Math.max(maximum - minimum, 0.0001) };
  }, [trajectory]);
  const gradientMax = useMemo(
    () => Math.max(...trajectory.map((row) => Math.abs(row.state.G)), 0.0001),
    [trajectory],
  );

  const selectedCurrent = currentSignals(assessment, selectedObserver);
  const selectedHistory = observerSignals(assessment, selectedObserver)
    .filter((signal) => severityFilter === "all" || signal.severity === severityFilter)
    .slice(-8)
    .reverse();
  const primary = selectedCurrent[0] ?? observerSignals(assessment, selectedObserver).slice(-1)[0];
  const selectedPresentation = primary?.presentations?.[locale];

  function changeLocale(next: Locale) {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, next);
    window.dispatchEvent(new Event(LOCALE_CHANGE_EVENT));
  }

  async function openArtifact(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const payload = JSON.parse(await file.text()) as Assessment;
      if (
        payload.schema_version !== "ergonektim.assessment.v1.3" ||
        !Array.isArray(payload.timeline) ||
        !payload.input_binding ||
        !payload.kernel_binding ||
        payload.summary?.observer_count !== 6
      ) {
        throw new Error("invalid assessment");
      }
      setAssessment(payload);
      setSourceName(file.name);
      setIsDemo(false);
      setError(null);
      setSeverityFilter("all");
    } catch {
      setError(t.invalid);
    } finally {
      event.target.value = "";
    }
  }

  async function copyHash(value: string | undefined, key: string) {
    if (!value) return;
    await navigator.clipboard.writeText(value);
    setCopied(key);
    window.setTimeout(() => setCopied(null), 1600);
  }

  return (
    <main className="app-shell">
      <input
        ref={fileInput}
        className="visually-hidden"
        type="file"
        accept="application/json,.json"
        onChange={openArtifact}
        aria-label={t.load}
      />

      <header className="topbar">
        <div className="brand-block">
          <div className="brand-mark" aria-hidden="true">E</div>
          <div>
            <p className="eyebrow">ERGONEKTIM</p>
            <h1>{t.controlRoom}</h1>
            <p className="subtitle">{t.subtitle}</p>
          </div>
        </div>
        <div className="topbar-actions">
          <div className="language-switch" aria-label="Language / Idioma">
            <button className={locale === "es" ? "active" : ""} onClick={() => changeLocale("es")} aria-pressed={locale === "es"}>ES</button>
            <button className={locale === "en" ? "active" : ""} onClick={() => changeLocale("en")} aria-pressed={locale === "en"}>EN</button>
          </div>
          <button className="load-button" onClick={() => fileInput.current?.click()}>
            <span aria-hidden="true">↥</span>
            {isDemo ? t.load : t.replace}
          </button>
        </div>
      </header>

      <section className="artifact-strip" aria-label={t.access}>
        <div className="artifact-identity">
          <span className={`mode-dot ${isDemo ? "demo" : "live"}`} aria-hidden="true" />
          <div>
            <span className="strip-label">{isDemo ? t.demo : t.loaded}</span>
            <strong>{sourceName}</strong>
          </div>
        </div>
        <div className="artifact-tags">
          <span>{t.independent}</span>
          <span>{t.noScalar}</span>
          <span>{t.outcomeFree}</span>
        </div>
        <p className="privacy-note">{t.localOnly}</p>
      </section>

      {isDemo && <div className="notice" role="status">{t.demoNotice}</div>}
      {error && <div className="error-notice" role="alert">{error}</div>}

      <section className="section custody-section">
        <div className="section-heading">
          <div>
            <p className="section-kicker">01 · CUSTODY</p>
            <h2>{t.custody}</h2>
          </div>
          <span className="assessment-id">{assessment.input_binding.assessment_id ?? "assessment.v1"}</span>
        </div>
        <div className="custody-grid">
          <article className="custody-card">
            <div className="custody-title"><span>{t.input}</span><strong className={assessment.input_binding.verified ? "verified" : "unverified"}>{assessment.input_binding.verified ? t.verified : t.unverified}</strong></div>
            <button className="hash-button" onClick={() => copyHash(assessment.input_binding.bundle_sha256, "bundle")} title={t.copyHash}>
              <code>{compactHash(assessment.input_binding.bundle_sha256)}</code>
              <span>{copied === "bundle" ? t.copied : "SHA-256"}</span>
            </button>
            <p>{assessment.summary.rows} {t.rows}</p>
          </article>
          <article className="custody-card">
            <div className="custody-title"><span>{t.kernel}</span><strong className={assessment.kernel_binding.verified ? "verified" : "unverified"}>{assessment.kernel_binding.verified ? t.verified : t.unverified}</strong></div>
            <button className="hash-button" onClick={() => copyHash(assessment.kernel_binding.python_kernel_sha256, "kernel")} title={t.copyHash}>
              <code>{compactHash(assessment.kernel_binding.python_kernel_sha256)}</code>
              <span>PRAMA {assessment.kernel_binding.prama_version}</span>
            </button>
            <p>{t.kernel} · Python</p>
          </article>
          <article className="custody-card">
            <div className="custody-title"><span>{t.recert}</span><strong className={assessment.kernel_binding.recertification?.verified ? "verified" : "unverified"}>{assessment.kernel_binding.recertification?.verified ? t.verified : t.unverified}</strong></div>
            <button className="hash-button" onClick={() => copyHash(assessment.kernel_binding.recertification?.sha256, "recert")} title={t.copyHash}>
              <code>{compactHash(assessment.kernel_binding.recertification?.sha256)}</code>
              <span>{copied === "recert" ? t.copied : "SHA-256"}</span>
            </button>
            <p>{assessment.access.outcomes_accessed ? "Outcome access" : t.outcomeFree}</p>
          </article>
        </div>
      </section>

      <section className="section observer-section">
        <div className="section-heading">
          <div>
            <p className="section-kicker">02 · OBSERVERS</p>
            <h2>{t.observerPanel}</h2>
            <p>{t.panelNote}</p>
          </div>
          <span className="observer-count">06</span>
        </div>
        <div className="observer-grid" role="tablist" aria-label={t.select}>
          {observers.map((observer, index) => {
            const current = currentSignals(assessment, observer);
            const history = observerSignals(assessment, observer);
            const status = current[0];
            const name = status?.presentations?.[locale]?.observer_name ?? observerFallback[observer][locale];
            const codes = Array.from(new Set(current.map((signal) => signal.code)));
            return (
              <button
                key={observer}
                className={`observer-card ${selectedObserver === observer ? "selected" : ""}`}
                onClick={() => setSelectedObserver(observer)}
                role="tab"
                aria-selected={selectedObserver === observer}
              >
                <div className="observer-card-head">
                  <span className="observer-index">{String(index + 1).padStart(2, "0")}</span>
                  <span className="history-count">{history.length}</span>
                </div>
                <h3>{name}</h3>
                <div className="status-list">
                  {codes.length ? codes.slice(0, 2).map((code) => {
                    const signal = current.find((item) => item.code === code)!;
                    return <span key={code} className={`status-pill severity-${signal.severity}`}><i aria-hidden="true" />{signal.presentations?.[locale]?.label ?? code}</span>;
                  }) : <span className="status-pill severity-indeterminate"><i aria-hidden="true" />—</span>}
                </div>
                <p>{observerBoundaries[observer][locale]}</p>
                <span className="card-action">{t.select} <b aria-hidden="true">→</b></span>
              </button>
            );
          })}
        </div>
      </section>

      <section className="analysis-grid">
        <article className="trajectory-card">
          <div className="panel-heading">
            <div><p className="section-kicker">03 · TRAJECTORY</p><h2>{t.trajectory}</h2><p>{t.trajectoryNote}</p></div>
            <div className="legend"><span className="legend-margin"><i />{t.margin}</span><span className="legend-gradient"><i />{t.gradient}</span></div>
          </div>
          <div className="trajectory-chart" role="img" aria-label={t.trajectoryNote}>
            <div className="zero-line" />
            {trajectory.map((row, index) => {
              const marginBottom = ((row.state.M - marginRange.minimum) / marginRange.span) * 78 + 11;
              const gradientHeight = Math.min(Math.abs(row.state.G) / gradientMax, 1) * 34;
              return (
                <div className="trace-column" key={row.timestamp_utc} title={`${row.timestamp_utc}\nM ${row.state.M.toFixed(4)} · G ${row.state.G.toFixed(4)}`}>
                  <span className="margin-dot" style={{ bottom: `${marginBottom}%` }} />
                  <span className={`gradient-stick ${row.state.G < 0 ? "negative" : "positive"}`} style={{ height: `${gradientHeight}%` }} />
                  {index % 12 === 0 && <span className="time-tick">{new Date(row.timestamp_utc).getUTCHours().toString().padStart(2, "0")}</span>}
                </div>
              );
            })}
          </div>
          <div className="trajectory-footer"><span>{trajectory[0]?.timestamp_utc.slice(0, 16).replace("T", " ")} UTC</span><span>{trajectory.at(-1)?.timestamp_utc.slice(0, 16).replace("T", " ")} UTC</span></div>
        </article>

        <aside className="detail-card">
          <div className="panel-heading compact">
            <div><p className="section-kicker">04 · DETAIL</p><h2>{t.detail}</h2></div>
            <span className="detail-number">{String(observers.indexOf(selectedObserver) + 1).padStart(2, "0")}</span>
          </div>
          <h3>{selectedPresentation?.observer_name ?? observerFallback[selectedObserver][locale]}</h3>
          <div className="current-signals">
            {selectedCurrent.map((signal, index) => (
              <div className="current-signal" key={`${signal.code}-${index}`}>
                <span className={`severity-beacon severity-${signal.severity}`} aria-hidden="true" />
                <div><small>{t.current} · {severityLabel(signal.severity, locale)}</small><strong>{signal.presentations?.[locale]?.label ?? signal.code}</strong><p>{signal.presentations?.[locale]?.explanation}</p></div>
              </div>
            ))}
          </div>
          {primary && (
            <>
              <div className="detail-section"><h4>{t.evidence}</h4><dl className="evidence-grid">{Object.entries(primary.evidence ?? {}).slice(0, 6).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{formatValue(value)}</dd></div>)}</dl></div>
              <div className="detail-section review"><h4>{t.review}</h4><p>{selectedPresentation?.review_action}</p></div>
              <div className="detail-section boundary"><h4>{t.boundary}</h4><p>{selectedPresentation?.claim_boundary ?? observerBoundaries[selectedObserver][locale]}</p></div>
            </>
          )}
        </aside>
      </section>

      <section className="section history-section">
        <div className="section-heading history-heading">
          <div><p className="section-kicker">05 · REGISTER</p><h2>{t.history}</h2></div>
          <div className="filter-row" aria-label="Severity filter">
            {(["all", "favorable", "attention", "critical", "indeterminate"] as const).map((filter) => (
              <button key={filter} className={severityFilter === filter ? "active" : ""} onClick={() => setSeverityFilter(filter)}>{filter === "all" ? t.all : t[filter]}</button>
            ))}
          </div>
        </div>
        <div className="history-table" role="table">
          <div className="history-row history-header" role="row"><span>{t.time}</span><span>{t.state}</span><span>{t.evidence}</span></div>
          {selectedHistory.length ? selectedHistory.map((signal, index) => (
            <div className="history-row" role="row" key={`${signal.timestamp_utc}-${signal.code}-${index}`}>
              <time>{signal.timestamp_utc.slice(0, 16).replace("T", " ")}</time>
              <span className={`status-pill severity-${signal.severity}`}><i aria-hidden="true" />{signal.presentations?.[locale]?.label ?? signal.code}</span>
              <code>{Object.entries(signal.evidence ?? {}).slice(0, 2).map(([key, value]) => `${key}=${formatValue(value)}`).join(" · ") || "—"}</code>
            </div>
          )) : <div className="empty-row">—</div>}
        </div>
      </section>

      <footer>
        <div><strong>ERGONEKTIM</strong><span>Aptadynamic Viability Assessment for Electric Power Systems</span></div>
        <div><span>assessment.v1</span><span>PRAMA {assessment.kernel_binding.prama_version}</span><span>UTC</span></div>
      </footer>
    </main>
  );
}

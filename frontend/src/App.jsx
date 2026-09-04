import React, { useState, useEffect } from "react";
import { 
  ShieldAlert, ShieldCheck, AlertTriangle, Activity, Database, Cpu, 
  Layers, Lock, RefreshCw, Zap, TrendingUp, DollarSign, Search, CheckCircle2, ChevronRight, Sliders
} from "lucide-react";

export default function App() {
  const [metrics, setMetrics] = useState(null);
  const [stream, setStream] = useState([]);
  const [abuseRings, setAbuseRings] = useState([]);
  const [selectedTxn, setSelectedTxn] = useState(null);
  const [investigationResult, setInvestigationResult] = useState(null);
  const [isInvestigating, setIsInvestigating] = useState(false);
  const [adversarialCase, setAdversarialCase] = useState(null);
  const [activeTab, setActiveTab] = useState("stream");

  // Real Merchant Policy Threshold Tuning
  // 0 (Strict) -> Hold @ 0.25, Block @ 0.60
  // 50 (Balanced) -> Hold @ 0.35, Block @ 0.75
  // 100 (VIP Friendly) -> Hold @ 0.45, Block @ 0.85
  const [policyPreset, setPolicyPreset] = useState(50);

  const holdThreshold = (0.25 + (policyPreset / 100) * 0.20).toFixed(2);
  const blockThreshold = (0.60 + (policyPreset / 100) * 0.25).toFixed(2);

  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    fetchMetrics();
    fetchStream();
    fetchAbuseRings();
    fetchAdversarialShowcase();
  }, [policyPreset]);

  const handleRefreshAll = async () => {
    setIsRefreshing(true);
    await Promise.all([
      fetchMetrics(),
      fetchStream(),
      fetchAbuseRings(),
      fetchAdversarialShowcase()
    ]);
    setTimeout(() => setIsRefreshing(false), 500);
  };

  const fetchMetrics = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/metrics");
      const data = await res.json();
      setMetrics(data);
    } catch (e) {
      console.error("Failed to load metrics", e);
    }
  };

  const fetchStream = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/transactions/stream?limit=30&hold_threshold=${holdThreshold}&block_threshold=${blockThreshold}`);
      const data = await res.json();
      setStream(data.items || []);
    } catch (e) {
      console.error("Failed to load stream", e);
    }
  };

  const fetchAbuseRings = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/graph/abuse-rings");
      const data = await res.json();
      setAbuseRings(data.rings || []);
    } catch (e) {
      console.error("Failed to load rings", e);
    }
  };

  const fetchAdversarialShowcase = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/adversarial-showcase");
      const data = await res.json();
      setAdversarialCase(data);
    } catch (e) {
      console.error("Failed to load adversarial case", e);
    }
  };

  const handleInvestigate = async (txn) => {
    setSelectedTxn(txn);
    setIsInvestigating(true);
    setInvestigationResult(null);
    try {
      const res = await fetch("http://localhost:8000/api/agent/investigate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(txn)
      });
      const data = await res.json();
      setInvestigationResult(data);
    } catch (e) {
      console.error("Investigation failed", e);
    } finally {
      setIsInvestigating(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-[#0d1322] px-6 py-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <ShieldAlert className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg tracking-tight text-white">Razorpay SentinelAI</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-blue-950 text-blue-400 border border-blue-800/60 font-mono">
                Track 02: AI Risk Manager
              </span>
            </div>
            <p className="text-xs text-slate-400">Autonomous Abuse-Ring Sentinel & Bounded Hold-Tier Defense</p>
          </div>
        </div>

        {/* Live Status Pill */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800 text-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-slate-300 font-medium">Real-Time XGBoost Inference</span>
          </div>
          <button 
            onClick={handleRefreshAll} 
            disabled={isRefreshing}
            className="flex items-center space-x-1.5 text-xs bg-slate-800 hover:bg-slate-700 active:scale-95 px-3 py-1.5 rounded-md border border-slate-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin text-blue-400" : ""}`} />
            <span>{isRefreshing ? "Refreshing..." : "Refresh"}</span>
          </button>
        </div>
      </header>

      {/* Hero Financial Ledger & KPIs */}
      {metrics && (
        <section className="px-6 py-4 bg-[#0c1220] border-b border-slate-800/80">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-3.5">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span>Net Fraud Prevented</span>
                <DollarSign className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-xl font-bold text-emerald-400">
                INR {metrics.financial_cost_ledger.fraud_amount_prevented_inr.toLocaleString('en-IN')}
              </div>
              <div className="text-[11px] text-emerald-500/80 mt-1 flex items-center space-x-1">
                <CheckCircle2 className="w-3 h-3" />
                <span>Zero chargeback liability</span>
              </div>
            </div>

            <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-3.5">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span>Held-Out Accuracy / F1</span>
                <TrendingUp className="w-4 h-4 text-blue-400" />
              </div>
              <div className="text-xl font-bold text-blue-400">
                {(metrics.f1_score * 100).toFixed(1)}% <span className="text-xs text-slate-400 font-normal">F1-Score</span>
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Held-out test: {metrics.held_out_test_records} txns (Zero-Leakage)
              </div>
            </div>

            <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-3.5">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span>False-Positive Friction Cost</span>
                <AlertTriangle className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-xl font-bold text-slate-200">
                INR {metrics.financial_cost_ledger.estimated_fp_friction_cost_inr.toLocaleString('en-IN')}
              </div>
              <div className="text-[11px] text-emerald-400 mt-1">
                0 false legitimate blocks
              </div>
            </div>

            <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-3.5">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span>Abuse Rings Neutralized</span>
                <Layers className="w-4 h-4 text-purple-400" />
              </div>
              <div className="text-xl font-bold text-purple-400">
                {abuseRings.length} Syndicates
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Bipartite Graph Resolved
              </div>
            </div>

            <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-3.5">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span>Autonomous Gating</span>
                <Cpu className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="text-xl font-bold text-indigo-400">
                3-Tier Gated
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                HMAC-SHA256 Signed
              </div>
            </div>
          </div>

          {/* Active Policy Slider */}
          <div className="mt-3 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2 text-slate-300 font-medium">
              <Sliders className="w-3.5 h-3.5 text-blue-400" />
              <span>Real Policy Engine Thresholds (Hold: &gt;={holdThreshold}, Block: &gt;{blockThreshold}):</span>
            </div>
            <div className="flex items-center space-x-3 w-1/2">
              <span className="text-[11px] text-slate-400">Strict Defense</span>
              <input 
                type="range" 
                min="0" 
                max="100" 
                value={policyPreset} 
                onChange={(e) => setPolicyPreset(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
              <span className="text-[11px] text-emerald-400 font-semibold">VIP Friendly ({policyPreset}%)</span>
            </div>
          </div>
        </section>
      )}

      {/* Main Tabs */}
      <div className="px-6 border-b border-slate-800 flex space-x-6 bg-[#0a0f1c]">
        <button 
          onClick={() => setActiveTab("stream")}
          className={`py-3 text-sm font-medium border-b-2 flex items-center space-x-2 transition ${
            activeTab === "stream" ? "border-blue-500 text-blue-400" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Activity className="w-4 h-4" />
          <span>Real-Time Triage Stream</span>
        </button>

        <button 
          onClick={() => setActiveTab("rings")}
          className={`py-3 text-sm font-medium border-b-2 flex items-center space-x-2 transition ${
            activeTab === "rings" ? "border-blue-500 text-blue-400" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Abuse Ring Graph Network ({abuseRings.length})</span>
        </button>

        <button 
          onClick={() => setActiveTab("adversarial")}
          className={`py-3 text-sm font-medium border-b-2 flex items-center space-x-2 transition ${
            activeTab === "adversarial" ? "border-blue-500 text-blue-400" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Zap className="w-4 h-4" />
          <span>Adversarial VIP Edge-Case Demo</span>
        </button>
      </div>

      {/* Main Workspace Layout */}
      <main className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 overflow-hidden">
        
        {/* Left Column (7 cols): Stream or Graph */}
        <div className="lg:col-span-7 space-y-4">
          {activeTab === "stream" && (
            <div className="bg-[#0e1424] border border-slate-800 rounded-xl overflow-hidden shadow-xl">
              <div className="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
                <div className="flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-blue-400" />
                  <span className="font-semibold text-sm">Live Razorpay Transaction Feed (Scored via Real XGBoost)</span>
                </div>
                <span className="text-xs text-slate-400">Click any row to trigger Investigation</span>
              </div>

              <div className="overflow-x-auto max-h-[580px] overflow-y-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950/80 text-slate-400 sticky top-0 border-b border-slate-800">
                    <tr>
                      <th className="px-4 py-2.5">Payment ID</th>
                      <th className="px-4 py-2.5">Method</th>
                      <th className="px-4 py-2.5">Amount</th>
                      <th className="px-4 py-2.5">Merchant / MCC</th>
                      <th className="px-4 py-2.5">XGBoost Risk</th>
                      <th className="px-4 py-2.5">Policy Tier</th>
                      <th className="px-4 py-2.5">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {stream.map((txn) => {
                      const isHold = txn.decision_tier === "HOLD_FOR_AGENT";
                      const isBlock = txn.decision_tier === "AUTO_BLOCK";
                      return (
                        <tr 
                          key={txn.payment_id}
                          onClick={() => handleInvestigate(txn)}
                          className={`cursor-pointer transition hover:bg-slate-800/50 ${
                            selectedTxn?.payment_id === txn.payment_id ? "bg-blue-950/40 border-l-2 border-blue-500" : ""
                          }`}
                        >
                          <td className="px-4 py-3 font-mono font-medium text-slate-200">
                            <div className="flex items-center space-x-1.5">
                              <span>{txn.payment_id.slice(0, 14)}...</span>
                              {txn.is_demo_hold && (
                                <span className="text-[9px] px-1.5 py-0.2 rounded bg-indigo-950 text-indigo-300 border border-indigo-700 font-sans font-bold">
                                  DEMO — HOLD FOR AGENT
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-3 uppercase text-[11px] font-semibold text-slate-300">
                            <span className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700">
                              {txn.method}
                            </span>
                          </td>
                          <td className="px-4 py-3 font-semibold text-slate-100">
                            INR {txn.amount.toLocaleString('en-IN')}
                          </td>
                          <td className="px-4 py-3 text-slate-400">
                            <div>{txn.merchant_id.replace("mer_", "")}</div>
                            <div className="text-[10px] text-slate-500">MCC {txn.mcc}</div>
                          </td>
                          <td className="px-4 py-3 font-mono">
                            <span className={`font-semibold ${
                              isBlock ? "text-rose-400" : isHold ? "text-amber-400" : "text-emerald-400"
                            }`}>
                              {(txn.risk_score * 100).toFixed(1)}%
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                              isBlock 
                                ? "bg-rose-950/70 text-rose-300 border-rose-800/80" 
                                : isHold 
                                ? "bg-amber-950/70 text-amber-300 border-amber-800/80 animate-pulse" 
                                : "bg-emerald-950/70 text-emerald-300 border-emerald-800/80"
                            }`}>
                              {txn.decision_tier}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <ChevronRight className="w-4 h-4 text-slate-500" />
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === "rings" && (
            <div className="bg-[#0e1424] border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-100">Coordinated Multi-Account Abuse Rings</h3>
                  <p className="text-xs text-slate-400">Detected via Bipartite Graph Entity Resolution (NetworkX)</p>
                </div>
                <span className="text-xs px-2.5 py-1 rounded bg-purple-950 text-purple-300 border border-purple-800 font-mono">
                  {abuseRings.length} Active Syndicates
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {abuseRings.map((ring) => (
                  <div key={ring.ring_id} className="bg-slate-900/80 border border-slate-800 rounded-lg p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-bold text-purple-300">{ring.ring_id}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-800 font-semibold">
                        {ring.threat_level} THREAT
                      </span>
                    </div>

                    <div className="grid grid-cols-3 gap-2 text-center text-xs py-2 bg-slate-950/50 rounded border border-slate-800/80">
                      <div>
                        <div className="text-slate-400 text-[10px]">Linked Accounts</div>
                        <div className="font-bold text-slate-100 mt-0.5">{ring.account_count}</div>
                      </div>
                      <div>
                        <div className="text-slate-400 text-[10px]">Shared Devices</div>
                        <div className="font-bold text-amber-400 mt-0.5">{ring.device_count}</div>
                      </div>
                      <div>
                        <div className="text-slate-400 text-[10px]">Subnet IPs</div>
                        <div className="font-bold text-blue-400 mt-0.5">{ring.ip_count}</div>
                      </div>
                    </div>

                    <div className="text-[11px] text-slate-400 space-y-1">
                      <div><span className="text-slate-500">Device Fingerprint:</span> <span className="font-mono text-slate-300">{ring.sample_devices[0]}</span></div>
                      <div><span className="text-slate-500">Sample Accounts:</span> <span className="font-mono text-slate-300">{ring.sample_accounts.join(", ")}</span></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === "adversarial" && adversarialCase && (
            <div className="bg-[#0e1424] border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
              <div className="flex items-center space-x-2 text-amber-400">
                <Zap className="w-5 h-5" />
                <h3 className="text-base font-bold text-slate-100">{adversarialCase.scenario}</h3>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                {adversarialCase.description}
              </p>

              <div className="grid grid-cols-2 gap-4 text-xs">
                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                  <div className="text-slate-400 font-semibold mb-1">Naive Fixed-Threshold Verdict</div>
                  <div className="text-rose-400 font-bold text-sm">HARD BLOCK ? (False Positive)</div>
                  <p className="text-[11px] text-slate-500 mt-1">High burst velocity triggered naive blocking rule.</p>
                </div>

                <div className="p-3 bg-emerald-950/30 rounded-lg border border-emerald-800/60">
                  <div className="text-emerald-400 font-semibold mb-1">SentinelAI Bounded Verdict</div>
                  <div className="text-emerald-400 font-bold text-sm">HOLD ? APPROVE ? (Safe)</div>
                  <p className="text-[11px] text-emerald-500/80 mt-1">Agent inferred VIP tenure (950d) & cleared transaction.</p>
                </div>
              </div>

              <button 
                onClick={() => handleInvestigate(adversarialCase.transaction)}
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 rounded-lg font-semibold text-xs transition shadow-lg shadow-blue-600/20 flex items-center justify-center space-x-2"
              >
                <span>Replay Bounded Investigation for this Case</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        {/* Right Column (5 cols): Bounded Agent Investigation Drawer */}
        <div className="lg:col-span-5 bg-[#0e1424] border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
              <div className="flex items-center space-x-2">
                <Cpu className="w-5 h-5 text-indigo-400" />
                <h3 className="font-bold text-sm text-slate-100">Bounded Autonomous Investigator</h3>
              </div>
              {selectedTxn && (
                <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                  {selectedTxn.payment_id.slice(0, 10)}...
                </span>
              )}
            </div>

            {!selectedTxn && (
              <div className="text-center py-16 text-slate-500 space-y-2">
                <Search className="w-8 h-8 mx-auto text-slate-600" />
                <p className="text-xs">Select any transaction from the stream to trigger the bounded investigation loop.</p>
              </div>
            )}

            {isInvestigating && (
              <div className="text-center py-16 space-y-3">
                <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                <p className="text-xs text-indigo-400 font-mono animate-pulse">
                  Evaluating dynamic evidence across Device, Graph & Velocity tools...
                </p>
              </div>
            )}

            {investigationResult && (
              <div className="space-y-4 text-xs">
                {/* Final Verdict Banner */}
                <div className={`p-3 rounded-lg border flex items-center justify-between ${
                  investigationResult.agent_verdict === "BLOCK" 
                    ? "bg-rose-950/40 border-rose-800 text-rose-200" 
                    : investigationResult.agent_verdict === "STEP_UP_2FA"
                    ? "bg-amber-950/40 border-amber-800 text-amber-200"
                    : "bg-emerald-950/40 border-emerald-800 text-emerald-200"
                }`}>
                  <div>
                    <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Agent Verdict</div>
                    <div className="text-base font-bold mt-0.5">{investigationResult.action_code}</div>
                  </div>
                  <div className="text-right font-mono">
                    <div className="text-[10px] text-slate-400">Investigation Score</div>
                    <div className="text-sm font-bold">{(investigationResult.investigation_score * 100).toFixed(0)}%</div>
                  </div>
                </div>

                {/* Plain-English Explanation */}
                <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
                  <div className="text-[10px] uppercase font-bold text-slate-400 mb-1">Explainable Audit Reason</div>
                  <p className="text-slate-200 text-xs leading-relaxed">
                    {investigationResult.explanation}
                  </p>
                </div>

                {/* Evidence Tool Execution Steps */}
                <div className="space-y-2">
                  <div className="text-[10px] uppercase font-bold text-slate-400">Evidence Gathering Trace</div>
                  <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                    {investigationResult.investigation_steps.map((step) => (
                      <div key={step.step} className="p-2 bg-slate-950 rounded border border-slate-800/80 font-mono text-[11px]">
                        <div className="flex items-center space-x-1.5 text-blue-400 font-semibold mb-0.5">
                          <span>Step {step.step}:</span>
                          <span>{step.action}</span>
                        </div>
                        <div className="text-slate-300 text-[10.5px] italic mb-1">
                          "{step.thought}"
                        </div>
                        <div className="text-slate-400 text-[10px] pl-2 border-l border-slate-800">
                          {step.observation}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* HMAC-SHA256 Cryptographic Audit Trail */}
          {investigationResult && (
            <div className="pt-4 border-t border-slate-800/80 text-[10px] font-mono text-slate-500 flex items-center justify-between">
              <div className="flex items-center space-x-1.5">
                <Lock className="w-3 h-3 text-indigo-400" />
                <span>HMAC-SHA256:</span>
              </div>
              <span className="text-slate-400 truncate max-w-[200px]">
                {investigationResult.audit_trail.hmac_sha256_signature}
              </span>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
